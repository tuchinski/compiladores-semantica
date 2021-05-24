from anytree import node
from anytree.node import nodemixin
from mytree import MyNode
import sintatica as sin
from sys import argv
from anytree.exporter import DotExporter, UniqueDotExporter

# !!!!!!!!!!!
# ATENCAO: TEM QUE INSTALAR O GRAPHVIZ!!!!!!!!
# !!!!!!!!!!!

tipos_numeros = {
    "NUM_INTEIRO": "INTEIRO",
    "NUM_PONTO_FLUTUANTE": "FLUTUANTE",
    "NUM_NOTACAO_CIENTIFICA": "notacao_cientifica"
}

erro = False
mensagens_warning = []
mensagens_erro = []
funcoes = {}
variaveis_declaradas = []
variaveis_utilzadas = []
escopo_atual = "global"
escopo_antigo = ""
verifica_se = False


# Funcao que analisa a arvore toda
def analisa_arvore(raiz):
    if raiz:
        filhos = raiz.children
        global verifica_se
        if raiz.name == "declaracao_variaveis":
            print("declaração variável")
            declaracao_variavel(raiz)
        elif raiz.name == 'declaracao_funcao':
            print("declaração funcao")
            declaracao_funcao(raiz)
            print(funcoes)
        elif raiz.name == 'fim':
            if verifica_se:
                print("fim se")
                verifica_se = False
            else:
                print("fim função")
                verifica_retorno_funcao_atual()
                sai_escopo()
        elif raiz.name == 'atribuicao':
            print("atribuição")
            atrib_node = atribuicao(raiz)
            atrib_node.parent = raiz.parent
            raiz.parent.children = [atrib_node]
            # raiz = atrib_node
            return
        elif raiz.name == 'retorna':
            print('retorna')
            nodes_novo = retorna(raiz)
            nodes_novo.parent = raiz.parent
            raiz.children = [nodes_novo]
            return
        elif raiz.name == 'chamada_funcao':
            node_novo = verifica_chamada_funcao(raiz, True)
            pai = raiz.anchestors[-7]
            pai.name = "chamada_funcao"
            pai.children = [node_novo]
            print("chamada funcao")
            return

        elif raiz.name == "escreva":
            print("escreva")
            node_novo = verifica_escreva(raiz)
            node_novo.parent = raiz.parent
            raiz.children = [node_novo]
            return
        elif raiz.name == "leia":
            print("leia")
            node_novo = verifica_leia(raiz)
            node_novo.parent = raiz.parent
            raiz.children = [node_novo]
            return
        elif raiz.name == "se":
            print("se")
            verifica_se = True
            analisa_se(raiz)
            return
        elif raiz.name == "repita":
            verifica_repita(raiz)
            return

        for filho in filhos:
            analisa_arvore(filho)

def verifica_repita(node):
    corpo = node.children[1]
    expressao = node.children[3]

    expressao_resolvida = resolve_expressao(expressao, None, None)
    expressao.children = [expressao_resolvida]

    analisa_arvore(corpo)


def verifica_leia(node):
    expressao_leia = node.children[2]
    nome_var = expressao_leia.children[0].children[0].label
    for var in variaveis_declaradas:
        if var["lexema"] == nome_var and escopo_atual == var["escopo"]:
            var["inicializado"] = True

    for var in variaveis_declaradas:
        if var["lexema"] == nome_var and "global" == var["escopo"]:
            var["inicializado"] = True

    return expressao_leia

def analisa_se(node):
    expressao_se = node.children[1]
    retorno_expressao_se = resolve_expressao(expressao_se, None, None)

    retorno_expressao_se.parent = expressao_se

    expressao_se.children = [retorno_expressao_se]

    corpo_se = node.children[3]
    analisa_arvore(corpo_se)

    if len(node.children) == 7:
        # tem senao
        corpo_senao = node.children[5]
        analisa_arvore(corpo_senao)

def verifica_escreva(node):
    expressao_escreva = node.children[2]
    expressao_resolvida = resolve_expressao(expressao_escreva, None, None)
    return expressao_resolvida


def verifica_chamada_funcao(raiz, retorna_arvore):
    id_funcao = raiz.children[0].children[0].label

    global funcoes
    global erro

    if id_funcao == "principal":
        if escopo_atual != "principal":
            mensagens_erro.append("Erro: Chamada para a função principal não permitida")
            return
        else:
            mensagens_warning.append("Aviso: Chamada recursiva para principal")

    # # aqui a gente ta otimizando a arvore
    # expressao_node = raiz.anchestors[-7]
    # raiz.parent = expressao_node.parent
    # expressao_node.parent = None

    if id_funcao not in funcoes.keys():
        mensagens_erro.append('Erro: Chamada a função \'{}\' que não foi declarada.'.format(id_funcao))
        erro = True
        return raiz

    lista_args = raiz.children[2]
    args_esperados = funcoes[id_funcao]['parametros']
    args_passados = verifica_lista_argumentos(lista_args)

    if len(args_esperados) != len(args_passados):
        mensagens_erro.append('Erro: Chamada da função \'{}\' passando {} parametro(s). Esperado {} parametro(s)'.format(
            id_funcao, str(len(args_passados)), str(len(args_esperados))
        ))
        erro = True
        return False

    returnErro = False
    for i in range(0, len(args_esperados)):
        tipo_esperado = args_esperados[i]['tipo']
        tipo_passado = args_passados[i].type
        if tipo_passado != tipo_esperado:
            mensagem_erro = "Erro: Parametro {} da função {} espera tipo {}, variável do tipo {} passada!".format(
                args_esperados[i]['id'], id_funcao, tipo_esperado, tipo_passado
            )
            erro = True
            returnErro = True
    if returnErro:
        return False
    else:
        funcoes[id_funcao]["utilizada"] = True
        if not retorna_arvore:
            return True
        else:
            tipo_fun = funcoes[id_funcao]['tipo']
            node = MyNode(name=id_funcao+"()",type=tipo_fun, id="chamada_funcao-" + tipo_fun)
            return node

    print(args_passados)


def verifica_lista_argumentos(node):
    args_passados = []
    for filho in node.children:
        if filho.label == 'lista_argumentos':
            lista = verifica_lista_argumentos(filho)
            args_passados += lista
        elif filho.label == 'expressao':
            args_passados.append(resolve_expressao(filho, None, None))
            print(args_passados)
    return args_passados


def verifica_retorno_funcao_atual():
    funcao_atual = funcoes[escopo_atual]
    if not funcao_atual['retornou'] and funcao_atual['tipo'] != "vazio":
        global mensagens_erro
        mensagens_erro.append(
            "Erro: Função '{}' deveria retornar {}, mas retorna vazio".format(escopo_atual, funcao_atual["tipo"]))
    return


def retorna(raiz):
    expressao_retorna = raiz.children[2]
    retorno_expressao = resolve_expressao(expressao_retorna, None, None)

    global mensagens_erro
    global funcoes
    tipo_var_retorno = retorno_expressao.type
    if tipo_var_retorno == 'error':
        mensagens_erro.append("Erro: Não é possível executar retorno da funcão '{}'.".format(escopo_atual))
        funcoes[escopo_atual]['retornou'] = True
        return
    tipo_retorno_esperado = funcoes[escopo_atual]['tipo']
    if tipo_var_retorno.lower() != tipo_retorno_esperado.lower():
        mensagens_erro.append("Erro: Função '{}' deveria retornar {}, mas retorna {}".format(escopo_atual, tipo_retorno_esperado,
                                                                                             tipo_var_retorno))
    funcoes[escopo_atual]['retornou'] = True
    return retorno_expressao


def atribuicao(node):
    id_atribuicao = node.children[0].children[0].children[0].label
    expressao = node.children[2]
    tipo_var = None

    variavel_atual_declarada = False
    global variaveis_declaradas
    global escopo_atual
    for var in variaveis_declaradas:
        if var['lexema'] == id_atribuicao and var['escopo'] == escopo_atual:
            variavel_atual_declarada = True
            tipo_var = var['tipo']
            var['usada'] = True
    if not variavel_atual_declarada:
        for var in variaveis_declaradas:
            if var['escopo'] == 'global' and var['lexema'] == id_atribuicao:
                variavel_atual_declarada = True
                tipo_var = var['tipo']
                var['usada'] = True

    if not variavel_atual_declarada:
        global mensagens_erro
        mensagens_erro.append('Erro: Variável \'{}\' não declarada1'.format(id_atribuicao))


    node_novo = MyNode(name=':=', type=":=")
    node_var = MyNode(name=id_atribuicao, type=tipo_var)
    node_var.parent = node_novo

    expressao_resolvida = resolve_expressao(expressao, tipo_var, id_atribuicao)

    indice = verifica_variavel_declarada_por_nome(id_atribuicao)

    if indice != -1:
        variaveis_declaradas[indice]['inicializado'] = True


    expressao_resolvida.parent = node_novo

    return node_novo


def resolve_expressao(exp, tipo_var, id_atrib):
    if exp.children[0].label == "expressao_logica":
        a = resolve_expressao_logica(exp.children[0], tipo_var, id_atrib)

        return a

    elif exp.children[0].label == 'atribuicao':
        print('atribuicao - expressao')


def resolve_expressao_logica(exp, tipo_var, id_atrib):
    filho = exp.children[0]
    if filho.label == 'expressao_simples':
        return resolve_expressao_simples(filho, tipo_var, id_atrib)
    else:
        print('tem que ver ainda - expressao logica!!!!!!!!!!!!')


def resolve_expressao_simples(exp, tipo_var, id_atrib):
    filho = exp.children[0]
    if filho.label == 'expressao_aditiva':
        return resolve_expressao_aditiva(filho, tipo_var, id_atrib)
    else:
        filho_esq = exp.children[0]
        filho_dir = exp.children[2]

        a1 = resolve_expressao_simples(filho_esq, tipo_var, id_atrib)
        a3 = resolve_expressao_aditiva(filho_dir, tipo_var, id_atrib)

        tipo_a1 = a1.type
        tipo_a3 = a3.type

        if tipo_a3 == tipo_a1:
            tipo_operacao = tipo_a3
        else:
            tipo_operacao = "FLUTUANTE"

        nome_operador = exp.children[1].children[0].label
        if nome_operador == "MAIOR":
            node_operacao = MyNode(name=">", type=tipo_operacao)
            node_operacao.id = ">-" + tipo_operacao
        elif nome_operador == "MENOR":
            node_operacao = MyNode(name="<", type=tipo_operacao)
            node_operacao.id = "<-" + tipo_operacao
        elif nome_operador == "IGUAL":
            node_operacao = MyNode(name="=", type=tipo_operacao)
            node_operacao.id = "=-" + tipo_operacao
        elif nome_operador == "DIFERENTE":
            node_operacao = MyNode(name="<>", type=tipo_operacao)
            node_operacao.id = "<>-" + tipo_operacao
        elif nome_operador == "MENOR_IGUAL":
            node_operacao = MyNode(name="<=", type=tipo_operacao)
            node_operacao.id = "<=-" + tipo_operacao
        elif nome_operador == "MAIOR_IGUAL":
            node_operacao = MyNode(name=">=", type=tipo_operacao)
            node_operacao.id = ">=-" + tipo_operacao


        a1.parent = node_operacao
        a3.parent = node_operacao

        return node_operacao

        # print("entrou no else de expressao simples, tem que resover aqui!!!!!!!!")


def resolve_expressao_aditiva(exp, tipo_var, id_atrib):
    filho = exp.children[0]
    if filho.label == 'expressao_multiplicativa':
        return resolve_expressao_multiplicativa(filho, tipo_var, id_atrib)
    else:
        filho_esq = exp.children[0]
        filho_dir = exp.children[2]
        a1 = resolve_expressao_aditiva(filho_esq, tipo_var, id_atrib)
        a3 = resolve_expressao_multiplicativa(filho_dir, tipo_var, id_atrib)

        tipo_a1 = a1.type
        tipo_a3 = a3.type

        if tipo_a3 == tipo_a1:
            tipo_operacao = tipo_a3
        else:
            tipo_operacao = "FLUTUANTE"

        nome_operador = exp.children[1].children[0].label
        if nome_operador == "MAIS":
            node_adicao = MyNode(name="+", type=tipo_operacao)
        elif nome_operador == "MENOS":
            node_adicao = MyNode(name="-", type=tipo_operacao)


        a1.parent = node_adicao
        a3.parent = node_adicao
        node_adicao.id = "+-" + tipo_operacao
        return node_adicao


def resolve_expressao_multiplicativa(exp, tipo_var, id_atrib):
    filho = exp.children[0]
    if filho.label == 'expressao_unaria':
        return resolve_expressao_unaria(filho, tipo_var, id_atrib)
    else:
        filho_esq = exp.children[0]
        filho_dir = exp.children[2]
        a1 = resolve_expressao_multiplicativa(filho_esq, tipo_var, id_atrib)
        a3 = resolve_expressao_unaria(filho_dir, tipo_var, id_atrib)

        tipo_a1 = a1.type
        tipo_a3 = a3.type

        if tipo_a3 == tipo_a1:
            tipo_operacao = tipo_a3
        else:
            tipo_operacao = "FLUTUANTE"

        node_multiplicacao = MyNode(name="*", type=tipo_operacao)
        a1.parent = node_multiplicacao
        a3.parent = node_multiplicacao
        node_adicao.id = "+-" + tipo_operacao

        return node_multiplicacao


def resolve_expressao_unaria(exp, tipo_var, id_atrib):
    global mensagens_warning
    global mensagens_erro
    global erro
    if len(exp.children) > 1:
        fator = exp.children[1]
    else:
        fator = exp.children[0]

    if fator.children[0].label == 'var':
        var = fator.children[0]
        index_variavel = verifica_variavel_declarada(var)
        if index_variavel < 0:
            nome_var_erro = fator.children[0].children[0].children[0].label
            num = MyNode(name=nome_var_erro, type='error')

        else:
            nome_var = variaveis_declaradas[index_variavel]["lexema"]
            tipo_var_expressao = variaveis_declaradas[index_variavel]["tipo"]
            if tipo_var is not None and tipo_var_expressao != tipo_var:
                mensagens_warning.append("Aviso: Coerção implícita do valor de '{}'".format(nome_var))
                # mensagens_warning.append(
                #     "Aviso: Atribuição de tipos distintos ‘{}’ {} e ‘expressão’ {}1".format(id_atrib, tipo_var,
                #                                                                            tipo_var_expressao))
            if variaveis_declaradas[index_variavel]['inicializado'] == False:
                mensagens_warning.append("Aviso: Variável ‘{}’ declarada e não inicializada em '{}'.".format(nome_var, escopo_atual))
                variaveis_declaradas[index_variavel]['inicializado'] = True
            variaveis_declaradas[index_variavel]['usada'] = True
            num = MyNode(name=nome_var, type=tipo_var_expressao)
            num.id = "var-"+tipo_var_expressao
        return num

    elif fator.children[0].label == 'chamada_funcao':
        if verifica_chamada_funcao(fator.children[0],False):
            # id_func = fator.children[0]
            id_func = fator.children[0].children[0].children[0].label

            funcao_chamada = funcoes[id_func]
            tipo_funcao = funcao_chamada['tipo']
            no_func = MyNode(name=id_func + '()', type=tipo_funcao)
            no_func.id = "chamada_funcao-" + tipo_funcao

            if tipo_var != None and tipo_funcao.lower() != tipo_var.lower():
                mensagens_warning.append("Aviso: Coerção implícita do valor retornado por '{}'".format(id_func))
                # mensagens_warning.append("Aviso: Atribuição de tipos distintos '{}' flutuante e '{}' retorna inteiro2".format(
                #     id_atrib, id_func
                # ))

            return no_func
        else:
            no_func = MyNode(name="error", type="error")
            return no_func

    elif fator.children[0].label == 'numero':
        tipo_num = fator.children[0].children[0].label
        tipo_num = tipos_numeros[tipo_num]

        if tipo_var is not None and tipo_num != tipo_var:
            mensagens_warning.append("Aviso: Coerção implícita do valor atribuído para '{}'".format(id_atrib))
            # mensagens_warning.append(
            #     "Aviso: Atribuição de tipos distintos ‘{}’ {} e ‘expressão’ {}3".format(id_atrib, tipo_var, tipo_num))

        num = fator.children[0].children[0].children[0].label
        novo_node = MyNode(name=num, type=tipo_num)
        novo_node.id = "numero-"+tipo_num
        return novo_node

    elif fator.children[1].label == "expressao":
        return resolve_expressao(fator.children[1], tipo_var, id_atrib)


def verifica_variavel_declarada(var):
    nome_var = var.children[0].children[0].label
    i = 0
    standby = -1
    for var in variaveis_declaradas:
        if var['lexema'] == nome_var and var['escopo'] == escopo_atual:
            return i
        elif var['lexema'] == nome_var and var['escopo'] == 'global':
            standby = i
            i += 1
        else:
            i += 1
    if standby >= 0:
        return standby
    else:
        global mensagens_erro
        mensagens_erro.append('Erro: Variável \'{}\' não declarada2'.format(nome_var))
        return -1

def verifica_variavel_declarada_por_nome(nome_var):
    i = 0
    standby = -1
    for var in variaveis_declaradas:
        if var['lexema'] == nome_var and var['escopo'] == escopo_atual:
            return i
        elif var['lexema'] == nome_var and var['escopo'] == 'global':
            standby = i
            i += 1
        else:
            i += 1
    if standby >= 0:
        return standby
    else:
        global mensagens_erro
        mensagens_erro.append('Erro: Variável \'{}\' não declarada3'.format(nome_var))
        return -1


def declaracao_variavel(node):
    tipo = node.children[0].children[0].label
    lista_variaveis = node.children[2]
    insere_lista_variaveis(tipo, lista_variaveis)


def insere_lista_variaveis(tipo, lista_variaveis):
    filhos = lista_variaveis.children
    # Se tiver só 1 filho, é só a declaracao de 1 variavel
    for filho in filhos:
        erro_variavel = False
        if filho.label == 'var':  # se entrar aqui já é a variável
            id_variavel = filho.children[0].children[0].label
            try:
                # aqui a gente ta vendo se a variável tem indice
                indice = filho.children[1]
                expressao_indice = indice.children[1]
                exp_resolvida_indice = resolve_expressao(expressao_indice,tipo,None)

                if exp_resolvida_indice.type != 'INTEIRO':
                    mensagens_erro.append("Erro: índice de array '{}' não inteiro1".format(id_variavel))


            except:
                print("segue a vida")



            for var in variaveis_declaradas:
                if var['lexema'] == id_variavel and (var['escopo'] == escopo_atual):# or var['escopo'] == 'global'):
                    mensagens_warning.append("Aviso: Variável \"{}\" já declarada anteriormente".format(id_variavel))
                    erro_variavel = True
                    global erro
                    erro = True
                    break
            dim = 0
            dim1 = 0
            dim2 = 0
            if len(filho.children) > 1:
                # pode ser array ou matriz
                indice = filho.children[1]
                if len(indice.children) == 3:
                    # é array
                    expressao_indice_array = indice.children[1]
                    expressao_resolvida = resolve_expressao(expressao_indice_array, None, None)
                    tipo_expressao = expressao_resolvida.type
                    # if tipo_expressao != "INTEIRO":
                    #     mensagens_erro.append("Erro: índice de array '{}' não inteiro2".format(id_variavel))
                    dim = 1
                    dim1 = expressao_resolvida.label
                    dim2 = 0
                elif len(indice.children) == 4:
                    expressao_indice_matriz1 = indice.children[0].children[1]
                    expressao_indice_matriz2 = indice.children[2]

                    exp_resolvida1 = resolve_expressao(expressao_indice_matriz1, None, None)
                    exp_resolvida2 = resolve_expressao(expressao_indice_matriz2, None, None)

                    tipo_expressao1 = exp_resolvida1.type
                    tipo_expressao2 = exp_resolvida2.type

                    if tipo_expressao1 != "INTEIRO" or tipo_expressao2 != "INTEIRO":
                        mensagens_erro.append("Erro: índice de matriz '{}' não inteiro".format(id_variavel))
                    dim = 2
                    dim1 = exp_resolvida1.label
                    dim2 = exp_resolvida2.label
            variavel = {
                "lexema": id_variavel,
                "escopo": escopo_atual,
                "dim": dim,
                "tam_dim1": dim1,
                "tam_dim2": dim2,
                "inicializado": False,
                "tipo": tipo,
                "usada": False
            }
            if not erro_variavel:
                variaveis_declaradas.append(variavel)

        elif filho.label == "lista_variaveis":
            insere_lista_variaveis(tipo, filho)


def declaracao_funcao(node):
    print("declaracao_funcao")
    filhos = node.children
    if (len(filhos) > 1):
        tipo = filhos[0].children[0].children[0].label
        cabecalho = filhos[1]
    else:
        tipo = "vazio"
        cabecalho = filhos[0]

    id_func = cabecalho.children[0].children[0].label

    entra_escopo(id_func)

    if id_func in funcoes.keys():
        mensagens_erro.append("Erro: Já existe uma função com o nome {}".format(id_func))
        global erro
        erro = True

    funcoes[id_func] = {
        "tipo": tipo,
        "id_func": id_func,
        "parametros": [],
        "retornou": False,
        "utilizada": False,
    }
    lista_parametros = cabecalho.children[2]
    get_lista_parametros_funcao(id_func, lista_parametros)


def get_lista_parametros_funcao(id_funcao, node):
    for filho in node.children:
        if filho.label == 'lista_parametros':
            get_lista_parametros_funcao(id_funcao, filho)
        elif filho.label == 'parametro':
            filho_analisado = filho
            is_arranjo = False
            if filho.children[0].label == "parametro":
                filho_analisado = filho.children[0]
                is_arranjo = True

            tipo_param = filho_analisado.children[0].children[0].label
            id_param = filho_analisado.children[2].children[0].label

            funcoes[id_funcao]["parametros"].append({
                "id": id_param,
                "tipo": tipo_param,
                "is_arranjo": is_arranjo
            })
            # todo tem que ver a parte da matriz
            if is_arranjo:
                dim = 1
            else:
                dim = 0
            variaveis_declaradas.append({
                "lexema": id_param,
                "escopo": escopo_atual,
                "dim": dim,
                "tam_dim1": dim,
                "tam_dim2": 0,
                "tipo": tipo_param,
                "inicializado": True,
                "usada": False
            })


def entra_escopo(novo_escopo):
    global escopo_antigo
    global escopo_atual
    escopo_antigo = escopo_atual
    escopo_atual = novo_escopo


def sai_escopo():
    global escopo_atual
    global escopo_antigo
    escopo_atual = escopo_antigo
    escopo_antigo = ""


def print_warnings():
    for warning in mensagens_warning:
        print(warning)


def print_erro():
    for erro in mensagens_erro:
        print(erro)

def verifica_variaveis_usadas():
    for var in variaveis_declaradas:
        if not var['usada']:
            mensagens_warning.append(
                "Aviso: Variável '{}' declarada e não utilizada em '{}'".format(var['lexema'],var['escopo'])
            )

def verifica_existe_principal():
    if "principal" not in funcoes.keys():
        mensagens_erro.append(
            "Erro: Função principal não declarada"
        )
        global erro
        erro = True

def verifica_funcoes_utilizadas():
    for funcao in funcoes:
        if funcao != "principal":
            func_atual = funcoes[funcao]
            if func_atual['utilizada'] == False:
                mensagens_warning.append("Aviso: Função ‘{}’ declarada, mas não utilizada.".format(funcao))

def semantica_main(data):
    raiz = sin.retorna_root(data)
    if raiz is None:
        print("Árvore não foi gerada!")
    else:
        print("Árvore gerada!")
        analisa_arvore(raiz)
        print("---------------------------------")
        verifica_existe_principal()
        verifica_variaveis_usadas()
        verifica_funcoes_utilizadas()
        print_erro()
        print_warnings()
        print("---------------------------------")
        if raiz and raiz.children != ():
            try:
                print("Generating Syntax Tree Graph...")
                UniqueDotExporter(raiz).to_picture(argv[1] + ".unique.ast.png")
                print("Graph was generated.\nOutput file: " + argv[1] + ".ast.png")
            except IndexError:
                print("Generating Syntax Tree Graph... v2")
                UniqueDotExporter(raiz).to_picture("arvoregerada.unique.ast.png")
                print("Graph was generated.\nOutput file: " + " arvoregerada.ast.png")
        return raiz


if __name__ == "__main__":
    if (len(argv) < 2):
        file = 'geracao-codigo-testes/testesimples.tpp'
    else:
        file = argv[1]
    data = file
    semantica_main(data)
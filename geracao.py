from sys import argv
import json
from semantica import semantica_main, variaveis_declaradas, funcoes, erro

from llvmlite import ir
from llvmlite import binding as llvm

lista_ponteiros_funcoes = []
lista_ponteiros_variaveis = []
cont_se = 0
cont_repita = 0

operadores = ["+", "*", "/", "-"]


def cria_lista_var_global(lista_variaveis, tipo, modulo):
    for filho in lista_variaveis.children:
        if filho.label == 'lista_variaveis':
            cria_lista_var_global(filho, tipo, modulo)
        elif filho.label == 'var':
            if tipo == "INTEIRO":
                variavel = ir.GlobalVariable(modulo, ir.IntType(32), filho.leaves[0].label)
                variavel.initializer = ir.Constant(ir.IntType(32), 0)

            elif tipo == "FLUTUANTE":
                variavel = ir.GlobalVariable(modulo, ir.FloatType(), filho.leaves[0].label)
                variavel.initializer = ir.Constant(ir.FloatType(), 0.0)

            variavel.linkage = "common"
            variavel.align = 4

            lista_ponteiros_variaveis.append(variavel)


def cria_lista_var_local(lista_variaveis, tipo, modulo, builder):
    for filho in lista_variaveis.children:
        if filho.label == 'lista_variaveis':
            cria_lista_var_local(filho, tipo, modulo, builder)
        elif filho.label == 'var':
            if tipo == "INTEIRO":
                variavel = builder.alloca(ir.IntType(32), name=filho.leaves[0].label)

            elif tipo == "FLUTUANTE":
                variavel = builder.alloca(ir.FloatType(), name=filho.leaves[0].label)

            variavel.linkage = "common"
            variavel.align = 4

            lista_ponteiros_variaveis.append(variavel)


def declara_variavel_global(node, modulo):
    tipo = node.children[0].children[0].label
    lista_variaveis = node.children[2]
    cria_lista_var_global(lista_variaveis, tipo, modulo)


def percorre_arvore(node, modulo):
    if node:
        if node.name == 'declaracao_variaveis':
            print("declarando variável global")
            declara_variavel_global(node, modulo)
            return
        elif node.name == 'declaracao_funcao':
            print("declarando funcao")
            declaracao_funcao(node, modulo)
            return
        filhos = node.children
        for filho in filhos:
            percorre_arvore(filho, modulo)


def declaracao_funcao(no, modulo):
    cabecalho = no.children[1]
    tipo_retorno_func = no.children[0].children[0].label
    if tipo_retorno_func == "INTEIRO":
        tipo_de_retorno = ir.IntType(32)
    elif tipo_retorno_func == "FLUTUANTE":
        tipo_de_retorno = ir.FloatType()

    id_func = cabecalho.children[0].children[0].label
    if id_func == "principal":
        id_func = "main"

    parametros_fun = cabecalho.children[2]

    tipo_da_funcao = ir.FunctionType(tipo_de_retorno, [])
    funcao = ir.Function(modulo, tipo_da_funcao, name=id_func)
    lista_ponteiros_funcoes.append(funcao)
    bloco_de_entrada = funcao.append_basic_block('%s.start' % id_func)
    builder = ir.IRBuilder(bloco_de_entrada)
    retorna = builder.alloca(tipo_de_retorno, name='return')
    retorna.align = 4
    lista_ponteiros_variaveis.append(retorna)
    corpo = cabecalho.children[4]
    resolve_corpo(corpo, modulo, builder)


def resolve_corpo(node, modulo, builder):
    if node:
        if node.label == "declaracao_variaveis":
            resolve_declaracao_variaveis_local(node, builder, modulo)
            return
        elif node.label == ":=":
            print("atribuicao na func - OK")
            resolve_atribuicao(node, modulo, builder)
            return
        elif node.label == "se":
            print("se na func - OK")
            resolve_se(node, modulo, builder)
            return
        elif node.label == "repita":
            print("repita na func - OK")
            resolve_repita(node, modulo, builder)
            return
        elif node.label == "leia":
            print("leia na func - OK")
            resolve_leia(node, modulo, builder)
            return
        elif node.label == "escreva":
            print("escreva na func - OK")
            resolve_escreva(node, modulo, builder)
        elif node.label == "retorna":
            print("retorna na func - OK")
            resolve_retorna(node, modulo, builder)
            return
        for filho in node.children:
            resolve_corpo(filho, modulo, builder)


def resolve_repita(node, modulo, builder):
    repita = builder.append_basic_block("repita")
    ate = builder.append_basic_block('ate')
    repita_fim = builder.append_basic_block('repita_fim')

    corpo = node.children[1]

    builder.branch(repita)
    builder.position_at_end(repita)

    resolve_corpo(corpo, modulo, builder)

    builder.branch(ate)
    builder.position_at_end(ate)

    expressao = node.children[3].children[0]
    var_temp_left, var_temp_right = resolve_expressao_logica(expressao.children[0], expressao.children[1], builder)

    operador = expressao.label
    if operador == "=":
        operador = "=="

    comp = builder.icmp_signed("==", var_temp_left, var_temp_right, name='expression')
    builder.cbranch(comp, repita_fim, repita)
    builder.position_at_end(repita_fim)


def resolve_leia(node, modulo, builder):
    var = node.children[0]
    nome_var = var.children[0].children[0].label

    i = 0
    while i < len(lista_ponteiros_variaveis):
        if lista_ponteiros_variaveis[i].name == nome_var:
            ponteiro_var = lista_ponteiros_variaveis[i]
        i = i + 1

    if ponteiro_var.type.intrinsic_name == "p0f32":
        resultado_leia = builder.call(leiaF, args=[])
    else:
        resultado_leia = builder.call(leiaI, args=[])

    builder.store(resultado_leia, ponteiro_var)

    # return builder.load(filho_direita, name='varTemporaria_var')

    print(node)


def resolve_expressao_logica(filho_esquerdo, filho_direito, builder):
    """
    Resolve a expressao lógica, e retorna o cara da esquerda e o cara da direita
    """
    filho_esq_expressao = filho_esquerdo
    tipo_filho_esq, tipo_var_filho_esq = filho_esq_expressao.id.split('-')

    filho_dir_expressao = filho_direito
    tipo_filho_dir, tipo_var_filho_dir = filho_dir_expressao.id.split('-')

    if tipo_filho_esq == "var":
        i = 0
        while i < len(lista_ponteiros_variaveis):
            if lista_ponteiros_variaveis[i].name == filho_esq_expressao.label:
                filho_esquerda = lista_ponteiros_variaveis[i]
            i = i + 1
        varTempLeft = builder.load(filho_esquerda, name='varTempLeft')

    elif tipo_var_filho_esq.lower() == "inteiro":
        varTempLeft = ir.Constant(ir.IntType(32), int(filho_esq_expressao.label))
    elif tipo_var_filho_esq.lower() == "flutuante":
        varTempLeft = ir.Constant(ir.FloatType(), float(filho_esq_expressao.label))

    if tipo_filho_dir == "var":
        i = 0
        while i < len(lista_ponteiros_variaveis):
            if lista_ponteiros_variaveis[i].name == filho_dir_expressao.label:
                filho_direita = lista_ponteiros_variaveis[i]
            i = i + 1
        varTempRight = builder.load(filho_direita, name='varTempRight')
    elif tipo_filho_dir == "numero":
        if tipo_var_filho_dir.lower() == "inteiro":
            varTempRight = ir.Constant(ir.IntType(32), int(filho_dir_expressao.label))
        elif tipo_var_filho_esq.lower() == "flutuante":
            varTempRight = ir.Constant(ir.FloatType(), float(filho_dir_expressao.label))

    return varTempLeft, varTempRight


def resolve_se(node, modulo, builder):
    iftrue = lista_ponteiros_funcoes[-1].append_basic_block("iftrue_" + str(cont_se))
    iffalse = lista_ponteiros_funcoes[-1].append_basic_block("iffalse_" + str(cont_se))
    ifend = lista_ponteiros_funcoes[-1].append_basic_block("ifend_" + str(cont_se))

    expressao = node.children[1].children[0]
    se_corpo1 = node.children[3]
    se_corpo2 = node.children[5]

    operador = expressao.label

    varTempLeft, varTempRight = resolve_expressao_logica(expressao.children[0], expressao.children[1], builder)

    aux = builder.icmp_signed(operador, varTempLeft, varTempRight, name="if_" + str(cont_se))
    builder.cbranch(aux, iftrue, iffalse)
    builder.position_at_start(iftrue)
    resolve_corpo(se_corpo1, modulo, builder)
    builder.branch(ifend)
    builder.position_at_start(iffalse)
    resolve_corpo(se_corpo2, modulo, builder)
    builder.branch(ifend)
    builder.position_at_end(ifend)
    contSe = cont_se + 1


def resolve_escreva(node, modulo, builder):
    expressao_retorna = node.children[0]
    expressao_resolvida_retorna = resolve_expressao(expressao_retorna, modulo, builder)

    if expressao_resolvida_retorna.type.intrinsic_name == "i32":
        varAux = builder.alloca(ir.IntType(32), 4, "temp")
        builder.store(expressao_resolvida_retorna, varAux)

        builder.call(escrevaI, args=[builder.load(varAux)])
    else:
        varAux = builder.alloca(ir.FloatType(), 4, "temp")
        builder.store(expressao_resolvida_retorna, varAux)
        # builder.call(escrevaF, args=[builder.load(varAux)])
        builder.call(escrevaF, args=[builder.load(varAux)])


def resolve_declaracao_variaveis_local(node, builder, modulo):
    tipo = node.children[0].children[0].label

    lista_var = node.children[2]
    cria_lista_var_local(lista_var, tipo, modulo, builder)
    print("declara var local")


def resolve_atribuicao(node, modulo, builder):
    var_nome = node.children[0].label
    i = 0
    while i < len(lista_ponteiros_variaveis):
        if lista_ponteiros_variaveis[i].name == var_nome:
            var = lista_ponteiros_variaveis[i]
        i = i + 1

    resultado = resolve_expressao(node.children[1], modulo, builder)
    if resultado is None:
        resultado = ir.Constant(ir.IntType(32), 0)
    builder.store(resultado, var)


def resolve_retorna(node, modulo, builder):
    i = 0
    while i < len(lista_ponteiros_variaveis):
        if lista_ponteiros_variaveis[i].name == "return":
            retorna = builder.load(lista_ponteiros_variaveis[i], name="retorna", align=4)
        i = i + 1
    nome = lista_ponteiros_funcoes[-1].name
    bloco_de_saida = lista_ponteiros_funcoes[-1].append_basic_block('%s.end' % nome)
    builder.branch(bloco_de_saida)
    builder.position_at_end(bloco_de_saida)
    expressao = node.children[0]
    res = resolve_expressao(expressao, modulo, builder)
    i = 0
    while i < len(lista_ponteiros_variaveis):
        if lista_ponteiros_variaveis[i].name == "return":
            variavel_de_retorno = lista_ponteiros_variaveis[i]
        i = i + 1
    builder.store(res, variavel_de_retorno)
    builder.ret(builder.load(variavel_de_retorno, name="ret"))
    # builder.ret(res)


def resolve_expressao(node, modulo, builder):
    split_node_id = node.id.split("-")
    tipo_nome = split_node_id[0]
    tipo_exp = split_node_id[1]

    if tipo_nome == "numero":
        print("expressao_num")
        valor_num = node.label
        if tipo_exp.lower() == "inteiro":
            valor_num = int(valor_num)
            return ir.Constant(ir.IntType(32), valor_num)
        elif tipo_exp.lower() == 'flutuante':
            valor_num = float(valor_num)
            return ir.Constant(ir.FloatType(), valor_num)

    elif tipo_nome == "chamada_funcao":
        pass

    elif tipo_nome == "var":
        var_id = node.label
        i = 0
        while i < len(lista_ponteiros_variaveis):
            if lista_ponteiros_variaveis[i].name == var_id:
                filho_direita = lista_ponteiros_variaveis[i]
            i = i + 1
        return builder.load(filho_direita, name='varTemporaria_var')

    elif tipo_nome in operadores:
        filho_esq = node.children[0]
        tipo_filho_esq, tipo_var_filho_esq = filho_esq.id.split('-')
        filho_dir = node.children[1]
        tipo_filho_dir, tipo_var_filho_dir = filho_dir.id.split('-')

        operador = node.label
        valor_filho_esquerda = str(filho_esq.label)
        valor_filho_direita = str(filho_dir.label)

        if tipo_filho_esq == "var":
            i = 0
            while i < len(lista_ponteiros_variaveis):
                if str(lista_ponteiros_variaveis[i].name) == valor_filho_esquerda:
                    filho_esquerda = lista_ponteiros_variaveis[i]
                i = i + 1
            var_temp_esq = builder.load(filho_esquerda, name='varTempLedt')

        if tipo_filho_dir == "var":
            i = 0
            while i < len(lista_ponteiros_variaveis):
                if str(lista_ponteiros_variaveis[i].name) == valor_filho_direita:
                    filho_direita = lista_ponteiros_variaveis[i]
                i = i + 1
            var_temp_dir = builder.load(filho_direita, name='varTempRight')

        elif tipo_filho_esq == "numero":
            if tipo_var_filho_esq.lower() == "inteiro":
                var_temp_esq = ir.Constant(ir.IntType(32), int(valor_filho_esquerda))
            elif tipo_var_filho_esq.lower() == "flutuante":
                var_temp_esq = ir.Constant(ir.FloatType(), float(valor_filho_esquerda))

        if tipo_filho_dir == "numero":
            if tipo_var_filho_dir.lower() == "inteiro":
                var_temp_dir = ir.Constant(ir.IntType(32), int(valor_filho_direita))
            elif tipo_var_filho_dir.lower() == "flutuante":
                var_temp_dir = ir.Constant(ir.FloatType(), float(valor_filho_direita))

        if operador == "+":
            if tipo_var_filho_dir == tipo_var_filho_esq and tipo_var_filho_dir.lower() == "inteiro":
                var_temp_add = builder.add(var_temp_esq, var_temp_dir)
            else:
                var_temp_add = builder.fadd(var_temp_esq, var_temp_dir)
            return var_temp_add
        elif operador == "-":
            var_temp_sub = builder.sub(var_temp_esq, var_temp_dir, name="varTempSub")
            return var_temp_sub
        elif operador == "*":
            var_temp_mult = builder.mul(var_temp_esq, var_temp_dir, name='varTempMult')
            return var_temp_mult
        elif operador == "/":
            var_temp_div = builder.sdiv(var_temp_esq, var_temp_dir, name='varTempDiv')
            return var_temp_div


if __name__ == '__main__':
    if len(argv) < 2:
        file = 'geracao-codigo-testes/testesimples.tpp'
    else:
        file = argv[1]
    data = file

    raiz = semantica_main(data)

    print("------------------------------------------")
    print("Geração de código®")
    print("------------------------------------------")

    llvm.initialize()
    llvm.initialize_all_targets()
    llvm.initialize_native_target()
    llvm.initialize_native_asmparser()

    moduloFinal = ir.Module(file)
    moduloFinal.triple = llvm.get_process_triple()
    target = llvm.Target.from_triple(moduloFinal.triple)
    targetMachine = target.create_target_machine()
    moduloFinal.data_layout = targetMachine.target_data
    print("------------------------------------------")
    print("Percorrendo a árvore na ger. cod®")
    print("------------------------------------------")

    _escrevaI = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    escrevaI = ir.Function(moduloFinal, _escrevaI, "escrevaInteiro")

    _escrevaF = ir.FunctionType(ir.VoidType(), [ir.FloatType()])
    escrevaF = ir.Function(moduloFinal, _escrevaF, "escrevaFlutuante")

    _leiaI = ir.FunctionType(ir.IntType(32), [])
    leiaI = ir.Function(moduloFinal, _leiaI, "leiaInteiro")

    _leiaF = ir.FunctionType(ir.FloatType(), [])
    leiaF = ir.Function(moduloFinal, _leiaF, "leiaFlutuante")

    percorre_arvore(raiz, moduloFinal)

    # print(json.dumps(variaveis_declaradas, indent=4))
    # print(json.dumps(funcoes, indent=4))
    # print(erro)

    with open("teste.ll", 'w') as arq:
        arq.write(str(moduloFinal))
    # print(moduloFinal)
    print("Executando o código")
    print("|------------------------------------------|")

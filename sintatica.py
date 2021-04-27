from os import P_NOWAIT, name
from sys import argv, exit

import logging
from typing import TYPE_CHECKING

logging.basicConfig(
     level = logging.DEBUG,
     filename = "log/log-parser.txt",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

# Importando o YACC
import ply.yacc as yacc

# Importando minha lexica
from lexica import tokens

# Importando as coisas pra fazer a árvore
from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from anytree import RenderTree, AsciiStyle, node

# Variável que guarda se teve algum erro

erro = False

# Sub-árvore.
#       (programa)
#           |
#   (lista_declaracoes)
#     /     |      \
#   ...    ...     ...
def p_programa(p):
    """programa : lista_declaracoes"""
    global root

    programa = MyNode(name='programa', type='PROGRAMA')

    root = programa
    p[0] = programa
    p[1].parent = programa

# Sub-árvore.
#    (lista_declaracoes)                          (lista_declaracoes)
#          /           \                                    |
# (lista_declaracoes)  (declaracao)                    (declaracao)
def p_lista_declaracoes(p):
    """lista_declaracoes : lista_declaracoes declaracao
                        | declaracao
    """
    pai = MyNode(name='lista_declaracoes', type='LISTA_DECLARACOES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


# Sub-árvore.
#      (declaracao)
#           |
#  (declaracao_variaveis ou
#   inicializacao_variaveis ou
#   declaracao_funcao)
def p_declaracao(p):
    """declaracao : declaracao_variaveis
                | inicializacao_variaveis
                | declaracao_funcao
    """
    pai = MyNode(name='declaracao', type='DECLARACAO')
    p[0] = pai
    p[1].parent = pai

# Sub-árvore.
#      (declaracao_variaveis)
#      /         |           \
# (tipo)    (DOIS_PONTOS)    (lista_variaveis)
#                |
#
def p_declaracao_variaveis(p):
    """declaracao_variaveis : tipo DOIS_PONTOS lista_variaveis"""
    pai = MyNode(name='declaracao_variaveis', type='DECLARACAO_VARIAVEIS')
    p[0] = pai
    p[1].parent = pai
    
    dois_pontos = MyNode(name='dois_pontos', type='DOIS_PONTOS', parent=pai)
    dois_pontos_simbolo = MyNode(name=p[2], type='SIMBOLO', parent=dois_pontos)
    p[2] = dois_pontos

    p[3].parent = pai

def p_declaracao_variaveis_error(p):
    """declaracao_variaveis : tipo DOIS_PONTOS error"""
    print('Erro na declaração de variável')
    error_line = p.lineno(2)
    father = MyNode(name='ERROR::{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father

# Sub-árvore.
#   (inicializacao_variaveis)
#              |
#         (atribuicao)
def p_inicializacao_variaveis(p):
    """inicializacao_variaveis : atribuicao"""
    pai = MyNode(name='inicializacao_variaveis', type='INICIALIZACAO_VARIAVEIS')

    p[0] = pai
    p[1].parent = pai

# Sub-árvore.
#                    (lista_variaveis)
#                             |
#                   /                   \
# (lista_variaveis) (',') (var)        (var) 

def p_lista_variaveis(p):
    """lista_variaveis : lista_variaveis VIRGULA var
                        | var
    """
    
    pai = MyNode(name='lista_variaveis', type='LISTA_VARIAVEIS')
    p[0] = pai
    p[1].parent = pai 
    if len(p) > 2:
        
        virgula = MyNode(name='virgula', type='VIRGULA', parent=pai)
        virgula_simbolo = MyNode(name=',', type='simbolo', parent=virgula)
        p[2] = virgula

        p[3].parent = pai

# Sub-árvore.
#        (var)
#          |
#   /              \
# (ID)         (ID)(indice) 

def p_var(p):
    """var : ID 
            | ID indice"""
    pai = MyNode(name='var', type='VAR')
    p[0] = pai 

    node_id = MyNode(name='ID', type='ID', parent=pai)
    node_id_simbolo = MyNode(name=p[1], type='SIMBOLO',parent=node_id)
    p[1] = node_id

    if len(p) > 2:
        p[2].parent = pai


# Sub-árvore
#                        (indice)
#                            |
#              /                        \
# (indice)([)(expressao)(])      ([)(expressao)(])
#  

def p_indice(p):
    """indice : indice ABRE_COLCHETE expressao FECHA_COLCHETE
                | ABRE_COLCHETE expressao FECHA_COLCHETE
    """
    pai = MyNode(name='indice', type='INDICE')
    p[0] = pai
    if len(p) == 5:
        p[1].parent = pai

        abre_colchete = MyNode(name='abre_colchete', type='ABRE_COLCHETE',parent=pai)
        abre_colchete_simbolo = MyNode(name='[', type='SIMBOLO',parent=abre_colchete)

        p[2] = abre_colchete

        p[3].parent = pai

        fecha_colchete = MyNode(name='fecha_colchete', type='FECHA_COLCHETE',parent=pai)
        fecha_colchete_simbolo = MyNode(name=']', type='SIMBOLO',parent=fecha_colchete)

        p[4] = fecha_colchete
    else: 
        abre_colchete = MyNode(name='abre_colchete', type='ABRE_COLCHETE',parent=pai)
        abre_colchete_simbolo = MyNode(name='[', type='SIMBOLO',parent=abre_colchete)

        p[1] = abre_colchete

        p[2].parent = pai

        fecha_colchete = MyNode(name='fecha_colchete', type='FECHA_COLCHETE',parent=pai)
        fecha_colchete_simbolo = MyNode(name=']', type='SIMBOLO',parent=fecha_colchete)

        p[3] = fecha_colchete

def p_indice_error(p):
    """indice : ABRE_COLCHETE error FECHA_COLCHETE
                | indice ABRE_COLCHETE error FECHA_COLCHETE
    """

    print("Erro na definicao do indice. Expressao ou indice.")

    # print("Erro:p[0]:{p0}, p[1]:{p1}, p[2]:{p2}, p[3]:{p3}".format(
    #     p0=p[0], p1=p[1], p2=p[2], p3=p[3]))
    error_line = p.lineno(2)
    father = MyNode(name='ERROR::{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father

# Sub-árvore:
#    (tipo)
#      |
#  (FLUTUANTE)
def p_tipo(p):
    """tipo : INTEIRO
        | FLUTUANTE
    """

    pai = MyNode(name='tipo', type='TIPO')
    p[0] = pai

    if p[1] == 'inteiro':
        inteiro = MyNode(name='INTEIRO', type='INTEIRO', parent=pai)
        inteiro_simbolo = MyNode(name=p[1], type=p[1].upper(), parent=inteiro)
        p[1] = inteiro

    else:
        flutuante = MyNode(name='FLUTUANTE', type='FLUTUANTE', parent=pai)
        flutuante_simbolo = MyNode(name=p[1], type=p[1].upper(), parent=flutuante)
        p[1] = flutuante

# Sub-árvore:
#        (declaracao_funcao)
#                 | 
#          /              \ 
# (tipo) (cabecalho)    (cabecalho)

def p_declaracao_funcao(p):
    """declaracao_funcao : tipo cabecalho 
                        | cabecalho 
    """
    pai = MyNode(name='declaracao_funcao', type='DECLARACAO_FUNCAO')
    p[0] = pai
    p[1].parent = pai


    if len(p) == 3:
        p[2].parent = pai

# Sub-árvore:
#                (cabecalho)
#                      |
# (ID) ('(') (lista_parametros)(')')(corpo)(FIM)

def p_cabecalho(p):
    """cabecalho : ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM"""
    pai = MyNode(name='cabecalho', type='CABECALHO')
    p[0] = pai

    node_id = MyNode(name="ID", type='ID', parent=pai)
    node_id_simbolo = MyNode(name=p[1], type='ID', parent=node_id)
    p[1] = node_id

    abre_parentese = MyNode(name='ABRE_PARENTESE',type='ABRE_PARENTESE',parent=pai)
    abre_parentese_simbolo = MyNode(name='(',type='SIMBOLO',parent=abre_parentese)
    p[2] = abre_parentese

    p[3].parent = pai

    fecha_parentese = MyNode(name='FECHA_PARENTESE',type='FECHA_PARENTESE',parent=pai)
    fecha_parentese_simbolo = MyNode(name=")",type='SIMBOLO',parent=fecha_parentese)
    p[4] = fecha_parentese

    p[5].parent = pai

    fim = MyNode(name='FIM', type='FIM', parent=pai)
    fim_simbolo = MyNode(name='fim', type='FIM', parent=fim)
    p[6] = fim



# Sub-árvore:
#                                      (lista_parametros)
#                                              |
#                      /                       |          \
# (lista_parametros) (',') (parametro)    (parametro)   (vazio)
def p_lista_parametros(p):
    """lista_parametros : lista_parametros VIRGULA parametro
                    | parametro
                    | vazio
    """
   
    pai = MyNode(name='lista_parametros', type='LISTA_PARAMETROS')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        virgula = MyNode(name='virgula', type='VIRGULA', parent=pai)
        virgula_simbolo = MyNode(name=',', type='SIMBOLO', parent=virgula)
        p[2] = virgula

        p[3].parent = pai


#                (parametro)
#                     |
#          /                      \
# (tipo) (":") (ID)     (parametro) ("[")("]")
def p_parametro(p):
    """parametro : tipo DOIS_PONTOS ID
                | parametro ABRE_COLCHETE FECHA_COLCHETE
    """
    pai = MyNode(name='parametro', type='PARAMETRO')
    p[0] = pai
    p[1].parent = pai
    if p[2] == ':':
        dois_pontos = MyNode(name="dois_pontos",type='DOIS_PONTOS', parent=pai)
        dois_pontos_simbolo = MyNode(name=":",type='SIMBOLO', parent=dois_pontos)
        p[2] = dois_pontos 

        node_id = MyNode(name='id', type='ID', parent=pai)
        filho_id = MyNode(name=p[3], type='ID', parent=node_id)
        p[3] = dois_pontos 
    else:
        abre_colchete = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        abre_colchete_simbolo = MyNode(name='[', type='SIMBOLO', parent=abre_colchete)
        p[2] = abre_colchete

        fecha_colchete = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        fecha_colchete_simbolo = MyNode(name=']', type='SIMBOLO', parent=fecha_colchete)
        p[2] = fecha_colchete

#             (corpo)
#                |
#        /              \
# (corpo) (acao)      (vazio)


def p_corpo(p):
    """corpo : corpo acao
            | vazio
    """
    pai = MyNode(name='corpo', type='CORPO')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


def p_acao(p):
    """acao : expressao
        | declaracao_variaveis
        | se
        | repita
        | leia
        | escreva
        | retorna
    """
    pai = MyNode(name='acao', type='ACAO')
    p[0] = pai
    p[1].parent = pai

# Sub-árvore:
#       ________ (se) ________________________________
#      /    /          \      \         \      \      \
# (SE) (expressao)  (ENTAO)  (corpo) (SENAO) (corpo) (FIM)
#  |       |           |
# (se)   (...)      (então) ....
def p_se(p):
    """se : SE expressao ENTAO corpo FIM
          | SE expressao ENTAO corpo SENAO corpo FIM
    """
    pai = MyNode(name='se', type='SE')
    p[0] = pai

    se = MyNode(name='se',type='SE',parent=pai)
    se_simbolo = MyNode(name=p[1],type='SE',parent=se)
    p[1] = se

    p[2].parent = pai

    entao = MyNode(name='entao',type='ENTAO', parent=pai)
    entao_simbolo = MyNode(name=p[3],type='ENTAO', parent=entao)
    p[3] = entao

    p[4].parent = pai

    if len(p) == 8:
        senao = MyNode(name='senao',type='SENAO',parent=pai)
        senao_simbolo = MyNode(name=p[5],type='SENAO',parent=senao)
        p[5] = senao

        p[6].parent = pai

        fim = MyNode(name='FIM', type='FIM', parent=pai)
        fim_simbolo = MyNode(name=p[7], type='FIM', parent=fim)
        p[7] = fim
    else:
        fim = MyNode(name='FIM', type='FIM', parent=pai)
        fim_simbolo = MyNode(name=p[5], type='FIM', parent=fim)
        p[5] = fim

def p_se_error(p):
    """se : SE expressao ENTAO corpo SENAO corpo error
    """
    print("Erro na definicao do indice. Expressao ou indice.")

    # print("Erro:p[0]:{p0}, p[1]:{p1}, p[2]:{p2}, p[3]:{p3}".format(
    #     p0=p[0], p1=p[1], p2=p[2], p3=p[3]))
    error_line = p.lineno(2)
    father = MyNode(name='ERROR::{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father



def p_repita(p):
    """repita : REPITA corpo ATE expressao"""
    pai = MyNode(name='repita',type='REPITA')
    p[0] = pai

    repita = MyNode(name='REPITA',type='REPITA',parent=pai)
    repita_simbolo = MyNode(name=p[1],type='REPITA',parent=repita)
    p[1] = repita

    p[2].parent = pai

    ate = MyNode(name='ATE',type='ATE',parent=pai)
    ate_simbolo = MyNode(name=p[3],type='ATE',parent=ate)
    p[3] = repita

    p[4].parent = pai
    
def p_atribuicao(p):
    """atribuicao : var ATRIBUICAO expressao"""
    pai = MyNode(name='atribuicao', type='ATRIBUICAO')
    p[0] = pai

    p[1].parent = pai

    atribuicao = MyNode(name='ATRIBUICAO', type='ATRIBUICAO', parent=pai)
    atribuicao_simbolo = MyNode(name=':=', type='SIMBOLO', parent=atribuicao)
    p[2] = atribuicao

    p[3].parent = pai

def p_leia(p):
    """leia : LEIA ABRE_PARENTESE var FECHA_PARENTESE"""

    pai = MyNode(name='leia', type='LEIA')
    p[0] = pai

    leia = MyNode(name='LEIA', type='LEIA', parent=pai)
    leia_simbolo = MyNode(name=p[1], type='LEIA', parent=leia)
    p[1] = leia

    abre_parentese = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    abre_parentese_simbolo = MyNode(name='(', type='SIMBOLO', parent=abre_parentese)
    p[2] = abre_parentese

    p[3].parent = pai  # var

    fecha_parentese = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    fecha_parentese_simbolo = MyNode(name=')', type='SIMBOLO', parent=fecha_parentese)
    p[4] = fecha_parentese

def p_escreva(p):
    """escreva : ESCREVA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='escreva', type='ESCREVA')
    p[0] = pai

    escreva = MyNode(name='ESCREVA', type='ESCREVA', parent=pai)
    escreva_simbolo = MyNode(name=p[1], type='ESCREVA', parent=escreva)
    p[1] = escreva

    abre_parentese = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    abre_parentese_simbolo = MyNode(name='(', type='SIMBOLO', parent=abre_parentese)
    p[2] = abre_parentese

    p[3].parent = pai

    fecha_parentese = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    fecha_parentese_simbolo = MyNode(name=')', type='SIMBOLO', parent=fecha_parentese)
    p[4] = fecha_parentese

def p_retorna(p):
    """retorna : RETORNA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='retorna', type='RETORNA')
    p[0] = pai

    retorna = MyNode(name='RETORNA', type='RETORNA', parent=pai)
    retorna_simbolo = MyNode(name=p[1], type='RETORNA', parent=retorna)
    p[1] = retorna

    abre_parentese = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    abre_parentese_simbolo = MyNode(name='(', type='SIMBOLO', parent=abre_parentese)
    p[2] = abre_parentese

    p[3].parent = pai

    fecha_parentese = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    fecha_parentese_simbolo = MyNode(name=')', type='SIMBOLO', parent=fecha_parentese)
    p[4] = fecha_parentese

def p_expressao(p):
    """expressao : expressao_logica
                    | atribuicao
    """
    pai = MyNode(name='expressao', type='EXPRESSAO')
    p[0] = pai
    p[1].parent = pai

def p_expressao_logica(p):
    """expressao_logica : expressao_simples
                    | expressao_logica operador_logico expressao_simples
    """
    pai = MyNode(name='expressao_logica', type='EXPRESSAO_LOGICA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_simples(p):
    """expressao_simples : expressao_aditiva
                        | expressao_simples operador_relacional expressao_aditiva
    """

    pai = MyNode(name='expressao_simples', type='EXPRESSAO_SIMPLES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_aditiva(p):
    """expressao_aditiva : expressao_multiplicativa
                        | expressao_aditiva operador_soma expressao_multiplicativa
    """

    pai = MyNode(name='expressao_aditiva', type='EXPRESSAO_ADITIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_multiplicativa(p):
    """expressao_multiplicativa : expressao_unaria
                               | expressao_multiplicativa operador_multiplicacao expressao_unaria
        """

    pai = MyNode(name='expressao_multiplicativa',
                 type='EXPRESSAO_MULTIPLICATIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_unaria(p):
    """expressao_unaria : fator
                        | operador_soma fator
                        | operador_negacao fator
        """
    pai = MyNode(name='expressao_unaria', type='EXPRESSAO_UNARIA')
    p[0] = pai
    p[1].parent = pai

    if p[1] == '!':
        negacao = MyNode(name='operador_negacao',type='OPERADOR_NEGACAO', parent=pai)
        negacao_simbolo = MyNode(name=p[1],type='OPERADOR_NEGACAO', parent=negacao)
        p[1] = negacao
    else:
        p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai

def p_operador_relacional(p):
    """operador_relacional : MENOR
                            | MAIOR
                            | IGUAL
                            | DIFERENTE 
                            | MENOR_IGUAL
                            | MAIOR_IGUAL
    """
    pai = MyNode(name='operador_relacional', type='OPERADOR_RELACIONAL')
    p[0] = pai

    if p[1] == "<":
        filho = MyNode(name='MENOR', type='MENOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">":
        filho = MyNode(name='MAIOR', type='MAIOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "=":
        filho = MyNode(name='IGUAL', type='IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<>":
        filho = MyNode(name='DIFERENTE', type='DIFERENTE', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<=":
        filho = MyNode(name='MENOR_IGUAL', type='MENOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">=":
        filho = MyNode(name='MAIOR_IGUAL', type='MAIOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    else:
        print('Erro operador relacional')

    p[1] = filho

def p_operador_soma(p):
    """operador_soma : MAIS
                    | MENOS
    """
    pai = MyNode(name='operador_soma',type='OPERADOR_SOMA')
    p[0] = pai

    if p[1] == "+":
        mais = MyNode(name='MAIS', type='MAIS',parent=pai)
        mais_simbolo = MyNode(name='+', type='SIMBOLO', parent=mais)
        p[1] = mais
    else:
       menos = MyNode(name='MENOS', type='MENOS',parent=pai)
       menos_simbolo = MyNode(name='-', type='SIMBOLO', parent=menos)
       p[1] = menos

def p_operador_logico(p):
    """operador_logico : E_LOGICO
                    | OU_LOGICO
    """
    pai = MyNode(name='operador_logico', type='OPERADOR_LOGICO')
    p[0] = pai

    if p[1] == "E":
        node = MyNode(name='E_LOGICO', type='E_LOGICO',parent=pai)
    else:
        node = MyNode(name="OU_LOGICO", type='OU_LOGICO',parent=pai)

    node_simbolo = MyNode(name=p[1], type='SIMBOLO',parent=node)
    p[1] = node

def p_operador_negacao(p):
    """operador_negacao : NEGACAO"""
    pai = MyNode(name='operador_negacao',type='OPERADOR_NEGACAO')
    nao = MyNode(name='NEGACAO', type='NEGACAO', parent=pai)
    nao_simbolo = MyNode(name=p[1], type='SIMBOLO', parent=nao)

    p[1] = nao

def p_operador_multiplicacao(p):
    """operador_multiplicacao : MULTIPLICACAO
                            | DIVISAO
    """
    pai = MyNode(name='operador_multiplicacao',type='OPERADOR_MULTIPLICACAO')
    p[0] = pai

    if(p[1] == '*'):
        node = MyNode(name='MULTIPLICACAO',type='MULTIPLICACAO',parent=pai)
    else:
        node = MyNode(name='DIVISAO',type='DIVISAO',parent=pai)
    node_simbolo = MyNode(name=p[1],type='SIMBOLO', parent=node)
    p[1] = node

def p_fator(p):
    """fator : ABRE_PARENTESE expressao FECHA_PARENTESE
            | var
            | chamada_funcao
            | numero
    """
    pai = MyNode(name='fator', type="FATOR")
    p[0] = pai
    if len(p) > 2:
        abre_parentese = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
        abre_parentese_simbolo = MyNode(name='(', type='SIMBOLO', parent=abre_parentese)
        p[1] = abre_parentese

        p[2].parent = pai

        fecha_parentese = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
        fecha_parentese_simbolo = MyNode(name=')', type='SIMBOLO', parent=fecha_parentese)
        p[3] = fecha_parentese
    else:
        p[1].parent = pai

def p_numero(p):
    """numero : NUM_INTEIRO
                | NUM_PONTO_FLUTUANTE
                | NUM_NOTACAO_CIENTIFICA
    """
    pai = MyNode(name='numero', type='NUMERO')
    p[0] = pai

    if str(p[1]).find('.') == -1:
        node = MyNode(name='NUM_INTEIRO', type='NUM_INTEIRO', parent=pai)
    elif str(p[1]).find('e') >= 0:
        node = MyNode(name='NUM_NOTACAO_CIENTIFICA', type='NUM_NOTACAO_CIENTIFICA', parent=pai)
    else:
        node = MyNode(name='NUM_PONTO_FLUTUANTE', type='NUM_PONTO_FLUTUANTE', parent=pai)
    node_simbolo = MyNode(name=p[1], type='VALOR', parent=node)
    p[1] = node

def p_chamada_funcao(p):
    """chamada_funcao : ID ABRE_PARENTESE lista_argumentos FECHA_PARENTESE"""
    pai = MyNode(name='chamada_funcao', type='CHAMADA_FUNCAO')
    p[0] = pai
    if len(p) > 2:
        node_id = MyNode(name='ID', type='ID',parent=pai)
        node_id_simbolo = MyNode(name=p[1], type='ID',parent=node_id)
        p[1] = node_id

        abre_parentese = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
        abre_parentese_simbolo = MyNode(name='(', type='SIMBOLO', parent=abre_parentese)
        p[2] = abre_parentese

        p[3].parent = pai

        fecha_parentese = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
        fecha_parentese_simbolo = MyNode(name=')', type='SIMBOLO', parent=fecha_parentese)
        p[4] = fecha_parentese
    else:
        p[1].parent = pai

def p_lista_argumentos(p):
    """lista_argumentos : lista_argumentos VIRGULA expressao
                    | expressao
                    | vazio
    """
    pai = MyNode(name='lista_argumentos', type='LISTA_ARGUMENTOS')
    p[0] = pai

    if len(p) > 2:
        p[1].parent = pai

        virgula = MyNode(name='VIRGULA', type='VIRGULA', parent=pai)
        virgula_simbolo = MyNode(name=p[2], type='SIMBOLO', parent=virgula)
        p[2] = virgula

        p[3].parent = pai
    else:
        p[1].parent = pai

def p_vazio(p):
    """vazio : """

    pai = MyNode(name='vazio', type='VAZIO')
    p[0] = pai

def p_error(p):

    if p:
        global erro
        erro = True
        token = p
        print("\nErro:[{line},{column}]: Erro próximo ao token '{token}'".format(
            line=token.lineno, column=token.lexpos, token=token.value))


def main():
    if(len(argv) < 2):
        print("Erro! Informe o nome do arquivo")
        exit()
    data = open(argv[1])

    source_file = data.read()
    parser.parse(source_file)
    global erro

    try:
        if root and root.children != () and erro == False:
            print("Generating Syntax Tree Graph...")
            # DotExporter(root).to_picture(argv[1] + ".ast.png")
            UniqueDotExporter(root).to_picture(argv[1] + ".unique.ast.png")
            # DotExporter(root).to_dotfile(argv[1] + ".ast.dot")
            UniqueDotExporter(root).to_dotfile(argv[1] + ".unique.ast.dot")
            # print(RenderTree(root, style=AsciiStyle()).by_attr())
            print("Graph was generated.\nOutput file: " + argv[1] + ".ast.png")

            DotExporter(root, graph="graph",
                        nodenamefunc=MyNode.nodenamefunc,
                        nodeattrfunc=lambda node: 'label=%s' % (node.type),
                        edgeattrfunc=MyNode.edgeattrfunc,
                        edgetypefunc=MyNode.edgetypefunc).to_picture(argv[1] + ".ast2.png")

            # DotExporter(root, nodenamefunc=lambda node: node.label).to_picture(argv[1] + ".ast3.png")

        else:
            print('\n--------------------------------\n')
            print('Não foi possível gerar a árvore!')
    except NameError as error:
        print("Erro: " + str(error))
        print('Não foi possível gerar a árvore!')

# Build the parser.
# __file__ = "02-compiladores-analise-sintatica-tppparser.ipynb"
# parser = yacc.yacc(optimize=True, start='programa', debug=True, debuglog=log)
parser = yacc.yacc(method="LALR", optimize=True, start='programa', debug=True,
                   debuglog=log, write_tables=False, tabmodule='tpp_parser_tab')

def retorna_root(filename):
    if(len(filename) == 0):
        print("Erro! Informe o nome do arquivo")
        exit()
    data = open(filename)

    source_file = data.read()
    parser.parse(source_file)

    UniqueDotExporter(root).to_picture(filename + ".png")
    return root

                  
if __name__ == "__main__":
    main()

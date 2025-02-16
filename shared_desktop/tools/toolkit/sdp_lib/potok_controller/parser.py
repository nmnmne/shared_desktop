from rply import ParserGenerator
from .constants import TOKENS


pg = ParserGenerator(
    TOKENS,
    precedence=[
        ("left", ['PLUS']),
        ("left", ['MUL']),
        ("right", ['NOT']),
    ]
)


@pg.production("expression : NUM")
def expression_num(p):
    return int(p[0].value)


@pg.production("expression : L_PAREN expression R_PAREN")
def expression_par(p):
    return p[1]


@pg.production("expression : expression PLUS expression")
@pg.production("expression : expression MUL expression")
def expression_bin_op(p):
    left = p[0]
    op = p[1]
    right = p[2]

    if op.gettokentype() == "PLUS":
        return left + right
    elif op.gettokentype() == "MUL":
        return left * right


@pg.production("expression : NOT expression")
def expression_un_op(p):
    return int(not p[1])






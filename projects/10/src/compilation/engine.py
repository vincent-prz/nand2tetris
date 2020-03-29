from dataclasses import dataclass
from functools import partial
from typing import List, Optional, Union

from tokenizer.jack_tokenizer import JackTokenizer, Token
from compilation.token_parsing_lib import choice, many, sequence, ParseResult


LeafValue = Union[int, str]


@dataclass
class JackAST:
    node_type: str
    children: Union[LeafValue, List]

    # def __repr__(self):
    #     def rec_repr(jast:JackAST, indentation_level: int):
    #         import pudb; pudb.set_trace()
    #         result = 4 * indentation_level * " " + jast.node_type
    #         if isinstance(jast.children, list) and len(jast.children) > 0:
    #             result += "\n" + "\n".join(
    #                 rec_repr(child, indentation_level + 1)
    #                 for child in jast.children
    #             )
    #         else:
    #             result += ": " + str(jast.children)
    #         return result
    #     return rec_repr(self, 0)


def parse_kw_or_symbol(tok: Token, tokens: List[Token]) -> ParseResult:
    assert tok.token_type in ["KEYWORD", "SYMBOL"]
    if len(tokens) == 0 or tokens[0] != tok:
        return None
    return JackAST(tok.token_type, tok.value), tokens[1:]


def parse_identifier(tokens: List[Token]) -> ParseResult:
    if len(tokens) == 0 or tokens[0].token_type != "IDENTIFIER":
        return None
    identifier = tokens[0]
    return JackAST("IDENTIFIER", identifier.value), tokens[1:]


# def flat_list(*elems) -> List:
#     result = []
#     for e in elems:
#         if isinstance(e, list):
#             result += e
#         else:
#             result.append(e)
#     return result


def parse_class(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "class")),
        parse_identifier,
        partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
        many(parse_class_var_dec),
        many(parse_subroutine_dec),
        partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
        aggregator=lambda *jasts: JackAST("CLASS", list(jasts)),
    )(tokens)


def parse_class_var_dec(tokens: List[Token]) -> ParseResult:
    return sequence(
        choice(
            partial(parse_kw_or_symbol, Token("KEYWORD", "static")),
            partial(parse_kw_or_symbol, Token("KEYWORD", "field")),
        ),
        parse_type,
        parse_identifier,
        many(
            sequence(
                partial(parse_kw_or_symbol, Token("SYMBOL", ",")), parse_identifier
            )
        ),
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("CLASS_VAR_DEC", list(jasts)),
    )(tokens)


def parse_subroutine_dec(tokens: List[Token]) -> ParseResult:
    return None


def parse_type(tokens: List[Token]) -> ParseResult:
    return choice(
        partial(parse_kw_or_symbol, Token("KEYWORD", "int")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "boolean")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "char")),
        parse_identifier,
    )(tokens)


class CompilationEngine:
    def __init__(self, file_name):
        self.file_name = file_name
        self._ast = None
        self._tokenizer = JackTokenizer(file_name)

    def compile_class(self):
        pass

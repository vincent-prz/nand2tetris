from dataclasses import dataclass
from functools import partial
from typing import List, Iterable, Optional, Union

from tokenizer.jack_tokenizer import JackTokenizer, Token
from compilation.token_parsing_lib import (
    choice,
    many,
    sequence,
    ParseResult,
    zero_or_one,
)


LeafValue = Union[int, str]


@dataclass
class JackAST:
    node_type: str
    children: Union[LeafValue, List["JackAST"]]

    def __repr__(self):
        def rec_repr(jast: JackAST, indentation_level: int):
            result = 4 * indentation_level * " " + jast.node_type
            if isinstance(jast.children, list) and len(jast.children) > 0:
                result += "\n" + "\n".join(
                    rec_repr(child, indentation_level + 1) for child in jast.children
                )
            else:
                result += ": " + str(jast.children)
            return result

        return rec_repr(self, 0)


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


def flat_list(elems: Iterable) -> List:
    result = []
    need_to_flatten = False
    for e in elems:
        if isinstance(e, list):
            result += e
            need_to_flatten = True
        elif e is not None:
            result.append(e)
    if need_to_flatten:
        return flat_list(result)
    return result


def parse_class(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "class")),
        parse_identifier,
        partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
        many(parse_class_var_dec),
        many(parse_subroutine_dec),
        partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
        aggregator=lambda *jasts: JackAST("CLASS", flat_list(jasts)),
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
                partial(parse_kw_or_symbol, Token("SYMBOL", ",")), parse_identifier,
            )
        ),
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("CLASS_VAR_DEC", flat_list(jasts)),
    )(tokens)


def parse_subroutine_dec(tokens: List[Token]) -> ParseResult:
    return sequence(
        choice(
            partial(parse_kw_or_symbol, Token("KEYWORD", "constructor")),
            partial(parse_kw_or_symbol, Token("KEYWORD", "function")),
            partial(parse_kw_or_symbol, Token("KEYWORD", "method")),
        ),
        choice(partial(parse_kw_or_symbol, Token("KEYWORD", "void")), parse_type),
        parse_identifier,
        partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
        parse_parameter_list,
        partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
        parse_subroutine_body,
        aggregator=lambda *jasts: JackAST("SUBROUTINE_DEC", flat_list(jasts)),
    )(tokens)


def parse_parameter_list(tokens: List[Token]) -> ParseResult:
    return zero_or_one(
        sequence(
            parse_type,
            parse_identifier,
            many(
                sequence(
                    partial(parse_kw_or_symbol, Token("SYMBOL", ",")), parse_identifier
                )
            ),
            aggregator=lambda *jasts: JackAST("PARAMETER_LIST", flat_list(jasts)),
        )
    )(tokens)


def parse_subroutine_body(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
        many(parse_var_dec),
        parse_statements,
        partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
        aggregator=lambda *jasts: JackAST("SUBROUTINE_BODY", flat_list(jasts)),
    )(tokens)


def parse_var_dec(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "var")),
        parse_type,
        parse_identifier,
        many(
            sequence(
                partial(parse_kw_or_symbol, Token("SYMBOL", ",")), parse_identifier
            )
        ),
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("VAR_DEC", flat_list(jasts)),
    )(tokens)


def parse_type(tokens: List[Token]) -> ParseResult:
    return choice(
        partial(parse_kw_or_symbol, Token("KEYWORD", "int")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "boolean")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "char")),
        parse_identifier,
    )(tokens)


def parse_statements(tokens: List[Token]) -> ParseResult:
    return sequence(
        many(parse_statement),
        aggregator=lambda *jasts: JackAST("STATEMENTS", flat_list(jasts)),
    )(tokens)


def parse_statement(tokens: List[Token]) -> ParseResult:
    return choice(
        parse_let_statement,
        parse_if_statement,
        parse_while_statement,
        parse_do_statement,
        parse_return_statement,
    )(tokens)


def parse_let_statement(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "let")),
        parse_identifier,
        zero_or_one(
            sequence(
                partial(parse_kw_or_symbol, Token("SYMBOL", "[")),
                parse_expression,
                partial(parse_kw_or_symbol, Token("SYMBOL", "]")),
            )
        ),
        partial(parse_kw_or_symbol, Token("SYMBOL", "=")),
        parse_expression,
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("LET_STATEMENT", flat_list(jasts)),
    )(tokens)


def parse_if_statement(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "if")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
        parse_expression,
        partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
        parse_statements,
        partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
        zero_or_one(
            sequence(
                partial(parse_kw_or_symbol, Token("KEYWORD", "else")),
                partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
                parse_statements,
                partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
            )
        ),
        aggregator=lambda *jasts: JackAST("IF_STATEMENT", flat_list(jasts)),
    )(tokens)


def parse_while_statement(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "while")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
        parse_expression,
        partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "{")),
        parse_statements,
        partial(parse_kw_or_symbol, Token("SYMBOL", "}")),
        aggregator=lambda *jasts: JackAST("WHILE_STATEMENT", flat_list(jasts)),
    )(tokens)


def parse_do_statement(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "do")),
        parse_subroutine_call,
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("DO_STATEMENT", flat_list(jasts)),
    )(tokens)


def parse_return_statement(tokens: List[Token]) -> ParseResult:
    return sequence(
        partial(parse_kw_or_symbol, Token("KEYWORD", "return")),
        zero_or_one(parse_expression),
        partial(parse_kw_or_symbol, Token("SYMBOL", ";")),
        aggregator=lambda *jasts: JackAST("RETURN_STATEMENT", flat_list(jasts)),
    )(tokens)


def parse_expression(tokens: List[Token]) -> ParseResult:
    return parse_identifier(tokens)


def parse_subroutine_call(tokens: List[Token]) -> ParseResult:
    return sequence(
        choice(
            sequence(
                parse_identifier,
                partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
                parse_expression_list,
                partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
            ),
            sequence(
                parse_identifier,
                partial(parse_kw_or_symbol, Token("SYMBOL", ".")),
                parse_identifier,
                partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
                parse_expression_list,
                partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
            ),
        ),
        aggregator=lambda *jasts: JackAST("SUBROUTINE_CALL", flat_list(jasts)),
    )(tokens)


def parse_expression_list(tokens: List[Token]) -> ParseResult:
    return sequence(
        zero_or_one(
            sequence(
                parse_expression,
                many(
                    sequence(
                        partial(parse_kw_or_symbol, Token("SYMBOL", ",")),
                        parse_expression,
                    )
                ),
            ),
        ),
        aggregator=lambda *jasts: JackAST("EXPRESSION_LIST", flat_list(jasts)),
    )(tokens)


def compilation_engine(file_name: str) -> JackAST:
    tokenizer = JackTokenizer(file_name)
    parse_result = parse_class(tokenizer.get_tokens())
    if parse_result is None:
        raise ValueError(f"Could not parse file")
    jast, remaining_tokens = parse_result
    if len(remaining_tokens):
        raise ValueError(f"Could not parse {remaining_tokens}")
    return jast

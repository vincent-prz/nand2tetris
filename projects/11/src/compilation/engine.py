from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, List, Iterable, NamedTuple, Optional, Union

from symbol_table import kind_to_str, Kind, SymbolTable
from tokenizer.jack_tokenizer import JackTokenizer, Token
from compilation.token_parsing_lib import (
    choice,
    many,
    sequence,
    ParseResult,
    zero_or_one,
)


LeafValue = Union[int, str]


class ScopeAttributes(NamedTuple):
    category: str
    mode: str
    kind: Optional[str] = None
    idx: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"mode": self.mode, "category": self.category}
        if self.kind is not None:
            result["kind"] = self.kind
        if self.idx is not None:
            result["idx"] = self.idx
        return result


@dataclass
class JackAST:
    node_type: str
    children: Union[LeafValue, List["JackAST"]]
    attributes: Optional[ScopeAttributes] = None

    def __repr__(self):
        def rec_repr(jast: JackAST, indentation_level: int):
            result = 4 * indentation_level * " " + jast.node_type
            if isinstance(jast.children, list) and len(jast.children) > 0:
                result += "\n" + "\n".join(
                    rec_repr(child, indentation_level + 1) for child in jast.children
                )
            else:
                result += ": " + str(jast.children)
                if jast.attributes is not None:
                    result += f" | {jast.attributes}"
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


def parse_integer_constant(tokens: List[Token]) -> ParseResult:
    if len(tokens) == 0 or tokens[0].token_type != "INT_CONST":
        return None
    const = tokens[0]
    return JackAST("INTEGER_CONSTANT", const.value), tokens[1:]


def parse_string_constant(tokens: List[Token]) -> ParseResult:
    if len(tokens) == 0 or tokens[0].token_type != "STRING_CONST":
        return None
    const = tokens[0]
    return JackAST("STRING_CONSTANT", const.value), tokens[1:]


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
                    partial(parse_kw_or_symbol, Token("SYMBOL", ",")),
                    parse_type,
                    parse_identifier,
                )
            ),
            aggregator=lambda *jasts: JackAST("PARAMETER_LIST", flat_list(jasts)),
        ),
        default_value=JackAST("PARAMETER_LIST", []),
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
    return sequence(
        parse_term,
        many(sequence(parse_op, parse_term)),
        aggregator=lambda *jasts: JackAST("EXPRESSION", flat_list(jasts)),
    )(tokens)


def parse_term(tokens: List[Token]) -> ParseResult:
    return choice(
        parse_integer_constant,
        parse_string_constant,
        parse_keyword_constant,
        sequence(
            parse_identifier,
            partial(parse_kw_or_symbol, Token("SYMBOL", "[")),
            parse_expression,
            partial(parse_kw_or_symbol, Token("SYMBOL", "]")),
        ),
        parse_subroutine_call,
        parse_identifier,
        sequence(
            partial(parse_kw_or_symbol, Token("SYMBOL", "(")),
            parse_expression,
            partial(parse_kw_or_symbol, Token("SYMBOL", ")")),
        ),
        sequence(parse_unary_op, parse_term),
        callback=lambda jast: JackAST("TERM", flat_list([jast])),
    )(tokens)


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


def parse_op(tokens: List[Token]) -> ParseResult:
    return choice(
        partial(parse_kw_or_symbol, Token("SYMBOL", "+")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "-")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "*")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "/")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "&")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "|")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "<")),
        partial(parse_kw_or_symbol, Token("SYMBOL", ">")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "=")),
    )(tokens)


def parse_unary_op(tokens: List[Token]) -> ParseResult:
    return choice(
        partial(parse_kw_or_symbol, Token("SYMBOL", "-")),
        partial(parse_kw_or_symbol, Token("SYMBOL", "~")),
    )(tokens)


def parse_keyword_constant(tokens: List[Token]) -> ParseResult:
    return choice(
        partial(parse_kw_or_symbol, Token("KEYWORD", "true")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "false")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "null")),
        partial(parse_kw_or_symbol, Token("KEYWORD", "this")),
    )(tokens)


def add_scope_attributes(root: JackAST) -> None:
    symbol_table = SymbolTable()
    assert root.node_type == "CLASS"
    assert isinstance(root.children, list)
    identifier_tree = root.children[1]
    assert identifier_tree.node_type == "IDENTIFIER"
    identifier_tree.attributes = ScopeAttributes(category="class", mode="declaration")

    class_var_decs = [
        child for child in root.children if child.node_type == "CLASS_VAR_DEC"
    ]
    for vd in class_var_decs:
        _add_var_dec_scope_attributes(vd, symbol_table)
    subroutine_decs = [
        child for child in root.children if child.node_type == "SUBROUTINE_DEC"
    ]
    for sd in subroutine_decs:
        symbol_table.start_subroutine()
        _add_subroutine_scope_attributes(sd, symbol_table)


def _add_var_dec_scope_attributes(vd: JackAST, symbol_table: SymbolTable) -> None:
    assert vd.node_type in ["CLASS_VAR_DEC", "VAR_DEC"]
    assert isinstance(vd.children, list)
    kind_str = vd.children[0].children
    typ = vd.children[1].children
    assert isinstance(kind_str, str)
    assert isinstance(typ, str)
    if kind_str == "static":
        kind = Kind.STATIC
    elif kind_str == "field":
        kind = Kind.FIELD
    elif kind_str == "var":
        kind = Kind.VAR
    child_index = 2
    while child_index < len(vd.children):
        # recall: syntax is '<kind> <type> <identifier> <separator>'
        # eg 'static int x, field string s;'
        identifier_tree = vd.children[child_index]
        varname = identifier_tree.children
        assert isinstance(varname, str)
        var_idx = symbol_table.define(varname, typ, kind)
        identifier_tree.attributes = ScopeAttributes(
            category=kind_str, mode="declaration", kind=kind_str, idx=var_idx
        )
        child_index = child_index + 2


def _add_subroutine_scope_attributes(jast: JackAST, symboltable: SymbolTable) -> None:
    assert jast.node_type == "SUBROUTINE_DEC"
    assert isinstance(jast.children, list)
    identifier_tree = jast.children[2]
    assert identifier_tree.node_type == "IDENTIFIER"
    identifier_tree.attributes = ScopeAttributes(
        category="subroutine", mode="declaration"
    )
    _add_parameter_list_scope_attributes(jast.children[4], symboltable)
    _add_subroutine_body_scope_attributes(jast.children[6], symboltable)


def _add_subroutine_body_scope_attributes(
    jast: JackAST, symboltable: SymbolTable
) -> None:
    assert jast.node_type == "SUBROUTINE_BODY"
    assert isinstance(jast.children, list)
    var_decs = [child for child in jast.children if child.node_type == "VAR_DEC"]
    for vd in var_decs:
        _add_var_dec_scope_attributes(vd, symboltable)
    root_statements = [
        child for child in jast.children if child.node_type == "STATEMENTS"
    ][0]
    _add_statements_scope_attributes(root_statements, symboltable)


def _add_parameter_list_scope_attributes(
    jast: JackAST, symboltable: SymbolTable
) -> None:
    assert jast.node_type == "PARAMETER_LIST"
    index = 0
    assert isinstance(jast.children, list)
    while index < len(jast.children):
        typ = jast.children[index].children
        identifier_tree = jast.children[index + 1]
        name = identifier_tree.children
        assert isinstance(name, str)
        assert isinstance(typ, str)
        arg_idx = symboltable.define(name, typ, Kind.ARG)
        identifier_tree.attributes = ScopeAttributes(
            category="arg", mode="declaration", kind="arg", idx=arg_idx
        )
        index = index + 3


def _add_statements_scope_attributes(jast: JackAST, symboltable: SymbolTable) -> None:
    """Recursively add scope attributes to identifiers used in statements."""

    def rec_aux(jast: JackAST, symboltable: SymbolTable) -> None:
        if jast.node_type == "IDENTIFIER":
            assert isinstance(jast.children, str)
            id_name = jast.children
            if (kind := symboltable.kind_of(id_name)) is not None:
                jast.attributes = ScopeAttributes(
                    category=kind_to_str(kind),
                    mode="usage",
                    kind=kind_to_str(kind),
                    idx=symboltable.index_of(id_name),
                )
        else:
            if isinstance(jast.children, (int, str)):
                return
            for child in jast.children:
                rec_aux(child, symboltable)

    assert jast.node_type == "STATEMENTS"
    assert isinstance(jast.children, list)
    for child in jast.children:
        rec_aux(child, symboltable)


def compilation_engine(file_name: str) -> JackAST:
    tokenizer = JackTokenizer(file_name)
    parse_result = parse_class(tokenizer.get_tokens())
    if parse_result is None:
        raise ValueError(f"Could not parse file {file_name}")
    jast, remaining_tokens = parse_result
    if len(remaining_tokens):
        raise ValueError(f"Could not parse {remaining_tokens}")
    add_scope_attributes(jast)
    return jast

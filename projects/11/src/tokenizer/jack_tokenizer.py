from dataclasses import dataclass
from functools import partial
import re
from typing import Union

from tokenizer.parsing_lib import *


KEYWORDS = [
    "class",
    "constructor",
    "function",
    "method",
    "field",
    "static",
    "var",
    "int",
    "char",
    "boolean",
    "void",
    "true",
    "false",
    "null",
    "this",
    "let",
    "do",
    "if",
    "else",
    "while",
    "return",
]
SYMBOLS = [
    "{",
    "}",
    "(",
    ")",
    "[",
    "]",
    ".",
    ",",
    ";",
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "<",
    ">",
    "=",
    "~",
]


@dataclass
class Token:
    token_type: str
    value: Union[int, str]


def parse_keyword(keyword, s):
    if s.startswith(keyword):
        rest = s.lstrip(keyword)
        # this condition is a hack to prevent an identifier such as 'double' to be parsed as two tokens
        # 'do' and 'uble'
        if len(rest) > 0 and not rest[0].isalnum():
            return Token("KEYWORD", keyword), rest


def parse_symbol(symbol, s):
    if s.startswith(symbol):
        return Token("SYMBOL", symbol), s[len(symbol) :]


def parse_int_const(s):
    if (m := re.match(r"([0-9]+)", s)) is not None:
        value = int(m.group(0))
        if value > 32767:
            raise ValueError(f"Cannot parse {value}, upper bound is 32767")
        return Token("INT_CONST", value), s.lstrip(m.group(1))


def parse_string_const(s):
    if (m := re.match(r'"([^\n"]*)"', s)) is not None:
        # need to strip string litteral + surrounding quotes
        # hence we strip m.group(0)
        return Token("STRING_CONST", m.group(1)), s.lstrip(m.group(0))


def parse_identifier(s):
    if (m := re.match(r"([a-zA-Z_]\w*)", s)) is not None:
        return Token("IDENTIFIER", m.group(1)), s.lstrip(m.group(1))


def parse_token(s):
    parsers = []
    for kw in KEYWORDS:
        parsers.append(partial(parse_keyword, kw))

    for symbol in SYMBOLS:
        parsers.append(partial(parse_symbol, symbol))

    parsers.append(parse_int_const)
    parsers.append(parse_string_const)
    parsers.append(parse_identifier)
    return alternative(*parsers)(s)


def parse_regex(regex, s, result=None):
    if (m := re.match(regex, s)) is not None:
        return result, s.lstrip(m.group(0))


def parse_whitespace(s):
    return parse_regex(r"\s*", s, "WHITESPACE")


def parse_comment(s):
    return parse_regex(r"//.*", s, "COMMENT")


def parse_start_multiline_comment(s):
    return parse_regex(r"/\*\*.*", s, "START_ML_COMMENT")


def parse_end_multiline_comment(s):
    return parse_regex(r"\*/", s, "END_ML_COMMENT")


class JackTokenizer:
    def __init__(self, file_name):
        self.file_name = file_name
        self._token_index = -1
        self._tokens = []
        self._consume_file()

    def _consume_file(self):
        with open(self.file_name) as stream:
            multiline_comment = False
            for line_no, line in enumerate(stream.readlines()):
                # remove left and whitespace
                line = line.lstrip().rstrip()
                # handling multiline comments
                if line.startswith("/**"):
                    if not line.endswith("*/"):
                        multiline_comment = True
                    continue
                if line.endswith("*/"):
                    multiline_comment = False
                    continue
                if multiline_comment:
                    continue
                parser = many(
                    chain_and_ignore_right(
                        alternative(parse_comment, parse_token), parse_whitespace
                    )
                )
                parse_result = parser(line)
                tokens = parse_result[0]
                if "COMMENT" in tokens:
                    tokens = tokens[: tokens.index("COMMENT")]
                self._tokens += tokens
                remainder = parse_result[1]
                if not (remainder.isspace() or remainder == ""):
                    raise ValueError(
                        f"Couldn't tokenize {repr(remainder)} at line {line_no + 1} in file {self.file_name}"
                    )

    def has_more_tokens(self):
        return self._token_index < len(self._tokens) - 1

    def advance(self):
        self._token_index += 1

    def token_type(self):
        current_token = self._current_token
        return current_token.token_type

    def keyword(self):
        return self._get_val("KEYWORD")

    def symbol(self):
        return self._get_val("SYMBOL")

    def identifier(self):
        return self._get_val("IDENTIFIER")

    def int_val(self):
        return self._get_val("INT_CONST")

    def string_val(self):
        return self._get_val("STRING_CONST")

    def get_tokens(self):
        result = []
        while self.has_more_tokens():
            self.advance()
            result.append(self._current_token)
        return result

    def _get_val(self, token_type):
        current_token = self._current_token
        function_name = self.type_to_method_map[token_type]
        if current_token.token_type != token_type:
            raise ValueError(
                f"Cannot get {function_name} for {current_token.token_type} token"
            )
        return current_token.value

    @property
    def type_to_method_map(self):
        return {
            "KEYWORD": "keyword",
            "SYMBOL": "symbol",
            "INT_CONST": "int_val",
            "STRING_CONST": "string_val",
            "IDENTIFIER": "identifier",
        }

    @property
    def _current_token(self):
        if self._token_index >= 0:
            return self._tokens[self._token_index]

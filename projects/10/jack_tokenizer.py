from dataclasses import dataclass
import re
from typing import Union


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
        return Token("KEYWORD", keyword), s.lstrip(keyword)


def parse_symbol(symbol, s):
    if s.startswith(symbol):
        return Token("SYMBOL", symbol), s.lstrip(symbol)


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
    for kw in KEYWORDS:
        parse_result = parse_keyword(kw, s)
        if parse_result is not None:
            return parse_result

    for symbol in SYMBOLS:
        parse_result = parse_symbol(symbol, s)
        if parse_result is not None:
            return parse_result

    parse_result = parse_int_const(s) or parse_string_const(s) or parse_identifier(s)
    return parse_result


def parse_whitespace(s):
    if (m := re.match(r"\s*", s)) is not None:
        return None , s.lstrip(m.group(0))

# def many(parser):
#     def func(s):
#         parsed = []
#         parse_result = parser(s)
#         while parse_result is not None:
#             parsed.append(parse_result[0])
#             parse_result = parser(parse_result[1])
# 
#         return result
#     return func





class JackTokenizer:
    def __init__(self, file_name):
        self.file_name = file_name
        self._token_index = -1
        self._tokens = []
        self._consume_file()

    def _consume_file(self):
        multiline_comment = False
        with open(self.file_name) as stream:
            for line_no, line in enumerate(stream.readlines()):
                # remove left whitespace
                line = line.lstrip()
                # handle multiline comments
                # if line.startswith("/**"):
                #     multiline_comment = True
                # elif line.startswith("*/"):
                #     multiline_comment = False
                # if multiline_comment:
                #     continue

                # ignore comment
                str_buffer = line.split("//")[0].split("/**")[0]
                parse_result = parse_token(str_buffer)
                while parse_result is not None:
                    token = parse_result[0]
                    self._tokens.append(token)
                    # remove whitespace
                    parse_result = parse_whitespace(parse_result[1])
                    str_buffer = parse_result[1]
                    parse_result = parse_token(str_buffer)
                if not (str_buffer.isspace() or str_buffer == ""):
                    raise ValueError(
                        f"Couldn't tokenize {repr(str_buffer)} at line {line_no + 1} in file {self.file_name}"
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

    def _get_val(self, token_type):
        current_token = self._current_token
        function_name = self.type_to_method_map[token_type]
        if current_token.token_type != token_type:
            raise ValueError(f"Cannot get {function_name} for {current_token.token_type} token")
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

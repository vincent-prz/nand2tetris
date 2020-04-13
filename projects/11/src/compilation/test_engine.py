import unittest

from tokenizer.jack_tokenizer import Token
from compilation.engine import *


class TestParser(unittest.TestCase):
    def test_empty_class(self):
        tokens = [
            Token(token_type="KEYWORD", value="class"),
            Token(token_type="IDENTIFIER", value="HelloWorld"),
            Token(token_type="SYMBOL", value="{"),
            Token(token_type="SYMBOL", value="}"),
        ]
        result = parse_class(tokens)
        assert result is not None
        parsed, remaining_tokens = result
        assert str(parsed) == (
            "CLASS\n"
            "    KEYWORD: class\n"
            "    IDENTIFIER: HelloWorld\n"
            "    SYMBOL: {\n"
            "    SYMBOL: }"
        )
        assert remaining_tokens == []

    def test_class_with_var_dec(self):
        tokens = [
            Token(token_type="KEYWORD", value="class"),
            Token(token_type="IDENTIFIER", value="HelloWorld"),
            Token(token_type="SYMBOL", value="{"),
            Token(token_type="KEYWORD", value="static"),
            Token(token_type="KEYWORD", value="int"),
            Token(token_type="IDENTIFIER", value="x"),
            Token(token_type="SYMBOL", value=";"),
            Token(token_type="SYMBOL", value="}"),
        ]
        result = parse_class(tokens)
        assert result is not None
        parsed, remaining_tokens = result
        assert str(parsed) == (
            "CLASS\n"
            "    KEYWORD: class\n"
            "    IDENTIFIER: HelloWorld\n"
            "    SYMBOL: {\n"
            "    CLASS_VAR_DEC\n"
            "        KEYWORD: static\n"
            "        KEYWORD: int\n"
            "        IDENTIFIER: x\n"
            "        SYMBOL: ;\n"
            "    SYMBOL: }"
        )
        assert remaining_tokens == []

    def test_class_with_several_var_dec(self):
        tokens = [
            Token(token_type="KEYWORD", value="class"),
            Token(token_type="IDENTIFIER", value="HelloWorld"),
            Token(token_type="SYMBOL", value="{"),
            Token(token_type="KEYWORD", value="static"),
            Token(token_type="KEYWORD", value="int"),
            Token(token_type="IDENTIFIER", value="x"),
            Token(token_type="SYMBOL", value=";"),
            Token(token_type="KEYWORD", value="field"),
            Token(token_type="KEYWORD", value="char"),
            Token(token_type="IDENTIFIER", value="y"),
            Token(token_type="SYMBOL", value=";"),
            Token(token_type="SYMBOL", value="}"),
        ]
        result = parse_class(tokens)
        assert result is not None
        parsed, remaining_tokens = result
        assert str(parsed) == (
            "CLASS\n"
            "    KEYWORD: class\n"
            "    IDENTIFIER: HelloWorld\n"
            "    SYMBOL: {\n"
            "    CLASS_VAR_DEC\n"
            "        KEYWORD: static\n"
            "        KEYWORD: int\n"
            "        IDENTIFIER: x\n"
            "        SYMBOL: ;\n"
            "    CLASS_VAR_DEC\n"
            "        KEYWORD: field\n"
            "        KEYWORD: char\n"
            "        IDENTIFIER: y\n"
            "        SYMBOL: ;\n"
            "    SYMBOL: }"
        )
        assert remaining_tokens == []

    def test_class_with_several_var_dec_inline(self):
        tokens = [
            Token(token_type="KEYWORD", value="class"),
            Token(token_type="IDENTIFIER", value="HelloWorld"),
            Token(token_type="SYMBOL", value="{"),
            Token(token_type="KEYWORD", value="static"),
            Token(token_type="KEYWORD", value="int"),
            Token(token_type="IDENTIFIER", value="x"),
            Token(token_type="SYMBOL", value=","),
            Token(token_type="IDENTIFIER", value="y"),
            Token(token_type="SYMBOL", value=","),
            Token(token_type="IDENTIFIER", value="z"),
            Token(token_type="SYMBOL", value=";"),
            Token(token_type="SYMBOL", value="}"),
        ]
        result = parse_class(tokens)
        assert result is not None
        parsed, remaining_tokens = result
        assert str(parsed) == (
            "CLASS\n"
            "    KEYWORD: class\n"
            "    IDENTIFIER: HelloWorld\n"
            "    SYMBOL: {\n"
            "    CLASS_VAR_DEC\n"
            "        KEYWORD: static\n"
            "        KEYWORD: int\n"
            "        IDENTIFIER: x\n"
            "        SYMBOL: ,\n"
            "        IDENTIFIER: y\n"
            "        SYMBOL: ,\n"
            "        IDENTIFIER: z\n"
            "        SYMBOL: ;\n"
            "    SYMBOL: }"
        )
        assert remaining_tokens == []

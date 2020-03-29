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
        assert parsed == JackAST(
            node_type="CLASS",
            children=[
                JackAST(node_type="KEYWORD", children="class"),
                JackAST(node_type="IDENTIFIER", children="HelloWorld"),
                JackAST(node_type="SYMBOL", children="{"),
                [],
                [],
                JackAST(node_type="SYMBOL", children="}"),
            ],
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
        print(parsed)
        assert parsed == JackAST(
            node_type="CLASS",
            children=[
                JackAST(node_type="KEYWORD", children="class"),
                JackAST(node_type="IDENTIFIER", children="HelloWorld"),
                JackAST(node_type="SYMBOL", children="{"),
                [
                    JackAST(
                        node_type="CLASS_VAR_DEC",
                        children=[
                            JackAST(node_type="KEYWORD", children="static"),
                            JackAST(node_type="KEYWORD", children="int"),
                            JackAST(node_type="IDENTIFIER", children="x"),
                            [],
                            JackAST(node_type="SYMBOL", children=";"),
                        ],
                    )
                ],
                [],
                JackAST(node_type="SYMBOL", children="}"),
            ],
        )

        assert remaining_tokens == []

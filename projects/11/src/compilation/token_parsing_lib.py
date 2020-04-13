from tokenizer.jack_tokenizer import Token

from typing import Any, Callable, List, Optional, Tuple, Union

ParseResult = Optional[Tuple[Any, List[Token]]]
ParserFunc = Callable[[List[Token]], ParseResult]


def sequence(*parser_funcs: ParserFunc, aggregator: Callable = None) -> ParserFunc:
    def parser_func(tokens: List[Token]) -> ParseResult:
        parsed_items = []
        for p in parser_funcs:
            parse_parsed_items = p(tokens)
            if parse_parsed_items is None:
                return None
            parsed, tokens = parse_parsed_items
            parsed_items.append(parsed)
        if aggregator is not None:
            return aggregator(*parsed_items), tokens
        return parsed_items, tokens

    return parser_func


def many(p: ParserFunc) -> ParserFunc:
    def parser_func(tokens: List[Token]) -> ParseResult:
        parsed_items = []
        parse_result = p(tokens)
        while parse_result is not None:
            parsed, tokens = parse_result
            parsed_items.append(parsed)
            parse_result = p(tokens)
        return parsed_items, tokens

    return parser_func


def zero_or_one(p: ParserFunc, default_value: Any = None) -> ParserFunc:
    def parser_func(tokens: List[Token]) -> ParseResult:
        parse_result = p(tokens)
        if parse_result is not None:
            return parse_result
        return default_value, tokens

    return parser_func


def choice(*parser_funcs: ParserFunc, callback: Callable = None) -> ParserFunc:
    def parser_func(tokens: List[Token]) -> ParseResult:
        for p in parser_funcs:
            parse_result = p(tokens)
            if parse_result is not None:
                if callback is not None:
                    parsed_item, tokens = parse_result
                    return callback(parsed_item), tokens
                return parse_result
        return None

    return parser_func

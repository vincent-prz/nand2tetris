def many(parser):
    def new_parser(s):
        parsed = []
        parse_result = parser(s)
        while parse_result is not None:
            parsed.append(parse_result[0])
            s = parse_result[1]
            parse_result = parser(s)

        return parsed, s

    return new_parser


def alternative(*parsers):
    def new_parser(s):
        for p in parsers:
            if (parse_result := p(s)) is not None:
                return parse_result

    return new_parser


def chain_and_ignore_right(parser_left, parser_right):
    def new_parser(s):
        parse_result = parser_left(s)
        if parse_result is None:
            return None
        parsed, s = parse_result

        parse_result = parser_right(s)
        if parse_result is None:
            return None
        _, s = parse_result
        return parsed, s

    return new_parser

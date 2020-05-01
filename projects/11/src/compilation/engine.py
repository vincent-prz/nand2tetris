from tokenizer.jack_tokenizer import JackTokenizer, Token
from jack_ast import add_scope_attributes, JackAST, parse_class 


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

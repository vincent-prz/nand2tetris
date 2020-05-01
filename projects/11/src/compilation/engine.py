from tokenizer.jack_tokenizer import JackTokenizer, Token
from jack_ast import add_scope_attributes, JackAST, parse_class
from vm_writer import write_vm_code


def compilation_engine(file_name: str, debug: bool = False) -> str:
    tokenizer = JackTokenizer(file_name)
    parse_result = parse_class(tokenizer.get_tokens())
    if parse_result is None:
        raise ValueError(f"Could not parse file {file_name}")
    jast, remaining_tokens = parse_result
    if len(remaining_tokens):
        raise ValueError(f"Could not parse {remaining_tokens}")
    add_scope_attributes(jast)
    vm_code = write_vm_code(jast)
    if debug:
        print("===AST===")
        print(jast)
        print("===VM CODE===")
        print(vm_code)
    return vm_code

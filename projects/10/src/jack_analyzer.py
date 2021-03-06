import os
import argparse
import re
import xml.etree.cElementTree as ET

from tokenizer.jack_tokenizer import JackTokenizer
from compilation import compilation_engine


def get_output_filename(output_folder, input_filename):
    output_basename = os.path.basename(input_filename).split(".")[0] + ".xml"
    return os.path.join(output_folder, output_basename)


def etree_toprettystring(tree):
    str_buffer = f"<{tree.tag}>"
    if len(tree) == 0:
        str_buffer += (
            tree.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
    else:
        str_buffer += (
            "\n" + "\n".join(etree_toprettystring(elem) for elem in tree) + "\n"
        )
    str_buffer += f"</{tree.tag}>"
    return str_buffer


def tokenizer_to_xml(tokenizer):
    root = ET.Element("tokens")
    while tokenizer.has_more_tokens():
        tokenizer.advance()
        if tokenizer.token_type() == "KEYWORD":
            keyword = tokenizer.keyword()
            ET.SubElement(root, "keyword").text = f" {keyword} "
        elif tokenizer.token_type() == "SYMBOL":
            symbol = tokenizer.symbol()
            ET.SubElement(root, "symbol").text = f" {symbol} "
        elif tokenizer.token_type() == "INT_CONST":
            value = tokenizer.int_val()
            ET.SubElement(root, "integerConstant").text = f" {value} "
        elif tokenizer.token_type() == "STRING_CONST":
            value = tokenizer.string_val()
            ET.SubElement(root, "stringConstant").text = f" {value} "
        elif tokenizer.token_type() == "IDENTIFIER":
            value = tokenizer.identifier()
            ET.SubElement(root, "identifier").text = f" {value} "
    return root


def jack_ast_to_xml(jast, parent=None):
    def capital_to_snake_case(s):
        parts = s.lower().split("_")
        result = parts[0]
        for p in parts[1:]:
            result += p[0].upper()
            for c in p[1:]:
                result += c
        return result

    tag = capital_to_snake_case(jast.node_type)
    if parent is None:
        tree = ET.Element(tag)
    else:
        tree = ET.SubElement(parent, tag)
    if isinstance(jast.children, list):
        for c in jast.children:
            jack_ast_to_xml(c, tree)
    else:
        tree.text = f" {jast.children} "
    return tree


def etree_toprettystring_full(tree, level=0):
    identation = level * 2 * " "
    str_buffer = f"{identation}<{tree.tag}>"
    if len(tree) == 0:
        if tree.text is not None:
            str_buffer += (
                tree.text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            ) + f"</{tree.tag}>"
        else:
            str_buffer += f"\n{identation}</{tree.tag}>"
    else:
        str_buffer += (
            "\n"
            + "\n".join(etree_toprettystring_full(elem, level + 1) for elem in tree)
            + "\n"
        ) + f"{identation}</{tree.tag}>"
    return str_buffer


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Perform syntactic analysis of Jack files."
    )
    argparser.add_argument(
        "input_arg", metavar="input", type=str, help="File or folder to analyze."
    )
    argparser.add_argument(
        "--tokenize-only",
        dest="tokenize_only",
        action="store_true",
        help="Perform only the tokenization, and not the parsing.",
    )
    argparser.add_argument(
        "--output-folder", dest="output_folder", help="Specify the output folder.",
    )
    args = argparser.parse_args()
    input_arg = args.input_arg
    if os.path.isfile(input_arg):
        file_names = [input_arg]
        output_folder = args.output_folder or os.path.dirname(input_arg)
    else:
        file_names = []
        for fn in os.listdir(input_arg):
            if fn.endswith(".jack"):
                file_names.append(fn)
        output_folder = args.output_folder or args.input_arg

    tokenize_only = args.tokenize_only
    for fn in file_names:
        if tokenize_only:
            tkz = JackTokenizer(fn)
            root = tokenizer_to_xml(tkz)
            output = etree_toprettystring(root)
        else:
            jast = compilation_engine(fn)
            output = etree_toprettystring_full(jack_ast_to_xml(jast))
            # ET.dump(jack_ast_to_xml(jast))

        output_filename = get_output_filename(output_folder, fn)
        with open(output_filename, "w") as output_stream:
            output_stream.write(output)
            output_stream.write("\n")

import os
import argparse
import re
import xml.etree.cElementTree as ET

from jack_tokenizer import JackTokenizer


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
        tokenizers = [JackTokenizer(input_arg)]
        output_folder = args.output_folder or os.path.dirname(input_arg)

    elif os.path.isfolder(input_arg):
        tokenizers = []
        for fn in os.listdir(input_arg):
            if fn.endswith(".jack"):
                tokenizers.append(JackTokenizer(input_arg))
        output_folder = args.output_folder or args.input_arg

    for tkz in tokenizers:
        root = ET.Element("tokens")
        while tkz.has_more_tokens():
            tkz.advance()
            if tkz.token_type() == "KEYWORD":
                keyword = tkz.keyword()
                ET.SubElement(root, "keyword").text = f" {keyword} "
            elif tkz.token_type() == "SYMBOL":
                symbol = tkz.symbol()
                ET.SubElement(root, "symbol").text = f" {symbol} "
            elif tkz.token_type() == "INT_CONST":
                value = tkz.int_val()
                ET.SubElement(root, "integerConstant").text = f" {value} "
            elif tkz.token_type() == "STRING_CONST":
                value = tkz.string_val()
                ET.SubElement(root, "stringConstant").text = f" {value} "
            elif tkz.token_type() == "IDENTIFIER":
                value = tkz.identifier()
                ET.SubElement(root, "identifier").text = f" {value} "
        output = etree_toprettystring(root)
        output_filename = get_output_filename(output_folder, tkz.file_name)
        with open(output_filename, "w") as output_stream:
            output_stream.write(output)
            output_stream.write("\n")

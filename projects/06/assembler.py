import sys


class Parser:
    def __init__(self, stream):
        self._cmds = []
        for line in stream.readlines():
            if line.isspace():
                continue
            line = line.strip()
            if line.startswith("//"):
                continue
            self._cmds.append(self._clean_cmd(line))
        self._cmd_index = -1

    def _clean_cmd(self, line):
        """Remove whitespace and inline comments. """
        return "".join([c for c in line if not c.isspace()]).split("//")[0]

    def has_more_commands(self):
        return self._cmd_index < len(self._cmds) - 1

    def advance(self):
        self._cmd_index += 1

    def command_type(self):
        current_command = self.current_command
        if current_command.startswith("@"):
            return "A_COMMAND"
        elif current_command.startswith("("):
            return "L_COMMAND"
        return "C_COMMAND"

    def symbol(self):
        command_type = self.command_type()
        if command_type == "C_COMMAND":
            raise ValueError("Cannot get symbol of C_COMMAND")
        current_command = self.current_command
        if command_type == "A_COMMAND":
            return current_command[1:]
        return current_command[1 : len(current_command) - 1]

    def dest(self):
        command_type = self.command_type()
        if command_type != "C_COMMAND":
            raise ValueError(f"Cannot get dest of {command_type}")
        current_command = self.current_command
        if "=" in current_command:
            return current_command.split("=")[0]

    def comp(self):
        command_type = self.command_type()
        if command_type != "C_COMMAND":
            raise ValueError(f"Cannot get comp of {command_type}")
        current_command = self.current_command
        if "=" in current_command:
            return current_command.split("=")[1].split(";")[0]
        return current_command.split(";")[0]

    def jump(self):
        command_type = self.command_type()
        if command_type != "C_COMMAND":
            raise ValueError(f"Cannot get dest of {command_type}")
        current_command = self.current_command
        if ";" in current_command:
            return current_command.split(";")[1]

    @property
    def current_command(self):
        if self._cmd_index >= 0:
            return self._cmds[self._cmd_index]

    def reset(self):
        self._cmd_index = -1


def encode_dest(dest):
    if dest is None:
        return [0, 0, 0]
    result = [0, 0, 0]
    if "A" in dest:
        result[0] = 1
    if "D" in dest:
        result[1] = 1
    if "M" in dest:
        result[2] = 1
    return result


def encode_comp(comp):
    if comp == "0":
        return [0, 1, 0, 1, 0, 1, 0]
    if comp == "1":
        return [0, 1, 1, 1, 1, 1, 1]
    if comp == "-1":
        return [0, 1, 1, 1, 0, 1, 0]
    if comp == "D":
        return [0, 0, 0, 1, 1, 0, 0]
    if comp == "A":
        return [0, 1, 1, 0, 0, 0, 0]
    if comp == "M":
        return [1, 1, 1, 0, 0, 0, 0]
    if comp == "!D":
        return [0, 0, 0, 1, 1, 0, 1]
    if comp == "!A":
        return [0, 1, 1, 0, 0, 0, 1]
    if comp == "!M":
        return [1, 1, 1, 0, 0, 0, 1]
    if comp == "-D":
        return [0, 0, 0, 1, 1, 1, 1]
    if comp == "-A":
        return [0, 1, 1, 0, 0, 1, 1]
    if comp == "-M":
        return [1, 1, 1, 0, 0, 1, 1]
    if comp == "D+1":
        return [0, 0, 1, 1, 1, 1, 1]
    if comp == "A+1":
        return [0, 1, 1, 0, 1, 1, 1]
    if comp == "M+1":
        return [1, 1, 1, 0, 1, 1, 1]
    if comp == "D-1":
        return [0, 0, 0, 1, 1, 1, 0]
    if comp == "A-1":
        return [0, 1, 1, 0, 0, 1, 0]
    if comp == "M-1":
        return [1, 1, 1, 0, 0, 1, 0]
    if comp == "D+A":
        return [0, 0, 0, 0, 0, 1, 0]
    if comp == "D+M":
        return [1, 0, 0, 0, 0, 1, 0]
    if comp == "D-A":
        return [0, 0, 1, 0, 0, 1, 1]
    if comp == "D-M":
        return [1, 0, 1, 0, 0, 1, 1]
    if comp == "A-D":
        return [0, 0, 0, 0, 1, 1, 1]
    if comp == "M-D":
        return [1, 0, 0, 0, 1, 1, 1]
    if comp == "D&A":
        return [0, 0, 0, 0, 0, 0, 0]
    if comp == "D&M":
        return [1, 0, 0, 0, 0, 0, 0]
    if comp == "D|A":
        return [0, 0, 1, 0, 1, 0, 1]
    if comp == "D|M":
        return [1, 0, 1, 0, 1, 0, 1]
    raise ValueError(f"Unknown comp value: {comp}")


def encode_jump(jump):
    if jump is None or jump == "":
        return [0, 0, 0]
    if jump == "JGT":
        return [0, 0, 1]
    if jump == "JEQ":
        return [0, 1, 0]
    if jump == "JGE":
        return [0, 1, 1]
    if jump == "JLT":
        return [1, 0, 0]
    if jump == "JNE":
        return [1, 0, 1]
    if jump == "JLE":
        return [1, 1, 0]
    if jump == "JMP":
        return [1, 1, 1]


def to_15_bits(n):
    bits = []
    for _ in range(15):
        bits.append(n % 2)
        n = n // 2
    return bits[::-1]


class SymbolTable:
    def __init__(self):
        self._data = {
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7,
            "R8": 8,
            "R9": 9,
            "R10": 10,
            "R11": 11,
            "R12": 12,
            "R13": 13,
            "R14": 14,
            "R15": 15,
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4,
            "SCREEN": 16384,
            "KBD": 24576,
        }
        self._ram_index = 16

    def add_entry(self, symbol, address=None):
        if symbol in self._data:
            raise ValueError(f"symbol {symbol} already in table")
        if address is None:
            address = self._ram_index
            self._ram_index += 1
        self._data[symbol] = address
        return address

    def contains(self, symbol):
        return symbol in self._data

    def get_address(self, symbol):
        return self._data[symbol]


def first_pass(parser, symbol_table):
    rom_index = 0
    while parser.has_more_commands():
        parser.advance()
        if parser.command_type() == "L_COMMAND":
            symbol = parser.symbol()
            if symbol_table.contains(symbol):
                raise ValueError(f"symbol {symbol} defined multiple times")
            symbol_table.add_entry(symbol, rom_index)
        else:
            rom_index += 1


def second_pass(parser, symbol_table):
    translated_lines = []
    while parser.has_more_commands():
        parser.advance()
        current_translated_line = []
        if parser.command_type() == "A_COMMAND":
            symbol = parser.symbol()
            if symbol.isdigit():
                address = int(symbol)
            elif symbol_table.contains(symbol):
                address = symbol_table.get_address(symbol)
            else:
                address = symbol_table.add_entry(symbol)
            current_translated_line = [0] + to_15_bits(address)
        elif parser.command_type() == "C_COMMAND":
            encoded_comp = encode_comp(parser.comp())
            encoded_dest = encode_dest(parser.dest())
            encoded_jump = encode_jump(parser.jump())
            current_translated_line = (
                [1, 1, 1] + encoded_comp + encoded_dest + encoded_jump
            )
        else:
            continue
        translated_lines.append(current_translated_line)
    return translated_lines


if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename) as stream:
        parser = Parser(stream)
    symbol_table = SymbolTable()
    first_pass(parser, symbol_table)
    parser.reset()
    translated_lines = second_pass(parser, symbol_table)

    if len(sys.argv) > 2:
        output_filename = sys.argv[2]
    else:
        output_filename = filename.split(".")[0] + ".hack"
    with open(output_filename, "w") as output_stream:
        for tl in translated_lines:
            output_stream.write("".join(str(b) for b in tl) + "\n")

import sys


class Parser:
    def __init__(self, stream):
        self._stream = stream
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
        return "".join([c for c in line if not c.isspace()])

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


if __name__ == "__main__":
    filename = sys.argv[1]
    translated_lines = []
    with open(filename) as stream:
        parser = Parser(stream)
        while parser.has_more_commands():
            parser.advance()
            current_translated_line = []
            if parser.command_type() == "A_COMMAND":
                symbol = parser.symbol()
                current_translated_line = [0] + to_15_bits(int(symbol))
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

    output_filename = filename.split(".")[0] + "1.hack"
    with open(output_filename, "w") as output_stream:
        for tl in translated_lines:
            output_stream.write("".join(str(b) for b in tl) + "\n")

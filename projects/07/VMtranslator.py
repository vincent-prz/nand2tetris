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
        """Remove inline comments. """
        return line.split("//")[0]

    def has_more_commands(self):
        return self._cmd_index < len(self._cmds) - 1

    def advance(self):
        self._cmd_index += 1

    def command_type(self):
        current_cmd = self.current_command
        if current_cmd.startswith("push"):
            return "C_PUSH"
        if current_cmd.startswith("pop"):
            return "C_POP"
        return "C_ARITHMETIC"

    def arg1(self):
        cmd_type = self.command_type()
        args = self.current_command.split()
        if cmd_type in ["C_PUSH", "C_POP"]:
            return args[1]
        return self.current_command

    def arg2(self):
        cmd_type = self.command_type()
        args = self.current_command.split()
        if cmd_type in ["C_PUSH", "C_POP"]:
            return int(args[2])
        raise ValueError(f"unexpected call to arg2 for a {cmd_type} command.")

    @property
    def current_command(self):
        if self._cmd_index >= 0:
            return self._cmds[self._cmd_index]


class StringBuilder:

    def __init__(self, s=None):
        if s is not None:
            self._strs = [s]
        else:
            self._strs = []

    def __add__(self, s):
        self._strs.append(s)
        return self

    def build(self):
        return "\n".join(self._strs) + "\n"

class CodeWriter:
    # NOTE: CodeWriter is owning the stream, and this is responsible for closing it
    def __init__(self, stream):
        self._stream = stream
        self._filename = None
        self._nb_cmd = 0

    def set_filename(self, filename):
        self._filename = filename

    def write_arithmetic(self, cmd):
        sb = None
        if cmd == "add":
            sb = self._build_binary_op(cmd, "+")
        elif cmd == "sub":
            sb = self._build_binary_op(cmd, "-")
        elif cmd == "and":
            sb = self._build_binary_op(cmd, "&")
        elif cmd == "or":
            sb = self._build_binary_op(cmd, "|")
        elif cmd == "neg":
            sb = self._build_unary_op(cmd, "-")
        elif cmd == "not":
            sb = self._build_unary_op(cmd, "!")
        elif cmd == "eq":
            sb = self._build_compare_op(cmd, "JEQ")
        elif cmd == "lt":
            sb = self._build_compare_op(cmd, "JLT")
        elif cmd == "gt":
            sb = self._build_compare_op(cmd, "JGT")
        else:
            raise ValueError(f"unrecognized arithmetic operation: {cmd}")

        self._stream.write(sb.build())
        self._nb_cmd += 1

    def _build_binary_op(self, cmd, op):
        sb = StringBuilder(f"// {cmd}")
        sb += "@SP"
        sb += "A=M-1"
        sb += "D=M"
        sb += "A=A-1"
        sb += f"M=M{op}D"
        sb += "@SP"
        sb += "M=M-1"
        return sb

    def _build_unary_op(self, cmd, op):
        sb = StringBuilder(f"// {cmd}")
        sb += "@SP"
        sb += "A=M-1"
        sb += f"M={op}M"
        return sb

    def _build_compare_op(self, cmd, jmp):
        sb = StringBuilder(f"// {cmd}")
        sb += "@SP"
        sb += "A=M-1"
        sb += "D=M"
        sb += "A=A-1"
        sb += "D=M-D"
        sb += f"@SET_TRUE_{self._nb_cmd}"
        sb += f"D;{jmp}"
        sb += "@SP"
        sb += "A=M-1"
        sb += "A=A-1"
        sb += "M=0"
        sb += f"@END_SET_TRUE_{self._nb_cmd}"
        sb += f"0;JMP"
        sb += f"(SET_TRUE_{self._nb_cmd})"
        sb += "@SP"
        sb += "A=M-1"
        sb += "A=A-1"
        sb += "M=-1"
        sb += f"(END_SET_TRUE_{self._nb_cmd})"
        sb += "@SP"
        sb += "M=M-1"
        return sb


    def write_push_pop(self, cmd, segment, index):
        if segment != "constant":
            return
        sb = StringBuilder(f"// {cmd} {segment} {index}")
        if cmd == "C_PUSH":
            sb += f"@{index}"
            sb += "D=A"
            sb += "@SP"
            sb += "A=M"
            sb += "M=D"
            sb += "@SP"
            sb += "M=M+1"

        self._stream.write(sb.build())
        self._nb_cmd += 1

    def close(self):
        self._stream.close()


if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename) as input_file:
        parser = Parser(input_file)
    output_filename = filename.split(".")[0] + ".asm"
    output_file = open(output_filename, "w")
    code_writer = CodeWriter(output_file)
    while parser.has_more_commands():
        parser.advance()
        cmd_type = parser.command_type()
        if cmd_type == "C_ARITHMETIC":
            code_writer.write_arithmetic(parser.current_command)
        elif cmd_type == "C_PUSH":
            segment = parser.arg1()
            index = parser.arg2()
            code_writer.write_push_pop(cmd_type, segment, index)

    code_writer.close()

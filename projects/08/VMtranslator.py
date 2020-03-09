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
        if current_cmd.startswith("label"):
            return "C_LABEL"
        if current_cmd.startswith("goto"):
            return "C_GOTO"
        if current_cmd.startswith("if-goto"):
            return "C_IF"
        return "C_ARITHMETIC"

    def arg1(self):
        cmd_type = self.command_type()
        if cmd_type == "C_ARITHMETIC":
            return self.current_command

        args = self.current_command.split()
        return args[1]

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


class CodeWriter:
    # NOTE: CodeWriter is owning the stream, and this is responsible for closing it
    def __init__(self, stream):
        self._stream = stream
        self._filename = None
        self._asm_cmd_index = 0
        self._current_function = "Sys.init"

    def set_filename(self, filename):
        self._filename = filename

    def write_arithmetic(self, cmd):
        if cmd == "add":
            self._write_binary_op("+")
        elif cmd == "sub":
            self._write_binary_op("-")
        elif cmd == "and":
            self._write_binary_op("&")
        elif cmd == "or":
            self._write_binary_op("|")
        elif cmd == "neg":
            self._write_unary_op("-")
        elif cmd == "not":
            self._write_unary_op("!")
        elif cmd == "eq":
            self._write_compare_op("JEQ")
        elif cmd == "lt":
            self._write_compare_op("JLT")
        elif cmd == "gt":
            self._write_compare_op("JGT")
        else:
            raise ValueError(f"unrecognized arithmetic operation: {cmd}")

    def _write_binary_op(self, op):
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("A=A-1")
        self._write_asm_cmd(f"M=M{op}D")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M-1")

    def _write_unary_op(self, op):
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd(f"M={op}M")

    def _write_compare_op(self, jmp):
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("A=A-1")
        self._write_asm_cmd("D=M-D")
        self._write_asm_cmd(f"@{self._asm_cmd_index + 8}")
        self._write_asm_cmd(f"D;{jmp}")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd("A=A-1")
        self._write_asm_cmd("M=0")
        self._write_asm_cmd(f"@{self._asm_cmd_index + 6}")
        self._write_asm_cmd("0;JMP")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd("A=A-1")
        self._write_asm_cmd("M=-1")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M-1")

    def write_push_pop(self, cmd, segment, index):
        if cmd == "C_PUSH":
            self._write_push(segment, index)
        elif cmd == "C_POP":
            self._write_pop(segment, index)

    def _get_segment_base(self, segment, index):
        if segment == "local":
            return "LCL"
        elif segment == "argument":
            return "ARG"
        elif segment == "this":
            return "THIS"
        elif segment == "that":
            return "THAT"
        elif segment == "pointer":
            return "R3"
        elif segment == "temp":
            return "R5"
        elif segment == "static":
            return f"{self._filename}.{index}"
        raise ValueError(f"unknown segment {segment}")

    def _write_push(self, segment, index):
        if segment == "constant":
            self._write_asm_cmd(f"@{index}")
            self._write_asm_cmd("D=A")
            self._write_asm_cmd("@SP")
            self._write_asm_cmd("A=M")
            self._write_asm_cmd("M=D")
            self._write_asm_cmd("@SP")
            self._write_asm_cmd("M=M+1")
            return

        base = self._get_segment_base(segment, index)
        # put in D the content of the address we want to push from
        self._write_asm_cmd(f"@{base}")
        if segment in ["pointer", "temp"]:
            self._write_asm_cmd("D=A")
        else:
            self._write_asm_cmd("D=M")
        if segment != "static":
            self._write_asm_cmd(f"@{index}")
            self._write_asm_cmd("A=A+D")
            self._write_asm_cmd("D=M")

        # push D to the top of the stack
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("M=D")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M+1")

    def _write_pop(self, segment, index):
        if segment == "constant":
            raise ValueError("cannot pop to constant segment")

        base = self._get_segment_base(segment, index)
        # put in D the address we want to pop to
        self._write_asm_cmd(f"@{base}")
        if segment in ["pointer", "temp", "static"]:
            self._write_asm_cmd("D=A")
        else:
            self._write_asm_cmd("D=M")
        if segment != "static":
            self._write_asm_cmd(f"@{index}")
            self._write_asm_cmd("D=A+D")

        # pop to target address
        # use R13 to store the target address.
        # this is allowed as per the standard VM mapping.
        self._write_asm_cmd("@R13")
        self._write_asm_cmd("M=D")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M-1")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("@R13")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("M=D")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M-1")

    def write_label(self, label):
        self._write_asm_cmd(f"({self._build_asm_label(label)})")

    def write_goto(self, label):
        self._write_asm_cmd(f"@{self._build_asm_label(label)}")
        self._write_asm_cmd("0;JMP")

    def write_if(self, label):
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M-1")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd(f"@{self._build_asm_label(label)}")
        self._write_asm_cmd("D;JNE")

    def _write_asm_cmd(self, cmd):
        self._stream.write(f"{cmd}\n")

    def _build_asm_label(self, label):
        return f"{self._current_function}${label}"

    def close(self):
        self._stream.close()


if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename) as input_file:
        parser = Parser(input_file)
    filename_prefix = filename.split(".")[0]
    output_filename = filename_prefix + ".asm"
    output_file = open(output_filename, "w")
    code_writer = CodeWriter(output_file)
    # TODO: use path lib
    code_writer.set_filename(filename_prefix.split("/")[-1])
    while parser.has_more_commands():
        parser.advance()
        cmd_type = parser.command_type()
        if cmd_type == "C_ARITHMETIC":
            code_writer.write_arithmetic(parser.current_command)
        elif cmd_type in ["C_PUSH", "C_POP"]:
            segment = parser.arg1()
            index = parser.arg2()
            code_writer.write_push_pop(cmd_type, segment, index)
        elif cmd_type == "C_LABEL":
            label = parser.arg1()
            code_writer.write_label(label)
        elif cmd_type == "C_GOTO":
            label = parser.arg1()
            code_writer.write_goto(label)
        elif cmd_type == "C_IF":
            label = parser.arg1()
            code_writer.write_if(label)

    code_writer.close()

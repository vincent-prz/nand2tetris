import os
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
        return line.split("//")[0].strip()

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
        if current_cmd.startswith("call"):
            return "C_CALL"
        if current_cmd.startswith("function"):
            return "C_FUNCTION"
        if current_cmd == "return":
            return "C_RETURN"
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
        if cmd_type in ["C_PUSH", "C_POP", "C_FUNCTION", "C_CALL"]:
            return int(args[2])
        raise ValueError(f"unexpected call to arg2 for a {cmd_type} command.")

    @property
    def current_command(self):
        if self._cmd_index >= 0:
            return self._cmds[self._cmd_index]


class CodeWriter:
    # NOTE: CodeWriter is owning the stream, and thus is responsible for closing it
    def __init__(self, stream):
        self._stream = stream
        self._filename = None
        self._asm_cmd_index = 0
        self._current_function_name = None

    def set_filename(self, filename):
        self._filename = filename

    def write_bootstrap_code(self):
        # SP = 256
        self._write_asm_cmd("@256")
        self._write_asm_cmd("D=A")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=D")
        # call Sys.init
        self.write_call("Sys.init", 0)
        # infinite loop
        self._write_asm_cmd(f"@{self._asm_cmd_index}")
        self._write_asm_cmd("0;JMP")

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
        self._write_asm_cmd(f"({self._build_asm_function_label(label)})")

    def write_goto(self, label):
        self._write_asm_cmd(f"@{self._build_asm_function_label(label)}")
        self._write_asm_cmd("0;JMP")

    def write_if(self, label):
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M-1")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd(f"@{self._build_asm_function_label(label)}")
        self._write_asm_cmd("D;JNE")

    def write_call(self, name, nb_args):
        # push return address
        return_label = f"RET_{self._asm_cmd_index}"
        self._write_asm_cmd(f"@{return_label}")
        self._write_asm_cmd("D=A")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("M=D")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=M+1")

        # push memory segments
        def _save_segment(segment):
            self._write_asm_cmd(f"@{segment}")
            self._write_asm_cmd("D=M")
            self._write_asm_cmd("@SP")
            self._write_asm_cmd("A=M")
            self._write_asm_cmd("M=D")
            self._write_asm_cmd("@SP")
            self._write_asm_cmd("M=M+1")

        _save_segment("LCL")
        _save_segment("ARG")
        _save_segment("THIS")
        _save_segment("THAT")
        # ARG = SP - n - 5
        self._write_asm_cmd(f"@{nb_args}")
        self._write_asm_cmd("D=A")
        self._write_asm_cmd("@5")
        self._write_asm_cmd("D=D+A")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("D=M-D")
        self._write_asm_cmd("@ARG")
        self._write_asm_cmd("M=D")
        # LCL = SP
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("@LCL")
        self._write_asm_cmd("M=D")

        # jump to function
        self._write_asm_cmd(f"@{name}")
        self._write_asm_cmd("0;JMP")
        # set return label
        self._write_asm_cmd(f"({return_label})")

    def write_function(self, name, nb_locals):
        self._current_function_name = name
        self._write_asm_cmd(f"({name})")
        for _ in range(nb_locals):
            self._write_push("constant", 0)

    def write_return(self):
        # FRAME = LCL (stored in R14)
        self._write_asm_cmd("@LCL")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("@R14")
        self._write_asm_cmd("M=D")
        # RET = *(FRAME - 5) (stored in R15)
        self._write_asm_cmd("@5")
        self._write_asm_cmd("D=A")
        self._write_asm_cmd("@R14")
        self._write_asm_cmd("D=M-D")
        self._write_asm_cmd("A=D")
        self._write_asm_cmd("D=M")
        self._write_asm_cmd("@R15")
        self._write_asm_cmd("M=D")
        # *ARG = POP()
        self._write_pop("argument", 0)
        # SP = ARG + 1
        self._write_asm_cmd("@ARG")
        self._write_asm_cmd("D=M+1")
        self._write_asm_cmd("@SP")
        self._write_asm_cmd("M=D")

        # restore segments from caller
        def _restore_from_caller(segment):
            self._write_asm_cmd("@R14")
            self._write_asm_cmd("M=M-1")
            self._write_asm_cmd("A=M")
            self._write_asm_cmd("D=M")
            self._write_asm_cmd(f"@{segment}")
            self._write_asm_cmd("M=D")

        _restore_from_caller("THAT")
        _restore_from_caller("THIS")
        _restore_from_caller("ARG")
        _restore_from_caller("LCL")
        # GOTO RET
        self._write_asm_cmd("@R15")
        self._write_asm_cmd("A=M")
        self._write_asm_cmd("0;JMP")

    def _write_asm_cmd(self, cmd):
        self._stream.write(f"{cmd}\n")
        # labels will not be removed by assembler, so we must not count them
        if not cmd.startswith("("):
            self._asm_cmd_index += 1

    def _build_asm_function_label(self, label):
        return f"{self._current_function_name}${label}"

    def write_comment(self, comment):
        self._stream.write(f"// {comment}\n")

    def close(self):
        self._stream.close()


if __name__ == "__main__":
    arg = sys.argv[1]
    if os.path.isfile(arg):
        filenames = [arg]
        output_filename = arg.split(".")[0] + ".asm"
    elif os.path.isdir(arg):
        filenames = [
            os.path.join(arg, fn) for fn in os.listdir(arg) if fn.endswith(".vm")
        ]
        output_filename = os.path.join(
            arg, os.path.split(arg.strip(os.sep))[1] + ".asm"
        )
    else:
        print("file not found")
        sys.exit(1)
    if len(filenames) == 0:
        print("no vm file found in this folder")
        sys.exit(1)

    parsers = []
    for fn in filenames:
        with open(fn) as input_file:
            parsers.append(Parser(input_file))

    output_file = open(output_filename, "w")
    code_writer = CodeWriter(output_file)
    if not (len(sys.argv) > 2 and sys.argv[2] == "no_bootstrap"):
        code_writer.write_comment(f"bootstrap")
        code_writer.write_bootstrap_code()
    for parser, fn in zip(parsers, filenames):
        code_writer.set_filename(os.path.split(fn)[1].split(".")[0])
        code_writer.write_comment(f"file {fn}")
        while parser.has_more_commands():
            parser.advance()
            code_writer.write_comment(parser.current_command)
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
            elif cmd_type == "C_CALL":
                name = parser.arg1()
                nb_args = parser.arg2()
                code_writer.write_call(name, nb_args)
            elif cmd_type == "C_FUNCTION":
                name = parser.arg1()
                nb_locals = parser.arg2()
                code_writer.write_function(name, nb_locals)
            elif cmd_type == "C_RETURN":
                code_writer.write_return()

    code_writer.close()

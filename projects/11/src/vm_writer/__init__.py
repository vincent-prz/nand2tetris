from typing import Dict, List
from jack_ast import JackAST


class JackASTVisitor:

    _class_name: str
    _class_nb_fields: int
    code: List[str]
    _current_subroutine_name: str
    _current_subroutine_type: str
    _current_if_label_idx: int
    _current_while_label_idx: int
    _memory_segment_map: Dict[str, str]

    def __init__(self):
        self.code = []
        self._current_if_label_idx = 0
        self._current_while_label_idx = 0
        self._memory_segment_map = {
            "var": "local",
            "arg": "argument",
            "field": "this",
        }

    def visit(self, root: JackAST) -> None:
        meth = getattr(self, f"visit_{root.node_type.lower()}", None)
        if meth is not None:
            meth(root)

    def visit_class(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        identifier = root.children[1]
        assert isinstance(identifier.children, str)
        self._class_name = identifier.children
        self._class_nb_fields = 0
        for c in root.children:
            self.visit(c)

    def visit_class_var_dec(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        dec_type = root.children[0]
        if dec_type.children == "field":
            self._class_nb_fields += len(
                [c for c in root.children if c.children == ","]
            ) + 1

    def visit_subroutine_dec(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        keyword = root.children[0]
        assert isinstance(keyword.children, str)
        identifier = root.children[2]
        assert isinstance(identifier.children, str)
        self._current_subroutine_name = f"{self._class_name}.{identifier.children}"
        self._current_subroutine_type = keyword.children
        for c in root.children:
            self.visit(c)

    def visit_subroutine_body(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        nb_local_vars = sum(
            len([_ for _ in c.children if _.children == ","]) + 1
            for c in root.children
            if c.node_type == "VAR_DEC" and isinstance(c.children, list)
        )
        self.code.append(f"function {self._current_subroutine_name} {nb_local_vars}")

        # allocate memory for constructors
        if self._current_subroutine_type == "constructor":
            self.code.append(f"push constant {self._class_nb_fields}")
            self.code.append("call Memory.alloc 1")
            self.code.append("pop pointer 0")
        # setting `this` for methods`
        elif self._current_subroutine_type == "method":
            self.code.append("push argument 0")
            self.code.append("pop pointer 0")
        statements = [c for c in root.children if c.node_type == "STATEMENTS"][0]
        self.visit(statements)

    def visit_statements(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        for c in root.children:
            self.visit(c)

    def visit_do_statement(self, root: JackAST) -> None:
        self._process_subroutine_call(root)
        # discard returned value
        # NOTE: not sure where to pop
        self.code.append("pop temp 0")

    def _process_subroutine_call(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        identifiers = [c for c in root.children if c.node_type == "IDENTIFIER"]
        is_method_call = False
        # case of call on a method of the current class, need to push `this`
        if len(identifiers) == 1:
            assert isinstance(identifiers[0].children, str)
            called_func_name = f"{self._class_name}.{identifiers[0].children}"
            is_method_call = True
            self.code.append("push pointer 0")
        else:  # call of the form <varname>.<subroutine>
            assert len(identifiers) == 2
            assert isinstance(identifiers[0].children, str)
            # case of a method call of the form <obj_name>.<routine>
            if identifiers[0].attributes is not None:
                is_method_call = True
                kind = identifiers[0].attributes.kind
                assert kind is not None
                memory_segment = self._memory_segment_map[kind]
                idx = identifiers[0].attributes.idx
                typ = identifiers[0].attributes.typ
                self.code.append(f"push {memory_segment} {idx}")
                called_func_name = f"{typ}.{identifiers[1].children}"
            # case of a plain function call
            else:
                called_func_name = f"{identifiers[0].children}.{identifiers[1].children}"

        # pushing explicit arguments
        for c in root.children:
            self.visit(c)
        expression_list = [
            c for c in root.children if c.node_type == "EXPRESSION_LIST"
        ][0]
        assert isinstance(expression_list.children, list)
        nb_args = len(
            [c for c in expression_list.children if c.node_type == "EXPRESSION"]
        )
        if is_method_call:
            nb_args += 1
        self.code.append(f"call {called_func_name} {nb_args}")

    def visit_let_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        # first visit expression on the right hand side
        expression = [c for c in root.children if c.node_type == "EXPRESSION"][0]
        self.visit(expression)

        identifier = root.children[1]
        assert identifier.attributes is not None
        assert identifier.attributes.mode == "usage"
        kind = identifier.attributes.kind
        assert kind is not None
        memory_segment = self._memory_segment_map[kind]
        memory_idx = identifier.attributes.idx
        self.code.append(f"pop {memory_segment} {memory_idx}")

    def visit_if_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        label_idx = self._current_if_label_idx
        self._current_if_label_idx += 1
        # first visit expression in condition
        expression = [c for c in root.children if c.node_type == "EXPRESSION"][0]
        self.visit(expression)
        # negate condition
        self.code.append("not")

        # if ~cond goto else
        # vm code for if
        self.code.append(f"if-goto L_IF_{label_idx}_ELSE")
        statement_groups = [c for c in root.children if c.node_type == "STATEMENTS"]
        assert len(statement_groups) <= 2
        if len(statement_groups) == 0:
            return
        self.visit(statement_groups[0])
        self.code.append(f"goto L_IF_{label_idx}_ENDIF")

        # vm code for else
        self.code.append(f"label L_IF_{label_idx}_ELSE")
        if len(statement_groups) == 2:
            self.visit(statement_groups[1])
        self.code.append(f"label L_IF_{label_idx}_ENDIF")

    def visit_while_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        label_idx = self._current_while_label_idx
        self._current_while_label_idx += 1
        self.code.append(f"label L_WHILE_{label_idx}_START")

        # first visit expression in condition
        expression = [c for c in root.children if c.node_type == "EXPRESSION"][0]
        self.visit(expression)
        # negate condition
        self.code.append("not")

        # if ~cond goto endwhile
        # vm code for while body
        self.code.append(f"if-goto L_WHILE_{label_idx}_END")
        statement_groups = [c for c in root.children if c.node_type == "STATEMENTS"]
        assert len(statement_groups) == 1
        self.visit(statement_groups[0])
        self.code.append(f"goto L_WHILE_{label_idx}_START")

        # end while
        self.code.append(f"label L_WHILE_{label_idx}_END")

    def visit_expression_list(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        for c in root.children:
            self.visit(c)

    def visit_expression(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        terms = [c for c in root.children if c.node_type == "TERM"]
        ops = [c for c in root.children if c.node_type == "SYMBOL"]
        assert len(terms) == len(ops) + 1
        for t in terms:
            self.visit(t)
        for op in ops[::-1]:
            self.visit(op)

    def visit_term(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        term = root.children[0]
        if term.node_type == "INTEGER_CONSTANT":
            assert isinstance(term.children, int)
            self.code.append(f"push constant {term.children}")
        elif term.node_type == "KEYWORD":
            self.visit(term)
        # subroutine call case
        elif term.node_type == "IDENTIFIER" and len(root.children) > 1:
            self._process_subroutine_call(root)
        elif term.node_type == "IDENTIFIER":
            assert isinstance(term.children, str)
            assert term.attributes is not None
            assert term.attributes.mode == "usage"
            kind = term.attributes.kind
            assert kind is not None
            memory_segment = self._memory_segment_map[kind]
            memory_idx = term.attributes.idx
            self.code.append(f"push {memory_segment} {memory_idx}")
        elif term.node_type == "SYMBOL" and term.children in ["-", "~"]:
            unary_symbol = term.children
            assert isinstance(unary_symbol, str)
            self.visit(root.children[1])
            if unary_symbol == "-":
                self.code.append("neg")
            elif unary_symbol == "~":
                self.code.append("not")
        else:  # term of the form [expression] or (expression)
            self.visit(root.children[1])

    def visit_symbol(self, root: JackAST) -> None:
        """Should only be called inside expressions."""
        assert isinstance(root.children, str)
        symbol = root.children
        if symbol == "+":
            self.code.append("add")
        elif symbol == "*":
            self.code.append("call Math.multiply 2")
        elif symbol == "-":
            self.code.append("sub")
        elif symbol == "=":
            self.code.append("eq")
        elif symbol == "<":
            self.code.append("lt")
        elif symbol == ">":
            self.code.append("gt")
        elif symbol == "&":
            self.code.append("and")

    def visit_keyword(self, root: JackAST) -> None:
        """Should only be called inside expressions."""
        keyword = root.children
        assert isinstance(keyword, str)
        if keyword == "true":
            self.code.append("push constant 1")
            self.code.append("neg")
        elif keyword == "false":
            self.code.append("push constant 0")
        elif keyword == "this":
            self.code.append("push pointer 0")

    def visit_return_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        expressions = [c for c in root.children if c.node_type == "EXPRESSION"]
        assert len(expressions) <= 1
        if len(expressions) == 1:
            self.visit(expressions[0])
        else:
            self.code.append("push constant 0")
        self.code.append("return")


def write_vm_code(root: JackAST) -> str:
    visitor = JackASTVisitor()
    visitor.visit(root)
    return "\n".join(visitor.code)

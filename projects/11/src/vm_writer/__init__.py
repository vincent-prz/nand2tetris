from typing import List
from jack_ast import JackAST


class JackASTVisitor:

    class_name: str
    code: List[str]
    _current_subroutine_name: str
    _current_unary_op: str

    def __init__(self):
        self.code = []
        self._current_unary_op = ""

    def visit(self, root: JackAST) -> None:
        meth = getattr(self, f"visit_{root.node_type.lower()}", None)
        if meth is not None:
            meth(root)
        # if isinstance(root.children, list):
        #     for c in root.children:
        #         self.visit(c)

    def visit_class(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        identifier = root.children[1]
        assert isinstance(identifier.children, str)
        self.class_name = identifier.children
        for c in root.children:
            self.visit(c)

    def visit_subroutine_dec(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        identifier = root.children[2]
        assert isinstance(identifier.children, str)
        self._current_subroutine_name = f"{self.class_name}.{identifier.children}"
        # self.code.append(f"function {function_name} {len(parameter_list.children)}")
        for c in root.children:
            self.visit(c)

    def visit_subroutine_body(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        nb_local_vars = len(
            [
                id
                for c in root.children
                if c.node_type == "VAR_DEC" and isinstance(c.children, list)
                for id in c.children
                if id.node_type == "IDENTIFIER"
            ]
        )
        self.code.append(f"function {self._current_subroutine_name} {nb_local_vars}")
        statements = [c for c in root.children if c.node_type == "STATEMENTS"][0]
        assert isinstance(statements.children, list)
        for c in statements.children:
            self.visit(c)

    # def visit_var_dec(self, root: JackAST) -> None:
    #     assert isinstance(root.children, list)
    #     identifiers = [c for c in root.children if c.node_type == "IDENTIFIER"]
    #     pas

    def visit_do_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        # visit arguments expressions
        for c in root.children:
            self.visit(c)
        identifiers = [c for c in root.children if c.node_type == "IDENTIFIER"]
        if len(identifiers) == 1:
            assert isinstance(identifiers[0].children, str)
            called_func_name = identifiers[0].children
        else:
            assert len(identifiers) == 2
            assert isinstance(identifiers[0].children, str)
            assert isinstance(identifiers[1].children, str)
            called_func_name = f"{identifiers[0].children}.{identifiers[1].children}"
        expression_list = [
            c for c in root.children if c.node_type == "EXPRESSION_LIST"
        ][0]
        assert isinstance(expression_list.children, list)
        nb_args = len(
            [c for c in expression_list.children if c.node_type == "EXPRESSION"]
        )
        self.code.append(f"call {called_func_name} {nb_args}")

    def visit_let_statement(self, root: JackAST) -> None:
        assert isinstance(root.children, list)
        expression = [c for c in root.children if c.node_type == "EXPRESSION"][0]
        self.visit(expression)

        identifier = root.children[1]
        assert identifier.attributes is not None
        assert identifier.attributes.mode == "usage"
        if identifier.attributes.kind == "var":
            memory_segment = "local"
        else:
            raise ValueError("Unsupported variable kind")
        memory_idx = identifier.attributes.idx
        self.code.append(f"pop {memory_segment} {memory_idx}")

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
            self.code.append(f"push constant {self._current_unary_op}{term.children}")
        # subroutine call case, we cam reuse the same visitor as do statement
        elif term.node_type == "IDENTIFIER" and len(root.children) > 1:
            self.visit_do_statement(root)
        elif term.node_type == "IDENTIFIER":
            assert isinstance(term.children, str)
            assert term.attributes is not None
            assert term.attributes.mode == "usage"
            if term.attributes.kind == "var":
                memory_segment = "local"
            else:
                raise ValueError("Unsupported variable kind")
            memory_idx = term.attributes.idx
            self.code.append(f"push {memory_segment} {memory_idx}")
        elif term.node_type == "SYMBOL" and term.children in ["-", "~"]:
            self._current_unary_op = term.children
            self.visit(root.children[1])
            self._current_unary_op = ""
        else:  # term of the form [expression] or (expression)
            self.visit(root.children[1])

    def visit_symbol(self, root: JackAST) -> None:
        assert isinstance(root.children, str)
        symbol = root.children
        if symbol == "+":
            self.code.append("add")
        elif symbol == "*":
            self.code.append("call Math.multiply 2")
        elif symbol == "-":
            self.code.append("sub")

    def visit_return_statement(self, root: JackAST) -> None:
        self.code.append("return")


def write_vm_code(root: JackAST) -> str:
    visitor = JackASTVisitor()
    visitor.visit(root)
    return "\n".join(visitor.code)

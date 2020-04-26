from enum import Enum
from typing import Dict, NamedTuple, Optional


Kind = Enum("Kind", "STATIC FIELD ARG VAR")


def kind_to_str(kind: Kind) -> str:
    if kind == Kind.STATIC:
        return "static"
    if kind == Kind.FIELD:
        return "field"
    if kind == Kind.ARG:
        return "arg"
    return "var"


class SymbolTableValue(NamedTuple):
    typ: str
    kind: Kind
    idx: int


class SymbolTable:
    _class_scope: Dict[str, SymbolTableValue]
    _subroutine_scope: Dict[str, SymbolTableValue]
    _nb_per_kind: Dict[Kind, int]

    def __init__(self) -> None:
        self._class_scope = {}
        self._subroutine_scope = {}
        self._nb_per_kind = {
            Kind.STATIC: 0,
            Kind.FIELD: 0,
            Kind.ARG: 0,
            Kind.VAR: 0,
        }

    def start_subroutine(self) -> None:
        self._subroutine_scope = {}
        self._nb_per_kind[Kind.ARG] = 0
        self._nb_per_kind[Kind.VAR] = 0

    def define(self, name: str, typ: str, kind: Kind) -> int:
        idx = self._nb_per_kind[kind]
        if kind in (Kind.STATIC, Kind.FIELD):
            self._class_scope[name] = SymbolTableValue(typ, kind, idx)
        else:
            self._subroutine_scope[name] = SymbolTableValue(typ, kind, idx)
        self._nb_per_kind[kind] = idx + 1
        return idx

    def var_count(self, kind: Kind) -> int:
        return self._nb_per_kind[kind]

    def _get_value(self, name: str) -> Optional[SymbolTableValue]:
        if name in self._subroutine_scope:
            return self._subroutine_scope[name]
        return self._class_scope.get(name)

    def kind_of(self, name: str) -> Optional[Kind]:
        if (val := self._get_value(name)) is not None:
            return val.kind
        return None

    def type_of(self, name: str) -> Optional[str]:
        if (val := self._get_value(name)) is not None:
            return val.typ
        return None

    def index_of(self, name: str) -> Optional[int]:
        if (val := self._get_value(name)) is not None:
            return val.idx
        return None

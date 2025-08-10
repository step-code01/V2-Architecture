from typing import Optional, Any, Protocol, TypeVar, SupportsAbs

_S = TypeVar("_S", bound=Any)
_SupportsAbsAndDunderGE = SupportsAbs

class TestCase(Protocol):
    def assertAlmostEqual(
        self,
        first: _S,
        second: _S,
        *,
        places: Optional[int] = ...,
        msg: Optional[str] = ...,
        delta: Optional[_SupportsAbsAndDunderGE] = ...,
    ) -> None: ...

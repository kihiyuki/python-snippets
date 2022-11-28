from typing import Optional, List
from pathlib import Path
import gzip
import lzma
import bz2

_failedmodules = dict()
try:
    from chardet import detect
except Exception as e:
    _failedmodules["chardet"] = e


__version__ = "0.0.1"
__all__ = [
]

_OPENFUNCTIONS = {
    None: open,
    "gzip": gzip.open,
    "xz": lzma.open,
    "bz2": bz2.open,
}


class File(object):
    def __init__(
        self,
        __f: str,
        detect_encoding: bool = False,
    ) -> None:
        self.path = Path(__f)
        self.encoding: Optional[str] = None
        self.compression: Optional[str] = None

        suffix = self.path.suffix
        if suffix == ".gz":
            self.compression = "gzip"
        elif suffix == ".xz":
            self.compression = "xz"
        elif suffix == ".bz2":
            self.compression = "bz2"

        if detect_encoding:
            self.__detect_encoding()
        return None

    def __str__(self) -> str:
        return str(self.path)

    def __open(self, mode: str):
        _func = _OPENFUNCTIONS[self.compression]
        return _func(
            self.path,
            mode=mode,
            encoding=self.encoding if self.compression is None else None
        )

    def __detect_encoding(self) -> None:
        if "chardet" in _failedmodules:
            raise _failedmodules["chardet"]
        with self.__open(mode="rb") as f:
            b = f.read(16)  # hardcode
            self.encoding = detect(b)["encoding"]
        # print("encoding", self.encoding)
        return None

    def open(
        self,
        mode: str = "r",
        encoding: Optional[str] = None,
    ):
        if encoding is not None:
            self.encoding = encoding
        return self.__open(mode=mode)

    def readlines(self, rstrip=True) -> List[str]:
        if (self.compression is None) or (self.encoding is None):
            with self.__open(mode="r") as f:
                lines = f.readlines()
        else:
            with self.__open(mode="rb") as f:
                lines = [x.decode(self.encoding) for x in  f.readlines()]
        if rstrip:
            lines = [x.rstrip() for x in lines]
        return lines

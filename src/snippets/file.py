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


__version__ = "0.0.2"
__all__ = [
    "File"
]


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

    def __open(
        self,
        mode: str,
        encoding: Optional[str] = None,
    ):
        if self.compression is None:
            _open = open
        elif self.compression == "gzip":
            _open = gzip.open
        elif self.compression == "xz":
            _open = lzma.open
        elif self.compression == "bz2":
            _open = bz2.open
        else:
            raise ValueError("invalid compression mode")

        if encoding is None:
            encoding = self.encoding if self.compression is None else None

        return _open(
            self.path,
            mode=mode,
            encoding=encoding,
        )

    def __detect_encoding(self) -> None:
        if "chardet" in _failedmodules:
            raise _failedmodules["chardet"]
        with self.__open(mode="rb") as f:
            b = f.read(16)  # hardcode
            self.encoding = detect(b)["encoding"]
        return None

    def open(
        self,
        mode: str = "r",
        encoding: Optional[str] = None,
    ):
        return self.__open(mode=mode, encoding=encoding)

    def readlines(
        self,
        rstrip: bool = True,
        encoding: Optional[str] = None,
    ) -> List[str]:
        if encoding is None:
            encoding = self.encoding
        if self.compression is None:
            with self.__open(mode="r", encoding=encoding) as f:
                lines = f.readlines()
        else:
            with self.__open(mode="rb") as f:
                if encoding is None:
                    lines = [x.decode() for x in f.readlines()]
                else:
                    lines = [x.decode(encoding) for x in f.readlines()]
        if rstrip:
            lines = [x.rstrip() for x in lines]
        return lines

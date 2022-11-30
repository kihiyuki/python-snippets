import os
import random
import gzip, lzma, bz2
from pathlib import Path
from typing import Optional

import pytest

from src.snippets.file import File

WINDOWS = os.name == "nt"

LINES = ["あいうえお ABC123", "", "かきくけこ,DEF:4"]
S = "\n".join(LINES)
# S = "あいうえお ABC123\n\nかきくけこ,DEF:4\n"
ENCODINGS = [None, "utf-8", "euc_jp"]
COMPRESSIONS = [None, "gzip", "xz", "bz2"]


@pytest.fixture(scope="function", autouse=False)
def filename():
    filename = f"test_{random.randint(100000,999999)}.txt"
    yield filename
    for p in Path().glob(f"{filename}*"):
        p.unlink()


def write(
    filename: str,
    encoding: Optional[str] = None,
    compression: Optional[str] = None
) -> str:
    if encoding is None:
        data = S.encode()
    else:
        data = S.encode(encoding=encoding)

    if compression is None:
        pass
    elif compression == "gzip":
        filename += ".gz"
        data = gzip.compress(data)
    elif compression == "xz":
        filename += ".xz"
        data = lzma.compress(data)
    elif compression == "bz2":
        filename += ".bz2"
        data = bz2.compress(data)

    with open(filename, mode="wb") as f:
        f.write(data)
    return filename


class TestFile(object):
    @pytest.mark.parametrize("compression", COMPRESSIONS)
    @pytest.mark.parametrize("encoding", ENCODINGS)
    @pytest.mark.parametrize("detect_encoding", [False, True])
    def test_file(
        self,
        filename: str,
        compression: Optional[str],
        encoding: Optional[str],
        detect_encoding: bool,
    ) -> None:
        filename = write(filename, encoding=encoding, compression=compression)
        file = File(filename, detect_encoding=detect_encoding)
        assert str(filename) == str(file)

        encoding_read = encoding
        if detect_encoding:
            encoding_read = None
        elif WINDOWS and (encoding is None):
            encoding_read = "utf-8"
        lines = file.readlines(encoding=encoding_read)
        assert lines == LINES
        return None

    @pytest.mark.parametrize("encoding", ENCODINGS)
    def test_open(
        self,
        filename: str,
        encoding: Optional[str],
    ) -> None:
        filename = write(filename, encoding=encoding)
        file = File(filename)
        if WINDOWS and (encoding is None):
            encoding = "utf-8"
        with file.open(encoding=encoding) as f:
            lines = f.readlines()
        lines = [x.rstrip() for x in lines]
        assert lines == LINES

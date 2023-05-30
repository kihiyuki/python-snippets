# https://github.com/kihiyuki/python-snippets
# Copyright (c) 2022 kihiyuki
# Released under the MIT license
# Supported Python versions: 3.7, 3.8, 3.9, 3.10, 3.11
# Requires: (using only Python Standard Library)
import shutil
from configparser import ConfigParser, DEFAULTSECT
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any
from warnings import warn


__version__ = "2.2.4"
__all__ = [
    "Config",
]
DEFAULTFILE: Optional[str] = "config.ini"
_DDT = Dict[str, Dict[str, Any]]
_DT = Dict[str, _DDT]

class Config(object):
    def __init__(
        self,
        __d: Union[str, Path, Dict[str, Any], Dict[str, Dict[str, Any]], None] = DEFAULTFILE,
        section: str = DEFAULTSECT,
        encoding: Optional[str] = None,
        notfound_ok: bool = False,
        default: Union[Dict[str, Any], Dict[str, Dict[str, Any]], None] = None,
        cast: bool = False,
        strict_cast: bool = False,
        strict_key: bool = False,
    ) -> None:
        """Read configuration file/data and convert its section to dict.

        Args:
            __d: Configuration filepath(str or Path) or data(dict)
            section: Section
            encoding: File encoding
            notfound_ok: If True, return empty dict.
            default: Default values
            cast: If True, cast to type of default value automatically.
            strict_cast: If False, cast as much as possible.
            strict_key: If False, keys can be added.

        Raises:
            FileNotFoundError: If `notfound_ok` is False and `file` not found.
            ValueError: If `strict_cast` is True and failed to cast.
            KeyError: If `strict_key` is True and some keys of configfile is not in default.
        """
        self._cast = cast
        self._strict_cast = strict_cast
        self._strict_key = strict_key

        self.filepath: Optional[Path] = None
        self.default: _DT
        self.data: _DT
        self.section: str = self._autocorrect(section, name="section name")

        if default is None:
            default = {self.section: {}}
        self.default = self._init_configdict(
            default,
            section=self.section,
        )

        if __d is None:
            self.data = {self.section: {}}
        else:
            if type(__d) is dict:
                file = None
                data = __d
                if not self._have_section(data):
                    data = {self.section: data}
            else:
                file = __d
                data = None

            # load all sections(section = None)
            self.data = self._load(
                file=file,
                data=data,
                section=None,
                encoding=encoding,
                notfound_ok=notfound_ok,
            )
        return None

    @staticmethod
    def _have_section(data: _DDT) -> bool:
        """Check if all values of data are dict"""
        return all([isinstance(v, dict) for v in data.values()])

    @staticmethod
    def _autocorrect(
        __x: Any,
        name: str = "",
        string: bool = True,
        lower: bool = False,
        convert: bool = True,
    ) -> str:
        if string and type(__x) is not str:
            if convert:
                __x = str(__x)
                warn(f"Convert {name} to string: {__x}")
            else:
                raise TypeError(f"{name} must be string: {__x}({type(__x)})")
        if lower and not __x.islower():
            if convert:
                __x = __x.lower()
                warn(f"Convert {name} to lowercase: {__x}")
            else:
                raise ValueError(f"{name} must be lowercase: {__x}")
        return __x

    # @staticmethod
    def _init_configdict(
        self,
        data: _DDT,
        section: Optional[str] = None,
    ) -> Dict[str, dict]:
        if self._have_section(data):
            if section is None:
                pass
            elif section not in data:
                data[section] = dict()
        else:
            if section is None:
                raise ValueError("Configdata must have section")
            data = {section: data}

        data: _DT
        data_ret: _DT = dict()
        for s, d in data.items():
            s = self._autocorrect(s, name="section name")
            data_ret[s] = dict()

            for k, v in d.items():
                k = self._autocorrect(k, name="key", lower=True)
                data_ret[s][k] = v

        return data_ret

    def _cast_value(self, __v: str, __v_def: Any) -> Any:
        try:
            _typename = type(__v_def).__name__
            # NOTE: bool must come before int
            for _type in [str, bool, float, int, list, tuple, set, dict]:
                if isinstance(__v_def, _type):
                    _typename = _type.__name__
                    break
            _raise = False
            if _typename in {"str"}:
                pass
            elif _typename in {"float", "int"}:
                __v = _type(__v)
            elif _typename in {"bool"}:
                if __v.lower() in {"true", "1"}:
                    __v = True
                elif __v.lower() in {"false", "0"}:
                    __v = False
                else:
                    _raise = True
            elif _typename in {"list"}:
                if __v.startswith("[") and __v.endswith("]"):
                    __v = eval(__v)
                else:
                    __v = __v.split(",")
            elif _typename in {"tuple"}:
                if __v.startswith("(") and __v.endswith(")"):
                    __v = eval(__v)
                else:
                    __v = tuple(__v.split(","))
            elif _typename in {"set"}:
                if __v.startswith("{") and __v.endswith("}"):
                    __v = eval(__v)
                else:
                    __v = set(__v.split(","))
            elif _typename in {"dict"}:
                if __v.startswith("{") and __v.endswith("}"):
                    __v = eval(__v)
                else:
                    __v = dict(tuple(x.split(":")) for x in __v.split(","))
            if _raise:
                raise ValueError(f'{_typename}("{__v}")')
        except ValueError as e:
            if self._strict_cast:
                raise ValueError(e)
            else:
                warn(f"cast failed: {e}", UserWarning)
        return __v

    def cast(
        self,
        __key: Optional[Any] = None,
        section: Optional[str] = None,
    ) -> Optional[Any]:
        """Cast to type of default value

        Example:
            >>> config.cast()
            >>> config.cast("key1")
            >>> config.cast("key1", section="debug")
        """
        if section is None:
            _sections = self.data.keys()
        else:
            _sections = [section]

        for s in _sections:
            if __key is not None:
                self.data[s][__key] = self._cast_value(self.data[s][__key], self.default[s][__key])
            else:
                for k in self.data[s].keys():
                    if k in self.default[s].keys():
                        self.data[s][k] = self._cast_value(self.data[s][k], self.default[s][k])
        return None

    def _load(
        self,
        file: Union[str, Path, None] = None,
        data: Union[_DT, _DDT, None] = None,
        section: Optional[str] = None,
        encoding: Optional[str] = None,
        notfound_ok: bool = False,
    ) -> _DT:
        if (file is not None) and (data is not None):
            raise ValueError("Both file and data are given")
        elif file is not None:
            self.filepath = Path(file)
            if self.filepath.is_file():
                parser = ConfigParser()
                with self.filepath.open(mode="r", encoding=encoding) as f:
                    parser.read_file(f)
                data = self.__parser_to_dict(parser)
            elif notfound_ok:
                warn(f"No such file or directory: {str(self.filepath)}", UserWarning)
                data = {DEFAULTSECT: {}}
            else:
                raise FileNotFoundError(file)
        elif data is not None:
            data = self._init_configdict(
                data=data,
                section=section,
            )
        else:
            raise ValueError("Both file and data are None")

        if section is None:
            sections_load = list(data.keys())
        else:
            sections_load = [section]

        if DEFAULTSECT not in sections_load:
            sections_load = [DEFAULTSECT] + sections_load

        # add default sections
        for s in self.default.keys():
            if s not in sections_load:
                sections_load.append(s)

        data_ret: _DT = dict()
        for s in sections_load:
            if s in self.default.keys():
                # initialize with default values
                data_ret[s] = self.default[s].copy()
                _empty_default = len(self.default[s]) == 0
            else:
                data_ret[s] = dict()
                _empty_default = True

            if s not in data.keys():
                continue
            for k, v in data[s].items():
                if k in data_ret[s]:
                    if self._cast:
                        v = self._cast_value(v, data_ret[s][k])
                elif self._strict_key:
                    if _empty_default:
                        pass
                    else:
                        raise KeyError(k)
                data_ret[s][k] = v

        return data_ret

    @staticmethod
    def __parser_to_dict(__p: ConfigParser) -> _DT:
        d = dict()
        for k, v in __p.items():
            d[k] = dict(v)
        return d

    def to_dict(self, allsection: bool = False) -> Union[_DT, _DDT]:
        """Convert to dict

        Example:
            >>> config = Config("./config.ini", section="a")
            >>> config.to_dict(allsection=True)
            {"DEFAULT": {"v": "xxx"}, "a": {"v": "yyy"}, "b": {"v": "zzz"}}
            >>> config.to_dict()
            {"v": "yyy"}
            >>> config.section = "b"
            >>> config.to_dict()
            {"v": "zzz"}
        """
        if allsection:
            return self.data.copy()
        else:
            return self.data[self.section].copy()

    def copy(
        self,
        cast: Optional[bool] = None,
        strict_key: Optional[bool] = None,
        strict_cast: Optional[bool] = None,
        ):
        if cast is None:
            cast = self._cast
        if strict_key is None:
            strict_key = self._strict_key
        if strict_cast is None:
            strict_cast = self._strict_cast
        return type(self)(
            self.data,
            section=self.section,
            default=self.default,
            cast=cast,
            strict_cast=strict_cast,
            strict_key=strict_key,
        )

    def __getitem__(self, __key: str):
        __key = self._autocorrect(__key, name="key", lower=True)
        return self.data[self.section][__key]

    def __setitem__(self, __key: str, __value) -> None:
        __key = self._autocorrect(__key, name="key", lower=True)
        if self.section not in self.data.keys():
            if self._strict_key:
                raise KeyError(self.section)
            else:
                self.data[self.section] = dict()

        if __key in self.data[self.section].keys():
            if self._cast:
                try:
                    __value = type(self.data[self.section][__key])(__value)
                except ValueError as e:
                    if self._strict_cast:
                        raise ValueError(e)
        elif self._strict_key:
            raise KeyError(__key)
        self.data[self.section][__key] = __value
        return None

    def __str__(self) -> str:
        return str(self.data)

    def __repr__(self) -> str:
        return f"{__class__.__name__}({repr(self.data)})"

    def __eq__(self, __o: Any) -> bool:
        if isinstance(__o, type(self)):
            # Config vs Config
            return self.to_dict(allsection=True) == __o.to_dict(allsection=True)
        elif isinstance(__o, ConfigParser):
            # Config vs ConfigParser
            parser = ConfigParser()
            parser.read_dict(self.data)
            return parser == __o
        elif type(__o) is dict:
            # Config vs dict
            data = self.to_dict(allsection=True)
            if data == __o:
                return True
            if len(data[DEFAULTSECT]) == 0:
                del data[DEFAULTSECT]
                return data == __o
        return False

    def save(
        self,
        file: Union[str, Path, None] = None,
        section: str = None,
        encoding: Optional[str] = None,
        mode: str = "add",
        keep_original_file: bool = True,
    ) -> None:
        """Save configuration dict to file.

        Args:
            file: Configuration file path
            section: Section (if single-section data)
            encoding: File encoding
            mode: 'interactive', 'write'('overwrite'), 'add', 'leave'
            exist_ok: If False and file exists, raise an error.
            overwrite: If True and file exists, overwrite.
            keep_original_file: If True, keep(copy) original file.

        Raises:
            ValueError: If `mode` is unknown
        """
        if file is None:
            if self.filepath is None:
                raise ValueError("filepath is not set")
            else:
                filepath = self.filepath
        else:
            filepath = Path(file)
        # if not filepath.parent.is_dir():
        #     raise FileNotFoundError(filepath.parent)

        if section is None:
            data = self.data
        else:
            # use only specified section
            data = {section: self.data[section]}

        if filepath.is_file():
            mode = mode.lower()
            if mode in ["i", "interactive"]:
                mode = input(f"'{filepath.name}' already exists --> (over[w]rite/[a]dd/[l]eave/[c]ancel)?: ").lower()
            if mode in ["w", "write", "overwrite"]:
                data_save = self._load(data=dict())
            elif mode in ["a", "add"]:
                data_save = self._load(
                    file=file,
                    encoding=encoding,
                    notfound_ok=True,
                )
            elif mode in ["l", "leave", "c", "cancel", "n", "no"]:
                return None
            else:
                raise ValueError(f"Unknown mode '{mode}'")

            for k in data.keys():
                if k in data_save.keys():
                    data_save[k].update(data[k])
                else:
                    data_save[k] = data[k]

            if keep_original_file:
                filepath_back = filepath.parent / f"{filepath.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copyfile(filepath, filepath_back)
        else:
            data_save = data

        parser = ConfigParser()
        parser.read_dict(data_save)
        with filepath.open(mode="w", encoding=encoding) as f:
            parser.write(f)
        return None

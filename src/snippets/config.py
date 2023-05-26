# https://github.com/kihiyuki/python-snippets
# Copyright (c) 2022 kihiyuki
# Released under the MIT license
import shutil
from configparser import ConfigParser, DEFAULTSECT
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any
from warnings import warn


__version__ = "2.2.0"
__all__ = [
    "Config",
]
DEFAULTFILE: Optional[str] = "config.ini"


def _have_section(data: dict) -> bool:
    have_section = True
    for v in data.values():
        if not isinstance(v, dict):
            have_section = False
            break
    return have_section


def _init_configdict(
    data: dict,
    section: Optional[str] = None,
    auto_sectionalize: bool = False,
) -> Dict[str, dict]:
    if _have_section(data):
        if section is None:
            pass
        elif section not in data:
            data[section] = dict()
    else:
        if section is None:
            if auto_sectionalize:
                section = DEFAULTSECT
            else:
                raise ValueError("Configdata must have section")
        data = {section: data}

    data_ret = dict()
    for s, d in data.items():
        if type(s) is not str:
            warn(f"Section name must be string: s -> '{s}'")
            s = str(s)
        data_ret[s] = dict()

        for k, v in d.items():
            if type(k) is not str:
                warn(f"Key must be string: {k} -> '{k}'")
                k = str(k)
            k_lower = k.lower()
            if k != k_lower:
                warn(f"Key must be lowercase: '{k}' -> '{k_lower}'")
            data_ret[s][k_lower] = v

    return data_ret


class Config(object):
    def __init__(
        self,
        __d: Union[str, Path, dict, None] = DEFAULTFILE,
        section: str = DEFAULTSECT,
        encoding: Optional[str] = None,
        notfound_ok: bool = False,
        default: Optional[dict] = None,
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
        self.section = section
        self._cast = cast
        self._strict_cast = strict_cast
        self._strict_key = strict_key

        self.filepath: Path
        self.default: dict
        # self.parser = ConfigParser()

        if default is None:
            default = {section: {}}
        if not _have_section(default):
            default = {section: default}
        self.default = _init_configdict(
            default,
            # section=section,
            # auto_sectionalize=True,
        )

        if __d is None:
            self.data = {section: {}}
        else:
            if type(__d) is dict:
                file = None
                data = __d
                if not _have_section(data):
                    data = {section: data}
            else:
                file = __d
                data = None
            self.data = self._load(
                file=file,
                data=data,
                encoding=encoding,
                notfound_ok=notfound_ok,
            )
        return None

    def _cast_value(self, __v: str, __v_def: Any) -> Any:
        try:
            _type = type(__v_def)
            _raise = False
            if _type in [str]:
                pass
            elif _type in [float, int]:
                __v = _type(__v)
            elif _type in [bool]:
                if __v.lower() in ["true", "1"]:
                    __v = True
                elif __v.lower() in ["false", "0"]:
                    __v = False
                else:
                    _raise = True
            elif _type in [list]:
                if __v.startswith("[") and __v.endswith("]"):
                    __v = eval(__v)
                else:
                    __v = __v.split(",")
            elif _type in [tuple]:
                if __v.startswith("(") and __v.endswith(")"):
                    __v = eval(__v)
                else:
                    __v = tuple(__v.split(","))
            elif _type in [set]:
                if __v.startswith("{") and __v.endswith("}"):
                    __v = eval(__v)
                else:
                    __v = set(__v.split(","))
            elif _type in [dict]:
                if __v.startswith("{") and __v.endswith("}"):
                    __v = eval(__v)
                else:
                    __v = dict(tuple(x.split(":")) for x in __v.split(","))
            if _raise:
                raise ValueError(f'{_type.__name__}("{__v}")')
        except ValueError as e:
            if self._strict_cast:
                raise ValueError(e)
            else:
                warn(f"cast failed: {e}")
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
        data: Optional[dict] = None,
        section: Optional[str] = None,
        encoding: Optional[str] = None,
        notfound_ok: bool = False,
    ) -> dict:
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
                data = {DEFAULTSECT: {}}
            else:
                raise FileNotFoundError(file)
        elif data is not None:
            if _have_section(data):
                pass
            elif section is not None:
                data = {section: data}
            data = _init_configdict(
                data,
                auto_sectionalize=True,
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
        for k in self.default.keys():
            if k not in sections_load:
                sections_load.append(k)

        data_ret = dict()
        for s in sections_load:
            if s in self.default:
                # initialize with default values
                data_ret[s] = self.default[s].copy()
            else:
                data_ret[s] = dict()
            if s not in data.keys():
                continue
            for k, v in data[s].items():
                if k in data_ret[s]:
                    if self._cast:
                        v = self._cast_value(v, data_ret[s][k])
                elif self._strict_key:
                    raise KeyError(k)
                data_ret[s][k] = v

        return data_ret

    @staticmethod
    def __parser_to_dict(__p: ConfigParser) -> dict:
        d = dict()
        for k, v in __p.items():
            d[k] = dict(v)
        return d

    def to_dict(self, allsection: bool = False) -> dict:
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

    def copy(self):
        return type(self)(
            self.data,
            section=self.section,
            default=self.default,
            cast=self.cast,
            strict_cast=self._strict_cast,
            strict_key=self._strict_key,
        )

    def __getitem__(self, __key):
        return self.data[self.section][__key]

    def __setitem__(self, __key, __value) -> None:
        if self.section not in self.data.keys():
            if self._strict_key:
                raise KeyError(self.section)
            else:
                self.data[self.section] = dict()

        if __key in self.data[self.section].keys():
            if self.cast:
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
        if isinstance(__o, Config):
            # Config vs Config
            if self.to_dict(allsection=True) == __o.to_dict(allsection=True):
                return True
        elif isinstance(__o, ConfigParser):
            # Config vs ConfigParser
            parser = ConfigParser()
            parser.read_dict(self.data)
            if parser == __o:
                return True
        elif type(__o) is dict:
            # Config vs dict
            data = self.to_dict(allsection=True)
            if data == __o:
                return True
            if len(data[DEFAULTSECT]) == 0:
                del data[DEFAULTSECT]
                if data == __o:
                    return True
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
            filepath = self.filepath
        else:
            filepath = Path(file)

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

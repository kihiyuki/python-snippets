# https://github.com/kihiyuki/python-snippets
# MIT License
import shutil
from configparser import ConfigParser, DEFAULTSECT
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


__version__ = "2.0.0"
__all__ = [
    "Config",
]
DEFAULT_FILENAME: Optional[str] = "./config.ini"


class Config(object):
    def __init__(
        self,
        __d: Union[str, Path, dict, None] = DEFAULT_FILENAME,
        section: Optional[str] = None,
        encoding: Optional[str] = None,
        notfound_ok: bool = False,
        default: Optional[dict] = None,
        cast: bool = False,
        strict_cast: bool = False,
        strict_key: bool = False,
    ) -> None:
        """Read configuration file/data and convert its section to dict.

        Args:
            __d (str or Path or dict, optional): Configuration filepath or data(dict)
            section (str, optional): Section (If None, load all sections)
            encoding (str, optional): File encoding
            notfound_ok (bool, optional): If True, return empty dict.
            default (dict, optional): Default values of config
            cast (bool, optional): If True, cast to type of default value.
            strict_cast (bool, optional): If False, cast as much as possible.
            strict_key (bool, optional): If False, keys can be added.

        Returns:
            dict

        Raises:
            FileNotFoundError: If `notfound_ok` is False and `file` not found.
            ValueError: If `strict_cast` is True and failed to cast.
            KeyError: If `strict_key` is True and some keys of configfile is not in default.
        """
        self.cast = cast
        self.strict_cast = strict_cast
        self.strict_key = strict_key

        self.filepath: Path
        self.parser = ConfigParser()

        if default is None:
            self.default = dict()
        else:
            self.default = self.__init_configdict(default, section=section)

        if __d is None:
            self.data = dict()
        else:
            if type(__d) is dict:
                file = None
                data = __d
            else:
                file = __d
                data = None
            self.data = self._load(
                file=file,
                data=data,
                section=section,
                encoding=encoding,
                notfound_ok=notfound_ok,
            )
        return None

    @staticmethod
    def __init_configdict(data: dict, section: Optional[str] = None):
        have_section = True
        for v in data.values():
            if not isinstance(v, dict):
                have_section = False
                break

        if have_section:
            if section is None:
                pass
            elif section not in data:
                data[section] = dict()
        else:
            if section is None:
                raise ValueError("configdata must have section")
            else:
                data = {section: data}

        return data

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
                with self.filepath.open(mode="r", encoding=encoding) as f:
                    self.parser.read_file(f)
            elif not notfound_ok:
                raise FileNotFoundError(file)
        elif data is not None:
            try:
                d = self.__init_configdict(data, section=section)
            except ValueError:
                d = self.__init_configdict(data, section=DEFAULTSECT)
            self.parser.read_dict(d)
        else:
            raise ValueError("Both file and data are None")

        allsection = section is None
        if allsection:
            sections_file = self.parser.sections()
            if len(dict(self.parser[DEFAULTSECT])) > 0:
                sections_file = [DEFAULTSECT] + sections_file
        else:
            sections_file = [section]
        sections = sections_file.copy()

        for k in self.default.keys():
            if k not in sections:
                sections.append(k)

        data = dict()
        for s in sections:
            if s in self.default:
                data[s] = self.default[s].copy()
            else:
                data[s] = dict()
            if s not in sections_file:
                continue
            for k, v in dict(self.parser[s]).items():
                if k in data[s]:
                    if self.cast:
                        try:
                            # cast to type(default[k])
                            v = type(data[s][k])(v)
                        except ValueError as e:
                            if self.strict_cast:
                                raise ValueError(e)
                elif self.strict_key:
                    raise KeyError(k)
                data[s][k] = v

        if not allsection:
            data = data[section]

        return data

    def to_dict(self) -> dict:
        __d = dict()
        for k, v in self.parser.items():
            __d[k] = dict(v)
        return __d

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Config):
            # Config vs Config
            if self.parser == __o.parser:
                return True
        elif type(__o) is dict:
            # Config vs dict
            if self.to_dict() == __o:
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
            file (str or Path, optional): Configuration file path
            section (str, optional): Section (if single-section data)
            encoding (str, optional): File encoding
            mode (str, optional): 'interactive', 'write'('overwrite'), 'add', 'leave'
            exist_ok (bool, optional): If False and file exists, raise an error.
            overwrite (bool, optional): If True and file exists, overwrite.
            keep_original_file (bool, optional): If True, keep(copy) original file.

        Returns:
            None

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

        write = True
        if filepath.is_file():
            mode = mode.lower()
            if mode in ["i", "interactive"]:
                mode = input(f"'{filepath.name}' already exists --> (over[w]rite/[a]dd/[l]eave/[c]ancel)?: ").lower()
            if mode in ["w", "write", "overwrite"]:
                data_save = dict()
            elif mode in ["a", "add"]:
                data_save = self._load(
                    file = file,
                    section = None, 
                    encoding = encoding,
                    notfound_ok = True,
                )
            elif mode in ["l", "leave", "c", "cancel", "n", "no"]:
                write = False
                keep_original_file = False
            else:
                raise ValueError(f"Unknown mode '{mode}'")

            data_save.update(data)

            if keep_original_file:
                filepath_back = filepath.parent / f"{filepath.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copyfile(filepath, filepath_back)
        else:
            data_save = data

        if write:
            parser = ConfigParser()
            parser.read_dict(data_save)
            with filepath.open(mode="w", encoding=encoding) as f:
                parser.write(f)
        return None

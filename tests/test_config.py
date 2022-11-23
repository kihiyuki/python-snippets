import shutil
import math
from pathlib import Path

import pytest

from src.snippets.config import Config, DEFAULTSECT


VERBOSE = True
TEMPDIR = "./testtemp"
CONFIGFILE = TEMPDIR + "/config.ini"
EMPTYDICT = {DEFAULTSECT: {}}


@pytest.fixture(scope="class", autouse=True)
def tempdir():
    tempdirpath = Path(TEMPDIR).resolve()
    if tempdirpath.is_dir():
        shutil.rmtree(str(tempdirpath))
    tempdirpath.mkdir(exist_ok=False)

    yield None

    shutil.rmtree(str(tempdirpath))


@pytest.fixture(scope="function", autouse=False)
def sampleconfig() -> Config:
    data = {
        DEFAULTSECT: dict(
            x = "dx",
        ),
        "a": dict(
            x = "ax",
            y = "ay",
            n = "1",
        ),
        "b": dict(
            x = "bx",
            y = "by",
            n = "2",
        ),
    }
    config = Config(data)
    config.save(CONFIGFILE, mode="write")

    yield config

    Path(CONFIGFILE).unlink()


@pytest.fixture(scope="function", autouse=False)
def sampleconfig_cast() -> Config:
    data = {
        DEFAULTSECT: dict(
            s1 = "Abc,123",
            s2 = "1.5",
            b = False,
            i = -2,
            f = 2.0,
            l = ["", False],
            t = (),
            st = {7, 8},
            d = dict(a=5, b="B"),
        ),
    }
    config = Config(data)
    config.save(CONFIGFILE, mode="write")

    yield config

    Path(CONFIGFILE).unlink()

class TestConfig(object):
    def test_load(self, sampleconfig: Config):
        config_load = Config(CONFIGFILE)
        assert config_load == sampleconfig

        with pytest.raises(FileNotFoundError):
            # notfound_ok = False
            _ = Config(".INVALID")
        config_load = Config(".INVALID", notfound_ok=True)
        assert config_load == EMPTYDICT

    def test_load_section(self, sampleconfig: Config):
        # load all section when choose a section
        config_load = Config(CONFIGFILE, section="a")
        assert config_load == sampleconfig
        # load all section when choose a section which is not exists
        config_load = Config(CONFIGFILE, section="xxx")
        c: dict = sampleconfig.to_dict(allsection=True)
        c.update({"xxx": {}})
        assert config_load == c

    def test_load_default(self, sampleconfig: Config):
        default = dict(n=11, m=12)
        config_load = Config(CONFIGFILE, section="a", default=default)
        config_load2 = Config(CONFIGFILE, default={"a": default})
        c = sampleconfig.to_dict(allsection=True)
        c["a"]["m"] = 12
        assert config_load.to_dict() == c["a"]
        assert config_load2 == c

        # strict_key
        with pytest.raises(KeyError):
            _ = Config(CONFIGFILE, default={"a": default}, strict_key=True)

        # strict_cast
        with pytest.raises(ValueError):
            _ = Config(CONFIGFILE, default={"a": dict(x=0)}, cast=True, strict_cast=True)

        # cast
        config_load = Config(CONFIGFILE, default={"a": default}, cast=True)
        c = sampleconfig.to_dict(allsection=True)
        c["a"]["n"] = int(c["a"]["n"])
        c["a"]["m"] = 12
        assert config_load == c

    def test_load_default_cast(self, sampleconfig_cast: Config):
        config_load = Config(CONFIGFILE, default=sampleconfig_cast.to_dict(allsection=True), cast=True)
        assert config_load.data[DEFAULTSECT].keys() == sampleconfig_cast.data[DEFAULTSECT].keys()
        for k in config_load.data[DEFAULTSECT].keys():
            if type(sampleconfig_cast[k]) is float:
                assert math.isclose(config_load[k], sampleconfig_cast[k])
            else:
                assert config_load[k] == sampleconfig_cast[k]

    def test_save(self, sampleconfig: Config):
        data = dict(hoge=dict(fuga=5))
        # invalid mode
        with pytest.raises(ValueError):
            config = Config(data)
            config.save(CONFIGFILE, mode="x")

    @pytest.mark.parametrize("mode", ["w", "Write", "OVERWRITE"])
    def test_save_write(self, sampleconfig: Config, mode):
        data = dict(hoge=dict(fuga=5))
        data_str = dict(hoge=dict(fuga="5"))
        config = Config(data)
        config.save(CONFIGFILE, mode=mode)
        config_load = Config(CONFIGFILE)
        assert config_load == data_str

    @pytest.mark.parametrize("mode", ["a", "ADD"])
    def test_save_add(self, sampleconfig: Config, mode):
        data = dict(a=dict(x="addx", z="addz"), b=dict(y="addy"))
        config = Config(data)
        config.save(CONFIGFILE, mode=mode)
        config_load = Config(CONFIGFILE)
        sampleconfig.section = "a"
        sampleconfig["x"] = "addx"
        sampleconfig["z"] = "addz"
        sampleconfig.section = "b"
        sampleconfig["y"] = "addy"
        assert config_load == sampleconfig

    @pytest.mark.parametrize("section", [DEFAULTSECT, "a", "c"])
    @pytest.mark.parametrize("has_section", [False, True])
    def test_save_add_param(self, sampleconfig: Config, section, has_section):
        data = dict(x="addx", z="addz")
        if has_section:
            data = {section: data}
        config = Config(data, section=section)
        config_load = Config(CONFIGFILE, section=section)
        config.save(CONFIGFILE, mode="a")
        config_load_aftersave = Config(CONFIGFILE, section=section)

        config_load["x"] = "addx"
        config_load["z"] = "addz"
        if section == DEFAULTSECT:
            config_load.data["a"]["z"] = "addz"
            config_load.data["b"]["z"] = "addz"

        assert config_load == config_load_aftersave

    @pytest.mark.parametrize("mode", ["l", "leave", "c", "Cancel", "N", "no"])
    def test_save_leave(self, sampleconfig, mode):
        data = dict(hoge=dict(fuga="5"))
        config = Config(data)
        config.save(CONFIGFILE, mode=mode)
        config_load = Config(CONFIGFILE)
        assert config_load != data
        assert config_load == sampleconfig

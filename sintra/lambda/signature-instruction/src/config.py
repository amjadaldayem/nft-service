from pathlib import Path

from dynaconf import Dynaconf

_settings_file = Path(__file__).absolute().parent / "settings.toml"

settings = Dynaconf(
    envvar_prefix="SINTRA",
    settings_file=[_settings_file],
)

import socket

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="INTERFACE", environments=True, settings_files=["settings.toml"]
)

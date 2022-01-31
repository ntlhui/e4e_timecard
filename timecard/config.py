from __future__ import annotations

from pathlib import Path
from typing import Optional

import appdirs
import schema
import yaml

import timecard
class Config:
    __instance: Optional[Config] = None

    SCHEMA = schema.Schema(
        {
            'logPath': str,
            'email': str,
            'password': str
        }
    )

    def __init__(self, configPath: Path):
        if not configPath.is_file():
            configPath.parent.mkdir(parents=True, exist_ok=True)
            with open(configPath.as_posix(), 'w') as configFile:
                user_log_path = Path(appdirs.user_log_dir(appname=timecard.__appname__), 'log.log')
                user_log = user_log_path.as_posix()
                configFile.write(yaml.safe_dump(
                    {
                        'logPath': user_log,
                        'email': '',
                        'password': ''
                    }
                ))
        with open(configPath.as_posix(), 'r') as configFile:
            data = yaml.safe_load(configFile)
            self.SCHEMA.validate(data)

        self.__logPath = data['logPath']
        self.__email = data['email']
        self.__password = data['password']

    @property
    def logPath(self) -> Path:
        return Path(self.__logPath)

    @property
    def email(self) -> str:
        return self.__email

    @property
    def password(self) -> str:
        return self.__password

    @classmethod
    def instance(cls, *, configPath: Path=None) -> Config:
        if cls.__instance is None:
            if configPath is None:
                raise RuntimeError
            cls.__instance = Config(configPath)
        return cls.__instance
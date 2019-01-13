from __future__ import annotations

from dataclasses import dataclass
from configparser import ConfigParser
from os import path
from typing import List


class RcloneConfig:
    def __init__(self, config_string: str, filePath: bool = False) -> None:
        self._config_values: ConfigParser = ConfigParser(allow_no_value=True)

        if not filePath:
            self._config_values.read_string(config_string)
        else:
            read_files: List[str] = self._config_values.read(config_string)
            if len(read_files) != 1 and read_files[0] != config_string:
                raise FileNotFoundError(f"Can't find rclone config at {config_string}")

        self.remotes: List[RCloneRemote] = []

        for remote in self._config_values.sections():
            self.remotes.append(RCloneRemote(remote, self._config_values))

    @staticmethod
    def get_default_config() -> RcloneConfig:
        default_config_location: str = path.expanduser("~/.config/rclone/rclone.conf")

        return RcloneConfig(default_config_location, True)


class RCloneRemote:
    def __init__(self, remote_name: str, config_file: ConfigParser):
        self.name: str = remote_name
        self.options: RCloneRemoteOptions = RCloneRemoteOptions(
            remote_type=config_file.get(self.name, "type")
        )


@dataclass
class RCloneRemoteOptions:
    remote_type: str

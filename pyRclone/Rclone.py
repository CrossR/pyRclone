import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .RcloneConfig import RcloneConfig


class RcloneError(Enum):
    RCLONE_MISSING = -1
    PYTHON_EXCEPTION = -2
    SUCCESS = 0
    SYNTAX_OR_USAGE_ERROR = 1
    UNCATEGORISED = 2
    FOLDER_NOT_FOUND = 3
    FILE_NOT_FOUND = 4
    RETRY_ERROR = 5
    NO_RETRY_ERROR = 6
    FATAL_ERROR = 7
    TRANSFER_EXCEEDED = 8


@dataclass
class RcloneOutput:
    return_code: RcloneError
    output: List[str]
    error: List[str]


class Rclone:
    """Rclone

    A class to wrap the Rclone binary.
    """

    def __init__(self, config: Optional[RcloneConfig] = None) -> None:
        self.logger: logging.Logger = logging.getLogger("Rclone")

        if config is None:
            self.config: RcloneConfig = RcloneConfig.get_default_config()
        else:
            self.config: RcloneConfig = config

    def _execute(self, command_to_run: List[str]) -> RcloneOutput:
        """_execute

        A helper function to run a given rclone command, and return the output.

        The command is expected to be given as a list of strings, ie
        the command "rclone lsd dropbox:" would be:
            ["rclone", "lsd", "dropbox:"]
        """
        self.logger.debug(f"Running: {command_to_run}")

        try:
            with subprocess.Popen(
                command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ) as rclone_process:
                output: str
                error: bytes
                (output, error) = rclone_process.communicate()

                self.logger.debug(f"Command returned {output}")

                if error:
                    self.logger.warning(error.decode("utf-8").replace("\\n", "\n"))

                return RcloneOutput(
                    RcloneError(rclone_process.returncode),
                    output.splitlines(),
                    error.decode("utf-8").splitlines(),
                )
        except FileNotFoundError as e:
            self.logger.exception(f"Can't find rclone executable. {e}")
            return RcloneOutput(RcloneError.RCLONE_MISSING, [""], [""])
        except Exception as e:
            self.logger.exception(f"Exception running {command_to_run}. Exception: {e}")
            return RcloneOutput(RcloneError.PYTHON_EXCEPTION, [""], [""])

    def command(self, command: str, arguments: List[str] = []) -> RcloneOutput:
        """command

        Run a given command.

        This will add on the associated rclone parts (ie, "rclone", "--conf XXX")
        """

        full_command: List[str] = ["rclone", command]
        full_command += arguments

        return self._execute(full_command)

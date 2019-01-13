import logging
import subprocess
from typing import List, Optional
from dataclasses import dataclass

from .RcloneConfig import RcloneConfig


@dataclass
class RcloneOutput:
    return_code: int
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
                    return_code=rclone_process.returncode,
                    output=output.splitlines(),
                    error=error.decode("utf-8").splitlines(),
                )
        except FileNotFoundError as e:
            self.logger.exception(f"Can't find rclone executable. {e}")
            return RcloneOutput(return_code=-2, output=[""], error=[""])
        except Exception as e:
            self.logger.exception(f"Exception running {command_to_run}. Exception: {e}")
            return RcloneOutput(return_code=-2, output=[""], error=[""])

# pylint: disable=C0411
"""rclone

A typed interface for interactions with an RClone executable.
"""

import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Tuple

from .rclone_config import RcloneConfig


class RcloneError(Enum):
    """RcloneError

    An enum wrapping the errors that Rclone can raise, and some
    interface specific ones.
    """

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
    """RcloneOutput

    A wrapper for the Rclone command outputs, to ease access.
    """

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
            self.config = config

        # All ls (except lsf) commands are done in terms of lsjson with flags
        # added to make their behaviour consistent with the normal command.
        # This is because parsing the JSON is much easier. However, this can be
        # disabled by setting self.json_by_default to False.
        self.json_by_default: bool = True

        # When in dry run mode, all commands are ran with "--dry-run" added to
        # their arguments to prevent any accidents.
        self.dry_run_mode: bool = False

        # When in verbose mode, all commands are ran with "-vvv".
        self.verbose_mode: bool = False

    def listremotes(self) -> List[str]:
        """listremotes

        Return the defined remotes for the rclone config. This function
        doesn't wrap the rclone command, and instead just returns the remotes
        defined in the config file that was loaded.
        """

        return [f"{remote.name}:" for remote in self.config.remotes]

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
                communication_output: Tuple[bytes, bytes] = rclone_process.communicate()

                output: str = communication_output[0].decode("utf-8")
                error: str = communication_output[1].decode("utf-8")
                self.logger.debug(f"Command returned {output}")

                if error:
                    self.logger.warning(error.replace("\\n", "\n"))

                return RcloneOutput(
                    RcloneError(rclone_process.returncode),
                    output.splitlines(),
                    error.splitlines(),
                )
        except FileNotFoundError as file_missing:
            self.logger.exception(f"Can't find rclone executable. {file_missing}")
            return RcloneOutput(RcloneError.RCLONE_MISSING, [""], [""])
        except Exception as exception:
            self.logger.exception(
                f"Exception running {command_to_run}. Exception: {exception}"
            )
            return RcloneOutput(RcloneError.PYTHON_EXCEPTION, [""], [""])

    def command(self, command: str, arguments: Iterable[str] = tuple()) -> RcloneOutput:
        """command

        Run a given command in the correct mode.
        When in dry run mode, all commands are ran as trials.
        """

        if self.dry_run_mode:
            return self.dry_run_command(command, arguments)

        return self.run_command(command, arguments)

    def run_command(
        self, command: str, arguments: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """run_command

        Run a given command.

        This will add on the associated rclone parts (ie, "rclone", "--conf XXXX")
        """

        if self.dry_run_mode and "--dry-run" not in arguments:
            self.logger.warning("Attempted to run non-trial command in dry-run mode.")
            return RcloneOutput(RcloneError.PYTHON_EXCEPTION, [""], [""])

        full_command: List[str] = ["rclone", command]
        full_command += arguments

        if self.verbose_mode and "-vvv" not in full_command:
            full_command += ["-vvv"]

        return self._execute(full_command)

    def dry_run_command(
        self, command: str, arguments: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """dry_run_command

        Run a given command in dry run mode, ie a trial mode with no actual changes.
        """

        return self.run_command(command, ["--dry-run"] + list(arguments))

    def lsjson(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """lsjson

        Wrap the rclone lsjson command.
        """
        return self.command("lsjson", [remote] + list(flags) + ["--fast-list"])

    def ls(  # pylint: disable=C0103
        self, remote: str, flags: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """ls

        Wrap the rclone ls command.
        """

        if self.json_by_default:
            return self.lsjson(remote, ["-R"] + list(flags))

        return self.command("ls", [remote] + list(flags))

    @staticmethod
    def _filter_json(command_output: RcloneOutput, only_folders: bool) -> RcloneOutput:
        """_filter_json

        Helper to remove either files or folders from a given output.

        If only_folders is set, then only folders are kept.
        Otherwise, only files are kept.
        """

        filtered_output: List[str] = []

        output_line: str
        for output_line in command_output.output:

            if only_folders and '"IsDir":false' in output_line:
                continue

            if not only_folders and '"IsDir":true' in output_line:
                continue

            filtered_output.append(output_line)

        command_output.output = filtered_output

        return command_output

    def lsd(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """lsd

        Wrap the rclone lsd command.
        """
        if self.json_by_default:
            command_output: RcloneOutput = self.lsjson(remote, flags)
            return self._filter_json(command_output, True)

        return self.command("lsd", [remote] + list(flags))

    def lsl(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """lsl

        Wrap the rclone lsl command.
        """

        if self.json_by_default:
            command_output: RcloneOutput = self.lsjson(remote, ["-R"] + list(flags))
            return self._filter_json(command_output, False)

        return self.command("lsl", [remote] + list(flags))

    def lsf(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """lsf

        Wrap the rclone lsf command.
        """
        return self.command("lsf", [remote] + list(flags))

    def delete(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """delete

        Wrap the rclone delete command.
        """
        return self.command("delete", [remote] + list(flags))

    def deletefile(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """deletefile

        Wrap the rclone deletefile command.
        """
        return self.command("deletefile", [remote] + list(flags))

    def purge(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """purge

        Wrap the rclone purge command.
        """
        return self.command("purge", [remote] + list(flags))

    def mkdir(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """mkdir

        Wrap the rclone mkdir command.
        """
        return self.command("mkdir", [remote] + list(flags))

    def size(self, remote: str, flags: Iterable[str] = tuple()) -> RcloneOutput:
        """size

        Wrap the rclone size command.
        """
        return self.command("size", [remote] + list(flags))

    def sync(
        self, local: str, remote: str, flags: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """sync

        Wrap the rclone sync command.
        """
        return self.command("sync", [local] + [remote] + list(flags))

    def copy(
        self, local: str, remote: str, flags: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """copy

        Wrap the rclone copy command.
        """
        return self.command("copy", [local] + [remote] + list(flags))

    def move(
        self, local: str, remote: str, flags: Iterable[str] = tuple()
    ) -> RcloneOutput:
        """move

        Wrap the rclone move command.
        """
        return self.command("move", [local] + [remote] + list(flags))

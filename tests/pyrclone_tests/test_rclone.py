from __future__ import annotations

import unittest
from unittest import mock
from typing import List, Tuple

from pyrclone import Rclone, RcloneConfig, RcloneError, RcloneOutput

BYTE_OUTPUT: List[bytes] = [
    b"[\n",
    b'{"Path":"Test1.txt","Name":"Test1.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},\n',
    b'{"Path":"TestFolder","Name":"TestFolder","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},\n',
    b'{"Path":"TestFolder2","Name":"TestFolder2","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},\n',
    b'{"Path":"TestFolder2/Test3.txt","Name":"Test3.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},\n',
    b'{"Path":"TestFolder/Test2.txt","Name":"Test2.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false}\n',
    b"]\n",
]

STRING_OUTPUT: List[str] = [
    "[",
    '{"Path":"Test1.txt","Name":"Test1.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},',
    '{"Path":"TestFolder","Name":"TestFolder","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},',
    '{"Path":"TestFolder2","Name":"TestFolder2","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},',
    '{"Path":"TestFolder2/Test3.txt","Name":"Test3.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},',
    '{"Path":"TestFolder/Test2.txt","Name":"Test2.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false}',
    "]",
]


class rcloneMockProcess:
    def __init__(
        self, command: List[str], output: bytes, error: bytes, returncode: int
    ) -> None:
        self.command: List[str] = command

        self.output: bytes = output
        self.error: bytes = error
        self.returncode: int = returncode

    def communicate(self) -> Tuple[bytes, bytes]:
        return (self.output, self.error)

    def __enter__(self) -> rcloneMockProcess:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        pass


class rcloneTest(unittest.TestCase):
    """
    Tests for the functions in the pyrclone module.
    """

    def setUp(self) -> None:
        default_config: RcloneConfig = RcloneConfig(
            """[local]
            type = local
            nounc = true
            """
        )

        self.rclone: Rclone = Rclone(default_config)

        self.mock_return: bytes = b"".join(BYTE_OUTPUT)
        self.mock_error: bytes = b""
        self.returncode: int = 0

        self.last_mock_process: rcloneMockProcess = rcloneMockProcess([""], b"", b"", 0)

    def process_mock(
        self, command: List[str], stdout: int, stderr: int
    ) -> rcloneMockProcess:
        mock_process: rcloneMockProcess = rcloneMockProcess(
            command, self.mock_return, self.mock_error, self.returncode
        )
        self.last_mock_process = mock_process
        return mock_process

    def test_listremotes(self) -> None:
        result: List[str] = self.rclone.listremotes()

        assert result == ["local:"]

    def test_ls(self) -> None:
        with mock.patch("subprocess.Popen", self.process_mock):
            result: RcloneOutput = self.rclone.ls("dropbox:")

        expected_result: RcloneOutput = RcloneOutput(
            RcloneError.SUCCESS, STRING_OUTPUT, []
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == ["rclone", "lsjson", "dropbox:", "-R"]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_lsd(self) -> None:
        with mock.patch("subprocess.Popen", self.process_mock):
            result: RcloneOutput = self.rclone.lsd("dropbox:")

        expected_result: RcloneOutput = RcloneOutput(
            RcloneError.SUCCESS, [STRING_OUTPUT[i] for i in [0, 2, 3, -1]], []
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == ["rclone", "lsjson", "dropbox:"]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_lsl(self) -> None:
        with mock.patch("subprocess.Popen", self.process_mock):
            result: RcloneOutput = self.rclone.lsl("dropbox:")

        expected_result: RcloneOutput = RcloneOutput(
            RcloneError.SUCCESS, [STRING_OUTPUT[i] for i in [0, 1, 4, 5, -1]], []
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == ["rclone", "lsjson", "dropbox:", "-R"]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_lsf(self) -> None:
        self.mock_return = b"Test1.txt\nTestFolder/\nTestFolder2/\n"

        with mock.patch("subprocess.Popen", self.process_mock):
            result: RcloneOutput = self.rclone.lsf("dropbox:")

        output_result: List[str] = ["Test1.txt", "TestFolder/", "TestFolder2/"]
        expected_result: RcloneOutput = RcloneOutput(
            RcloneError.SUCCESS, output_result, []
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == ["rclone", "lsf", "dropbox:"]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_delete(self) -> None:
        self.mock_return = b""
        self.mock_error = (
            b"2019/01/13 20:03:41 NOTICE: Test1.txt: Not deleting as --dry-run\n"
        )

        # Test first in dry run mode
        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = True
            result: RcloneOutput = self.rclone.delete("dropbox:Test1.txt")

        output_result: List[str] = ["Test1.txt", "TestFolder/", "TestFolder2/"]
        expected_result: RcloneOutput = RcloneOutput(
            RcloneError.SUCCESS,
            [],
            ["2019/01/13 20:03:41 NOTICE: Test1.txt: Not deleting as --dry-run"],
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "delete",
            "--dry-run",
            "dropbox:Test1.txt",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.delete("dropbox:Test1.txt")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "delete",
            "dropbox:Test1.txt",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_deletefile(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.deletefile("dropbox:Test1.txt")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "deletefile",
            "dropbox:Test1.txt",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_purge(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.purge("dropbox:TestFolder")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "purge",
            "dropbox:TestFolder",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_mkdir(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.mkdir("dropbox:TestFolderNew")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "mkdir",
            "dropbox:TestFolderNew",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_size(self) -> None:
        self.mock_return = b"Total objects: 3\nTotal size: 0 Bytes (0 Bytes)\n"
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.size("dropbox:TestFolder")

        expected_result = RcloneOutput(
            RcloneError.SUCCESS,
            ["Total objects: 3", "Total size: 0 Bytes (0 Bytes)"],
            [],
        )

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "size",
            "dropbox:TestFolder",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_sync(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.sync("dropbox:Test1/", "dropbox:Test2/")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "sync",
            "dropbox:Test1/",
            "dropbox:Test2/",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_copy(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.copy("dropbox:Test1.txt", "dropbox:TestFolder/")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "copy",
            "dropbox:Test1.txt",
            "dropbox:TestFolder/",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

    def test_move(self) -> None:
        self.mock_return = b""
        self.mock_error = b""

        with mock.patch("subprocess.Popen", self.process_mock):
            self.rclone.dry_run_mode = False
            result = self.rclone.move("dropbox:TestFolder", "dropbox:TestFolderNew")

        expected_result = RcloneOutput(RcloneError.SUCCESS, [], [])

        # Assert is split so in the case of a failure, its easier to see.
        assert self.last_mock_process.command == [
            "rclone",
            "move",
            "dropbox:TestFolder",
            "dropbox:TestFolderNew",
        ]
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

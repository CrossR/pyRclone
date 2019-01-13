from __future__ import annotations

import unittest
from unittest import mock
from typing import List, Tuple

from pyrclone import Rclone, RcloneConfig, RcloneError, RcloneOutput


class rcloneMockProcess:
    def __init__(self, command: str) -> None:
        self.command: str = command

        self.output: bytes = b""
        self.error: bytes = b""
        self.returncode: int = 0

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

    def test_listremotes(self) -> None:
        result: List[str] = self.rclone.listremotes()

        assert result == ["local:"]

    def test_ls(self) -> None:
        def ls_mock(command: str, stdout: int, stderr: int) -> rcloneMockProcess:
            mock_process: rcloneMockProcess = rcloneMockProcess(command)
            mock_process.output = (
                b"[\n"
                + b'{"Path":"Test1.txt","Name":"Test1.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},\n'
                + b'{"Path":"TestFolder","Name":"TestFolder","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},\n'
                + b'{"Path":"TestFolder2","Name":"TestFolder2","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},\n'
                + b'{"Path":"TestFolder2/Test3.txt","Name":"Test3.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},\n'
                + b'{"Path":"TestFolder/Test2.txt","Name":"Test2.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false}\n'
                + b"]\n"
            )
            return mock_process

        with mock.patch("subprocess.Popen", ls_mock):
            result: RcloneOutput = self.rclone.ls("dropbox:")

        expected_output: List[str] = [
            "[",
            '{"Path":"Test1.txt","Name":"Test1.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},',
            '{"Path":"TestFolder","Name":"TestFolder","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},',
            '{"Path":"TestFolder2","Name":"TestFolder2","Size":-1,"ModTime":"2019-01-13T17:55:33.8053678Z","IsDir":true},',
            '{"Path":"TestFolder2/Test3.txt","Name":"Test3.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false},',
            '{"Path":"TestFolder/Test2.txt","Name":"Test2.txt","Size":0,"ModTime":"2019-01-13T17:41:00Z","IsDir":false}',
            "]",
        ]
        expected_result: RcloneOutput = RcloneOutput(RcloneError.SUCCESS, expected_output, [])

        # Assert is split so in the case of a failure, its easier to see.
        assert result.error == expected_result.error
        assert result.output == expected_result.output
        assert result.return_code == expected_result.return_code

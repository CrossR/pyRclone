# pylint: disable=all
from pyrclone import Rclone

DEBUG_PARSER: Rclone = Rclone()
REMOTES = DEBUG_PARSER.listremotes()
TEST_OUTPUT = DEBUG_PARSER.lsl("dropbox:Photos")

print(TEST_OUTPUT)

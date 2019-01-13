from pyRclone import Rclone

DEBUG_PARSER: Rclone = Rclone()
COMMAND_TO_RUN = ["rclone", "lsd", "drive:"]
TEST_OUTPUT = DEBUG_PARSER._execute(COMMAND_TO_RUN)

print(TEST_OUTPUT)
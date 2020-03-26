# pyRclone

A typed rClone interface for python.

Written to more easily express awkward logic, that would be a pain or not
(easily) possible on the command line.

A short example, to tidy up and half the number of backups is shown below.
The logic can be trivially expanded to instead say, parse the time stamp of
the backup out of the folder name, to allow different logic to be applied
depending on the age of a backup (do nothing if 1 month old, half is 2 months
old, remove every other after a year old etc).

```py
import json
import logging
import os
import sys

from pyrclone import Rclone, RcloneError


def main():

    # Setup rclone runner, and have it run in verbose and dry run mode.
    rclone: Rclone = Rclone()
    rclone.verbose_mode = True
    rclone.dry_run_mode = True

    # Attach a logger, for more immediate output, rather than just on command completion.
    rclone.logger.setLevel(logging.DEBUG)
    handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    rclone.logger.addHandler(handler)

    # List all folders in backup directory to iterate over them.
    remote_path: str = "drive:PC/Backups"
    output = rclone.lsd(remote_path)

    # If we failed to run, stop.
    if output.return_code is not RcloneError.SUCCESS:
        print(output.error)
        return

    # lsd (and all other ls commands) will default to using lsjson.
    # Lets decode the JSON, and get a list of all our folders.
    backup_folders = []
    for folder in json.loads("".join(files)):
        backup_folders.append(f"{remote_path}/{folder['Path']}")

    # With our list of folders, lets delete every other folder, excluding these
    # useful ones.
    #
    # This could also be more indepth logic, such as using the modified timestamp
    # or the timestamp in the folder name to do logic to different backups of
    # varying age. This is allows the ease of scripting in Python to help, versus
    # confusing/verbose command line options and shell scripts.
    ignore_list = [
        "drive:PC/Backups/2017-09-18_WindowsUpdate",
        "drive:PC/Backups/2019-07-30_FlatMove",
        "drive:PC/Backups/2019-08-12_HDD-Swap",
    ]

    # Iterate over every other folder and delete if not in the ignore.
    #
    # Of course, right now we are in dry_run mode, so this won't do anything
    # except list what it would have done.
    for folder in backup_folders[1::2]:
        if folder in ignore_list:
            continue
        rclone.delete(folder)


if __name__ == "__main__":
    main()

```
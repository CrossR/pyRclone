import logging
import subprocess
from typing import List, Optional

from .RcloneConfig import RcloneConfig

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

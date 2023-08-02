# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import logging
import os
from datetime import datetime


def init_logger(
    log_folder: str = "./log", log_level: str = "INFO",
):
    if not os.path.isdir(log_folder):
        os.makedirs(log_folder, exist_ok=True)

    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-5.5s] %(message)s"
    )
    root_logger = logging.getLogger()
    if (root_logger.hasHandlers()):
        return

    file_handler = logging.FileHandler(
        f"{log_folder}/{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    if log_level.upper() == "DEBUG":
        root_logger.setLevel(logging.DEBUG)
    elif log_level.upper() == "INFO":
        root_logger.setLevel(logging.INFO)
    elif log_level.upper() == "WARNING":
        root_logger.setLevel(logging.WARNING)
    elif log_level.upper() == "ERROR":
        root_logger.setLevel(logging.ERROR)
    elif log_level.upper() == "CRITICAL":
        root_logger.setLevel(logging.CRITICAL)
    else:
        root_logger.setLevel(logging.INFO)
        root_logger.warning(
            f"Invalid log level '{log_level}', using INFO level instead.")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

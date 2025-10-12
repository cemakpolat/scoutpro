"""
@author: Cem Akpolat
@created by cemakpolat at 2021-12-29
"""

import sys
sys.path.append("..") # Adds higher directory to python modules path.

from src.utils.Utils import Logger
from src.restapi.restapi import mainAPI

logger = Logger(__name__).get_logger()

if __name__ == "__main__":
    logger.info("Opta Backend Service is started...")
    mainAPI.run()

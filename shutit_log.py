#!/usr/bin/env python

import logging

def setup(log_level = logging.WARNING, log_file=None):
    """
    Setup logging format and level for the whole project.

    @param log_level:   only messages with a severity equal or higher than this will be logged
                        default: logging.WARNING
    @param log_file:    name of the file to log to
    """
    log_format = '%(asctime)s [%(levelname)-8s] %(module)s:%(funcName)s | %(msg)s'
    logging.basicConfig(format = log_format, level = log_level, filename = log_file)
    logging.debug("logging configured")

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module provides functions for printing and handling diagnostic output, like exceptions.
"""

import linecache
import sys


def print_exception():
    """
    Informative exception handler
    """
    _, exc_obj, traceback = sys.exc_info()
    frame = traceback.tb_frame
    lineno = traceback.tb_lineno
    filename = frame.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, frame.f_globals)
    print(f'EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}')

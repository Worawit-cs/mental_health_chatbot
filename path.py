"""
How to use?  ==>
                import os
                from ..path import get_path
                BASE_DIR,PATH = get_path()
                DATA_PATH = os.path.join(BASE_DIR, PATH["DATA_PATH"])
                RAW_DATA_PATH = os.path.join(BASE_DIR, PATH["RAW_DATA_PATH"])
in file ==>
    {
        "DATA_PATH":"data/",
        "RAW_DATA_PATH":"raw_data",
        "BACKEND_PATH":"backend",
        "FRONT_PATH":"front_end",
        "PDF_SOURCE":"raw_data/source"
    }
"""

import os
import json

def get_path():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, "PATH.json")) as f:
        PATH = json.load(f)
    return BASE_DIR,PATH


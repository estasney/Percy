import os
import glob

def fetch_tmp_files(d):
    file_pattern = "*.json"
    file_pattern = os.path.join(d, file_pattern)
    file_list = glob.glob(file_pattern)
    return file_list

import os
import glob


def make_tmp_dirs(d_list):
    for d in d_list:
        if not os.path.isdir(d):
            os.mkdir(d)
        else:
            existing_files = glob.glob(os.path.join(d, "*.json"))
            for f in existing_files:
                f = os.path.join(d, f)
                if os.path.isfile(f):
                    os.remove(f)


def fetch_tmp_files(d):
    file_pattern = "*.json"
    file_pattern = os.path.join(d, file_pattern)
    file_list = glob.glob(file_pattern)
    return file_list

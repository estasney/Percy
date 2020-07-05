import os
import glob
from flask import current_app


class Packer(object):

    def __init__(self, app=None):
        self.app = app
        self.static_folder = None
        self.cache_assets = True
        self.asset_manifest = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        self.static_folder = app.static_folder
        app.add_template_global(self.asset_url_for)

        if app.config.get('DEBUG', False):
            self.cache_assets = False

    def _file_search(self, path, filename, file_ext):

        # check if this file is present as-is
        filename_ext = filename + file_ext

        straight_string = os.path.join(path, filename_ext)
        if os.path.isfile(straight_string):
            return filename_ext

        del filename_ext, straight_string
        filename_glob_ext = "{}*{}".format(filename, file_ext)
        glob_str = os.path.join(path, filename_glob_ext)
        matched_contents = glob.glob(glob_str)
        if not matched_contents:
            return None
        elif len(matched_contents) == 1:
            matched = matched_contents[0]
            matched = os.path.split(matched)[1]
            return matched
        else:
            matched = sorted(matched_contents, key=lambda x: os.path.getmtime(x), reverse=True)[0]
            matched = os.path.split(matched)[1]
            return matched

    def asset_url_for(self, folder, filename):

        if self.cache_assets and filename in self.asset_manifest:
            return self.asset_manifest[filename]

        pieces = filename.split("/")
        path = pieces[:-1]
        file = pieces[-1]

        filename, file_ext = os.path.splitext(file)

        os_path = os.sep.join(path)
        abs_path = os.path.join(self.static_folder, os_path)

        found_file_name = self._file_search(path=abs_path, filename=filename, file_ext=file_ext)
        # file.ext

        if not found_file_name:
            return "/{}/{}".format(folder, "/".join(pieces))

        result = "/{}/{}/{}".format(folder, "/".join(path), found_file_name)

        if self.cache_assets:
            self.asset_manifest[filename] = result

        return result

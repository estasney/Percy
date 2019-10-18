import os
from flask import current_app


class Packer(object):

    def __init__(self, app=None):
        self.app = app
        self.app_static_folder = None
        self.static_pack_files = None
        self.asset_manifest = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        self.app_static_folder = app.static_folder
        self._set_asset_paths(app)

        app.add_template_global(self.asset_url_for)

        if app.config.get('DEBUG', False):
            app.before_request(self._refresh_asset_paths)

    def _file_search(self, f):
        path, file = os.path.split(f)
        filename, file_ext = os.path.splitext(file)
        path_contents = os.listdir(path)

        # match on file extension
        matched_contents = [file for file in path_contents if file.endswith(file_ext)]

        # files should follow this pattern
        # filename.hash.ext
        for matched_file in matched_contents:
            if matched_file == file:
                # this is not hashed
                return matched_file
            elif matched_file.count(".") == 2:
                name, hash_, ext = matched_file.split(".")
                unhashed_name = "{}.{}".format(name, ext)

                if unhashed_name == file:
                    return matched_file

    def _os_seps(self, file):
        if os.sep == "\\" and "/" in file:
            file = file.replace("/", "\\")
        elif os.sep == "/" and "\\" in file:
            file = file.replace("\\", "/")
        return file

    def _set_asset_paths(self, app):

        # Iterate through static pack files
        # Split path and filename
        # Find matched file
        pack_files = [self._os_seps(f) for f in app.config['STATIC_PACK_FILES']]
        self.static_pack_files = pack_files
        for given_file_name in self.static_pack_files:
            abs_path = os.path.join(app.static_folder, given_file_name)
            found_file_name = self._file_search(abs_path)
            key_name = os.path.split(given_file_name)[1]
            if not found_file_name:
                found_file_name = key_name
            self.asset_manifest[key_name] = found_file_name

    def _refresh_asset_paths(self):
        self._set_asset_paths(current_app)

    def asset_url_for(self, folder, filename):
        pieces = filename.split("/")
        path = pieces[:-1]
        file = pieces[-1]
        if file not in self.asset_manifest:
            result = "/{}/{}".format(folder, "/".join(pieces))
            return result
        hashed_file = self.asset_manifest[file]
        pieces = path + [hashed_file]
        result = "/{}/{}".format(folder, "/".join(pieces))
        return result

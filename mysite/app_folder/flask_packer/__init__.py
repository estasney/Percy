import os
import fnmatch
from pathlib import Path

from flask import current_app, url_for


class Packer(object):

    def __init__(self, app=None):
        self.app = app
        self.static_folder_abs = None
        self.static_folder_name = None
        self.asset_manifest = {}
        self.debug = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        # app.static_folder_abs is an absolute path
        self.static_folder_abs = app.static_folder
        self.static_folder_name = os.path.dirname(app.static_folder)
        self.debug = app.config.get("DEBUG", False)
        app.add_template_global(self.asset_url_for)

    def _build_manifest(self):

        """
        Builds a dictionary where

        {somefile.ext : somefile.hash.ext}

        """
        from flask import current_app
        manifest = {}
        ignored = set(current_app.config.get("PACKER_IGNORE", set([])))

        # We only include path info after the dirname of self.static_folder_abs

        for root_dir, folders, files in os.walk(os.path.join(self.static_folder_abs, "assets")):
            for file in files:
                full_path = os.path.join(root_dir, file)  # full path is used for fnmatch
                if any([fnmatch.fnmatch(full_path, i) for i in ignored]):
                    continue

                # get the relative path from self.static_folder_abs
                root_rel, filename = os.path.split(os.path.relpath(full_path, self.static_folder_abs))

                try:
                    filename, file_hash, *file_ext = filename.split(".")
                except ValueError:
                    continue
                file_ext = ".".join(file_ext)
                common_name = str(Path(os.path.join(root_rel, "{}.{}".format(filename, file_ext))).as_posix())
                if common_name in manifest:  # keep the newest
                    current_app.logger.warning("Duplicate File Matched for {}".format(common_name))
                else:
                    manifest[common_name] = str(Path(os.path.join(root_rel, file)).as_posix())

        if self.debug:
            current_app.logger.info("Built Manifest with {} items".format(len(manifest)))
        self.asset_manifest = manifest

    def asset_url_for(self, folder, filename):
        from flask import current_app
        if not self.asset_manifest:
            self._build_manifest()
        manifest_path = self.asset_manifest.get(filename, filename)
        if manifest_path == filename:
            current_app.logger.info("No hashed asset found for {}".format(filename))
        if self.debug:
            current_app.logger.info("Asset URL For {}, Found {}".format(filename, manifest_path))
        return url_for(folder, filename=manifest_path)

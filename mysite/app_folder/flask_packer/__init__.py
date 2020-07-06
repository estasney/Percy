import os
import fnmatch

from flask import current_app, url_for
import json


class Packer(object):
    MANIFEST_NAME = ".packer_manifest.json"

    def __init__(self, app=None):
        self.app = app
        self.static_folder = None
        self.static_manifest_path = None
        self.asset_manifest = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.static_folder = os.path.basename(app.static_folder)
        self._build_manifest_path()
        app.add_template_global(self.asset_url_for)

    def _build_manifest_path(self):
        self.static_manifest_path = os.path.join(self.static_folder, self.MANIFEST_NAME)

    def _build_manifest(self):
        from flask import current_app
        current_app.logger.info("Build Manifest")
        manifest = {}
        ignored = set(current_app.config.get("PACKER_IGNORE", set([])))
        ignored.add("**/{}".format(Packer.MANIFEST_NAME))
        for root_dir, folders, files in os.walk(self.static_folder):
            root_dir = os.path.relpath(root_dir, "static")
            for file in files:
                full_path = os.path.join(root_dir, file)
                if any([fnmatch.fnmatch(full_path, i) for i in ignored]):
                    continue
                try:
                    filename, file_hash, *file_ext = file.split(".")
                except ValueError:
                    continue
                file_ext = ".".join(file_ext)
                common_name = os.path.join(root_dir, "{}.{}".format(filename, file_ext))
                if common_name in manifest:  # keep the newest
                    selected = max(
                            [manifest[common_name],
                             os.path.join(root_dir, file)],
                            key=lambda x: os.path.getmtime(x))
                    manifest[common_name] = selected
                else:
                    manifest[common_name] = os.path.join(root_dir, file)

        with open(self.static_manifest_path, "w+") as fp:
            json.dump(manifest, fp)
        self.asset_manifest = manifest

    def _load_manifest(self):
        if not self.static_manifest_path:
            self._build_manifest_path()
        if not os.path.isfile(self.static_manifest_path):
            self._build_manifest()
        with open(self.static_manifest_path, "r") as fp:
            self.asset_manifest = json.load(fp)

    def asset_url_for(self, folder, filename):

        if not self.asset_manifest:
            current_app.logger.info("Load Manifest")
            self._load_manifest()
        manifest_path = self.asset_manifest.get(filename, filename)
        current_app.logger.info("Asset URL For {}, Found {}".format(filename, manifest_path))
        return url_for(folder, filename=manifest_path)

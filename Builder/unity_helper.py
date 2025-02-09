import os
import shutil

from common import resolve_path


class UnityHelper:

    @staticmethod
    def list_package_assets(dir_project, ignored_files=None):
        """
        List all package assets in the directory, excluding ignored files.
        """
        if ignored_files is None:
            ignored_files = []

        # Add root directory
        files = [dir_project]

        # List files
        UnityHelper.list_assets(files, dir_project, lambda file: (
            # Exclude ignored files
            False if os.path.basename(file) in ignored_files else
            # Include directories
            True if os.path.isdir(file) else
            # Include the rest
            True
        ))

        return files

    @staticmethod
    def list_assets(result, path, filter_func=None):
        """
        Recursively list assets in the given path, applying a filter function if provided.
        """
        for file in os.listdir(path):
            full_path = resolve_path(os.path.join(path, file))

            # Skip .meta files
            if os.path.isfile(full_path) and full_path.endswith('.meta'):
                continue

            # Apply the filter function, if provided
            accepted = filter_func(full_path) if filter_func else True
            if not accepted:
                continue

            if accepted:
                result.append(full_path)

            # Recurse into directories
            if os.path.isdir(full_path):
                UnityHelper.list_assets(result, full_path, filter_func)

    @staticmethod
    def remove_unity_asset(path):
        """
        Remove a Unity asset and its associated .meta file.
        """
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

        meta_path = f"{path}.meta"
        try:
            os.remove(meta_path)
        except FileNotFoundError:
            pass

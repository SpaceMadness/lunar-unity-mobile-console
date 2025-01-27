import os
import subprocess

from platform import Platform


class UnityProject:

    def __init__(self, dir_project, bin_unity):
        self.dir_project = self.resolve_path(os.path.abspath(dir_project))
        self.bin_unity = self.resolve_path(bin_unity)

    def exec_unity_method(self, method, args=None, error_message=None):
        if args is None:
            args = {}
        self.exec_unity_method_opt(self.dir_project, method, args, {}, error_message)

    def exec_unity_method_opt(self, project, method, args=None, options=None, error_message=None):
        if args is None:
            args = {}
        if options is None:
            options = {}

        cmd = [self.bin_unity]
        if 'no_quit' not in options:
            cmd.append('-quit')
        if 'no_batch' not in options:
            cmd.append('-batchmode')
        if args:
            cmd.append(f'"{self.make_custom_args(args)}"')
        cmd.append(f'-executeMethod {method}')
        cmd.append(f'-projectPath "{project}"')

        self.exec_shell(cmd, error_message or f"Can't execute method: {method}\nProject: {project}")

        unity_log = Platform.unity_log()
        self.fail_script_unless_file_exists(unity_log)

        with open(unity_log, 'r') as file:
            result = file.read()

        if not "Exiting batchmode successfully now!" in result:
            raise RuntimeError(f"Unity batch failed\n{result}")

    def exec_unity(self, project, command, error_message=None):
        self.fail_script_unless_file_exists(project)
        cmd = [self.bin_unity, '-quit', '-batchmode', f'-projectPath "{project}"', command]
        self.exec_shell(cmd, error_message or f"Can't execute unit command: {command}\nProject: {project}")

        unity_log = Platform.unity_log()
        self.fail_script_unless_file_exists(unity_log)

        with open(unity_log, 'r') as file:
            result = file.read()

        if not "Exiting batchmode successfully now!" in result:
            raise RuntimeError(f"Unity batch failed\n{result}")

    def export_unity_package(self, file_output, assets):
        package_assets = [
            self.make_relative_path(file, self.dir_project)
            for file in assets
        ]

        dir_output = os.path.dirname(file_output)
        os.makedirs(dir_output, exist_ok=True)

        args = {
            'output': file_output,
            'assets': ','.join(package_assets)
        }

        self.exec_unity_method('LunarConsoleEditorInternal.PackageExporter.ExportUnityPackage', args, f"Can't export Unity package: {file_output}")

    def import_package(self, file_package):
        self.fail_script_unless_file_exists(file_package)
        self.exec_unity(self.dir_project, f'-importPackage "{file_package}"', f"Can't import unity package: {file_package}")

    def open(self, error_message=None):
        cmd = [self.bin_unity, f'-projectPath "{self.dir_project}"']
        self.exec_shell(cmd, error_message or f"Can't open Unity project: {self.dir_project}")

    @staticmethod
    def make_custom_args(args):
        if args:
            pairs = [f"{name}={value}" for name, value in args.items()]
            return f"-customArgs?{'&'.join(pairs)}"

    @staticmethod
    def resolve_path(path):
        return os.path.realpath(path)

    @staticmethod
    def exec_shell(cmd, error_message):
        try:
            subprocess.run(cmd, check=True, shell=True)
        except subprocess.CalledProcessError:
            raise RuntimeError(error_message)

    @staticmethod
    def fail_script_unless_file_exists(file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Required file not found: {file_path}")

    @staticmethod
    def make_relative_path(file_path, base_path):
        return os.path.relpath(file_path, base_path)

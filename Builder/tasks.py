import glob
import re
from os.path import abspath
from pathlib import Path

from invoke import task
import os
import shutil
import json

from common import resolve_path, not_nil, print_header, exec_shell, list_files
from platform import Platform
from unity_helper import UnityHelper
from unity_project import UnityProject

# Define global variables
dir_out = None
dir_out_packages = None
dir_builder = None
dir_utils = None
dir_repo = None
bin_unity_export = None
bin_unity_publish = None
dir_project = None
dir_project_plugin = None
dir_project_plugin_scripts = None
dir_project_plugin_editor = None
dir_project_plugin_ios = None
dir_project_plugin_android = None
dir_native = None
dir_native_ios = None
dir_native_ios_src = None
dir_native_android = None
dir_native_android_src = None
dir_native_ios_images_root = None
dir_native_android_images_root = None
dir_test_project = None
package_version = None
package_files = None
package_config = None


@task
def init(c):
    global dir_out, dir_out_packages, dir_builder, dir_utils, dir_repo
    global bin_unity_export, bin_unity_publish
    global dir_project, dir_project_plugin, dir_project_plugin_scripts
    global dir_project_plugin_editor, dir_project_plugin_ios, dir_project_plugin_android
    global dir_native, dir_native_ios, dir_native_ios_src, dir_native_android, dir_native_android_src
    global dir_native_ios_images_root, dir_native_android_images_root, dir_test_project, package_version

    dir_out = abspath("temp")
    dir_out_packages = abspath(f"{dir_out}/packages")
    dir_builder = resolve_path(".")
    dir_utils = resolve_path(f"{dir_builder}/utils")
    dir_repo = resolve_path(os.path.abspath(".."))

    # Define Unity-related paths
    bin_unity_export = resolve_path(Platform.unity_export())
    bin_unity_publish = resolve_path(Platform.unity_publish())

    # Plugin project paths
    dir_project = resolve_path(os.path.abspath("../Project"))
    dir_project_plugin = resolve_path(f"{dir_project}/Assets/LunarConsole")
    dir_project_plugin_scripts = resolve_path(f"{dir_project_plugin}/Scripts")
    dir_project_plugin_editor = resolve_path(f"{dir_project_plugin}/Editor")
    dir_project_plugin_ios = f"{dir_project_plugin_editor}/iOS"
    dir_project_plugin_android = f"{dir_project_plugin_editor}/Android"

    # Native project paths
    dir_native = resolve_path(os.path.abspath("../Native"))
    dir_native_ios = resolve_path(f"{dir_native}/iOS")
    dir_native_ios_src = resolve_path(f"{dir_native_ios}/LunarConsole/LunarConsole")
    dir_native_android = resolve_path(f"{dir_native}/Android")
    dir_native_android_src = resolve_path(f"{dir_native_android}/LunarConsole")
    dir_native_ios_images_root = resolve_path(dir_native_ios_src)
    dir_native_android_images_root = resolve_path(f"{dir_native_android_src}/lunarConsole/src/main/res")
    dir_test_project = resolve_path("TestProject")
    package_version = not_nil(extract_package_version(dir_project_plugin))


@task(pre=[init])
def clean(c):
    shutil.rmtree(dir_out, ignore_errors=True)
    os.makedirs(dir_out, exist_ok=True)


@task(pre=[init])
def full(ctx):
    global package_config
    package_config = "Full"


@task(pre=[init])
def free(ctx):
    global package_config
    package_config = "Free"


@task(pre=[init])
def build_native_ios(c):
    # List iOS project files
    ios_files = list_ios_files(dir_native_ios_src,
                               configuration=package_config,
                               use_relative_path=True)

    # Cleanup old files
    if os.path.exists(dir_project_plugin_ios):
        shutil.rmtree(dir_project_plugin_ios)
    os.makedirs(dir_project_plugin_ios, exist_ok=True)

    # Copy files to plugin native folder (keeping directory structure)
    for file in ios_files:
        file_src = os.path.join(dir_native_ios_src, file)
        dir_dest = os.path.join(dir_project_plugin_ios, os.path.dirname(file))
        os.makedirs(dir_dest, exist_ok=True)

        shutil.copy(file_src, os.path.join(dir_dest, os.path.basename(file)))

    # Generate .projmod
    projmods = {
        "group": "Lunar Console",
        "frameworks": ["MessageUI.framework"],
        "files": ios_files,
        "excludes": [
            r"^.*\.DS_Store$",
            r"^.*\.meta$",
            r"^.*\.mdown$",
            r"^.*\.pdf$",
            r"^.*\.svn$"
        ],
    }

    file_projmode = os.path.join(dir_project_plugin_ios, "Lunar.projmods")
    with open(file_projmode, "w") as f:
        json.dump(projmods, f, indent=4)


@task(pre=[init])
def build_native_android(ctx):
    # Clean up files.
    shutil.rmtree(dir_project_plugin_android, ignore_errors=True)
    os.makedirs(dir_project_plugin_android, exist_ok=True)

    # Build Android library.
    build_android_plugin(dir_native_android_src, "lunarConsole", package_config, dir_project_plugin_android)


@task(pre=[init, build_native_ios, build_native_android])
def build_native(ctx):
    pass


@task(pre=[full, build_native])
def build_native_full(ctx):
    pass


@task(pre=[free, build_native])
def build_native_free(ctx):
    pass


@task(pre=[init])
def list_package_files(ctx):
    global package_files
    package_files = UnityHelper.list_package_assets(dir_project_plugin)

    print_header("Package files:")
    print(package_files)


@task(pre=[init, build_native, list_package_files])
def export_package(ctx):
    import os

    file_package = f"{dir_out_packages}/lunar-console-{package_config.lower()}-{package_version}.unitypackage"
    print(f"Exporting package: {file_package}...")

    override_configuration_define(resolve_path(os.path.join(dir_project_plugin, "Scripts/LunarConsole.cs")),
                                  package_config)

    if not package_files:
        raise ValueError("PACKAGE_FILES is not set")

    project = UnityProject(dir_project, bin_unity_export)
    project.export_unity_package(file_package, package_files)


@task(pre=[clean, free, export_package])
def export_unity_package_free(c):
    pass


@task(pre=[clean, full, export_package])
def export_unity_package_full(c):
    pass


@task(pre=[clean, export_unity_package_free, export_unity_package_full])
def export_unity_packages(c):
    """Export unity packages"""
    print("All Unity packages exported.")


@task(pre=[build_native_android])
def build_run_native_android(c):
    project = UnityProject(dir_project, bin_unity_export)
    project.exec_unity_method("LunarConsoleEditorInternal.AndroidPlugin.ForceUpdateFiles")
    project.exec_unity_method("LunarConsoleEditorInternal.AppExporter.PerformAndroidBuild")

    apk_path = resolve_path(glob.glob(f"{dir_project}/Build/Android/*.apk")[0])

    print("Installing app...")
    exec_shell(f'adb install -r "{apk_path}"', "Can't install app...")

    print("Starting app...")
    exec_shell(
        'adb shell am start -n com.spacemadness.LunarConsoleTest/com.unity3d.player.UnityPlayerActivity',
        "Can't start app"
    )


@task(pre=[full, build_run_native_android])
def build_run_native_android_full(c):
    pass


@task(pre=[free, build_run_native_android])
def build_run_native_android_free(c):
    pass


@task
def optimize_png_files(c):
    """Optimize PNG files."""
    files = []
    files.extend(list_png_files(dir_native_ios_images_root))
    files.extend(list_png_files(dir_native_android_images_root))

    bin_pngout = resolve_path(f"{dir_utils}/pngout")

    size_before = 0.0
    size_after = 0.0

    for file in files:
        size_before += os.path.getsize(file)
        exec_shell(f'"{bin_pngout}" "{file}" -c3 -y -force', f"Can't optimize png: {file}")
        size_after += os.path.getsize(file)

    print_header(f"Compression rate: {100 * (size_after / size_before):.2f}% ({size_after}/{size_before})")


def list_png_files(dir_project):
    def is_png(file):
        if os.path.isdir(file):
            return False
        return os.path.splitext(file)[1] == '.png'

    return list(filter(is_png, list_files(dir_project)))


def list_ios_files(dir_project, **kwargs):
    extensions = ['.h', '.m', '.mm', '.xib', '.nib', '.c', '.cpp', '.png', '.bundle']
    configuration = kwargs.get('configuration')

    def is_valid_file(file):
        if os.path.isdir(file):
            return False
        if '/Full/' in file and configuration == 'Free':
            return False
        if '/Free/' in file and configuration == 'Full':
            return False
        return os.path.splitext(file)[1] in extensions

    files = list(filter(is_valid_file, list_files(dir_project)))

    if kwargs.get('use_relative_path'):
        return [os.path.relpath(file, dir_project) for file in files]

    return files


def build_android_plugin(dir_native_project, module_name, flavour, dir_android_plugin):
    print_header('Building Android library...')
    file_aar = build_android(dir_native_project, module_name, flavour)

    print_header('Preparing Android plugin')
    shutil.copy(file_aar, os.path.join(dir_android_plugin, 'lunar-console.aar'))


def build_android(dir_project, module_name, flavour, config='Release'):
    original_dir = os.getcwd()
    os.chdir(dir_project)

    print(dir_project)
    bin = './gradlew' if Platform.is_mac_os() else 'gradlew.bat'

    try:
        command = f"{bin} :{module_name}:clean :{module_name}:assemble{flavour}{config}"
        exec_shell(command, "Can't build Android aar")
        aar_path = os.path.join(module_name, 'build', 'outputs', 'aar',
                                f"{module_name}-{flavour.lower()}-{config.lower()}.aar")
        return resolve_path(abspath(aar_path))
    finally:
        os.chdir(original_dir)


def write_project_properties(file, properties):
    with open(file, 'w') as f:
        for name, value in properties.items():
            f.write(f"{name}={value}\n")


def override_configuration_define(file_script, configuration):
    with open(file_script, 'r') as f:
        source = f.read()

    if configuration == 'Full':
        source = source.replace('#define LUNAR_CONSOLE_FREE', '#define LUNAR_CONSOLE_FULL')
    elif configuration == 'Free':
        source = source.replace('#define LUNAR_CONSOLE_FULL', '#define LUNAR_CONSOLE_FREE')
    else:
        raise ValueError(f"Unexpected configuration: {configuration}")

    with open(file_script, 'w') as f:
        f.write(source)


def extract_package_version(dir_project):
    file_version = Path(dir_project) / "Scripts" / "Constants.cs"
    source = file_version.read_text()

    match = re.search(r'Version\s+=\s+"(\d+\.\d+\.\d+\w?)"', source)
    return match.group(1) if match else None

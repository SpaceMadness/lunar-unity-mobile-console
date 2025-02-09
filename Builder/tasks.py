import glob
import re
from pathlib import Path
from pprint import pprint

from invoke import task
import os
import shutil
import json

from common import resolve_path, not_nil, not_empty, print_header, exec_shell, list_files
from platform import Platform
from unity_helper import UnityHelper
from unity_project import UnityProject


@task
def _init(c):
    c.dir_out = os.path.abspath("temp")
    c.dir_out_packages = os.path.abspath(f"{c.dir_out}/packages")
    c.dir_builder = resolve_path(".")
    c.dir_utils = resolve_path(f"{c.dir_builder}/utils")
    c.dir_repo = resolve_path(os.path.abspath(".."))

    # Define Unity-related paths
    c.bin_unity_export = resolve_path(Platform.unity_export())
    c.bin_unity_publish = resolve_path(Platform.unity_publish())

    # Plugin project paths
    c.dir_project = resolve_path(os.path.abspath("../Project"))
    c.dir_project_plugin = resolve_path(f"{c.dir_project}/Assets/LunarConsole")
    c.dir_project_plugin_scripts = resolve_path(f"{c.dir_project_plugin}/Scripts")
    c.dir_project_plugin_editor = resolve_path(f"{c.dir_project_plugin}/Editor")
    c.dir_project_plugin_ios = f"{c.dir_project_plugin_editor}/iOS"
    c.dir_project_plugin_android = f"{c.dir_project_plugin_editor}/Android"

    # Native project paths
    c.dir_native = resolve_path(os.path.abspath("../Native"))
    c.dir_native_ios = resolve_path(f"{c.dir_native}/iOS")
    c.dir_native_ios_src = resolve_path(f"{c.dir_native_ios}/LunarConsole/LunarConsole")
    c.dir_native_android = resolve_path(f"{c.dir_native}/Android")
    c.dir_native_android_src = resolve_path(f"{c.dir_native_android}/LunarConsole")
    c.dir_native_ios_images_root = resolve_path(c.dir_native_ios_src)
    c.dir_native_android_images_root = resolve_path(f"{c.dir_native_android_src}/lunarConsole/src/main/res")
    c.dir_test_project = resolve_path("TestProject")
    c.package_version = not_nil(extract_package_version(c.dir_project_plugin))
    c.package_files = None
    c.package_config = None


@task(pre=[_init])
def clean(c):
    dir_out = not_empty(c.dir_out)

    shutil.rmtree(dir_out, ignore_errors=True)
    os.makedirs(dir_out, exist_ok=True)


@task(pre=[_init])
def _full(c):
    c.package_config = "Full"


@task(pre=[_init])
def _free(c):
    c.package_config = "Free"


@task(pre=[_init])
def _build_native_ios(c):
    dir_native_ios_src = not_nil(c.dir_native_ios_src)
    package_config = not_nil(c.package_config)
    dir_project_plugin_ios = not_nil(c.dir_project_plugin_ios)

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


@task(pre=[_init])
def _build_native_android(c):
    dir_project_plugin_android = not_nil(c.dir_project_plugin_android)
    dir_native_android_src = not_nil(c.dir_native_android_src)
    package_config = not_nil(c.package_config)

    # Clean up files.
    shutil.rmtree(dir_project_plugin_android, ignore_errors=True)
    os.makedirs(dir_project_plugin_android, exist_ok=True)

    # Build Android library.
    build_android_plugin(dir_native_android_src, "lunarConsole", package_config, dir_project_plugin_android)


@task(pre=[_init, _build_native_ios, _build_native_android])
def _build_native(c):
    pass


@task(pre=[_init])
def _list_package_files(c):
    dir_project_plugin = not_nil(c.dir_project_plugin)
    c.package_files = _list_package_files_helper(dir_project_plugin)


@task(pre=[_init, _build_native, _list_package_files])
def _export_package(c):
    dir_out_packages = not_empty(c.dir_out_packages)
    package_config = not_nil(c.package_config)
    package_version = not_nil(c.package_version)
    dir_project_plugin = not_nil(c.dir_project_plugin)
    dir_project = not_nil(c.dir_project)
    bin_unity_export = not_nil(c.bin_unity_export)
    package_files = not_empty(c.package_files)

    file_package = os.path.join(dir_out_packages, f"lunar-console-{package_config.lower()}-{package_version}.unitypackage")
    print(f"Exporting package: {file_package}...")

    override_configuration_define(resolve_path(os.path.join(dir_project_plugin, "Scripts/LunarConsole.cs")),
                                  package_config)

    project = UnityProject(dir_project, bin_unity_export)
    project.export_unity_package(file_package, package_files)

    resolve_path(file_package)


@task
def optimize_png_files(c):
    """Optimize PNG files using pngout to reduce file sizes while maintaining quality."""
    dir_native_ios_images_root = not_nil(c.dir_native_ios_images_root)
    dir_native_android_images_root = not_nil(c.dir_native_android_images_root)
    dir_utils = not_nil(c.dir_utils)

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


@task(pre=[_full, _build_native])
def build_native_full(c):
    """Build the full version of native iOS and Android plugins."""
    pass


@task(pre=[_free, _build_native])
def build_native_free(c):
    """Build the free version of native iOS and Android plugins."""
    pass


@task(pre=[clean, _free, _export_package])
def export_unity_package_free(c):
    """Export the free version of the Lunar Console Unity package."""
    pass


@task(pre=[clean, _full, _export_package])
def export_unity_package_full(c):
    """Export the full version of the Lunar Console Unity package."""
    pass


@task(pre=[clean, export_unity_package_free, export_unity_package_full])
def export_unity_packages(c):
    """Export both free and full versions of the Lunar Console Unity packages."""
    print("All Unity packages exported.")


@task(pre=[_build_native_android])
def build_run_native_android(c):
    """Build the Android plugin, create an APK, install and run it on a connected device."""
    dir_project = not_nil(c.dir_project)
    bin_unity_export = not_nil(c.bin_unity_export)

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


@task(pre=[_full, build_run_native_android])
def build_run_native_android_full(c):
    """Build, install and run the full version of the Android test app."""
    pass


@task(pre=[_free, build_run_native_android])
def build_run_native_android_free(c):
    """Build, install and run the free version of the Android test app."""
    pass


# Helper Functions
def _list_package_files_helper(dir_project_plugin):
    """List and print all Unity package assets from the plugin directory."""
    package_files = UnityHelper.list_package_assets(dir_project_plugin)
    print_header("Package files:")
    pprint(package_files)
    return package_files


def list_png_files(dir_project):
    """Find all PNG files in the specified directory."""

    def is_png(file):
        if os.path.isdir(file):
            return False
        return os.path.splitext(file)[1] == '.png'

    return list(filter(is_png, list_files(dir_project)))


def list_ios_files(dir_project, **kwargs):
    """
    List iOS source files with specific extensions (.h, .m, .mm, etc.).
    Filters files based on Free/Full configuration if specified.
    Can return relative paths if use_relative_path=True.
    """
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
    """
    Build Android AAR library and copy it to the Unity plugin directory.
    Handles both free and full flavors of the plugin.
    """
    print_header('Building Android library...')
    file_aar = build_android(dir_native_project, module_name, flavour)

    print_header('Preparing Android plugin')
    shutil.copy(file_aar, os.path.join(dir_android_plugin, 'lunar-console.aar'))


def build_android(dir_project, module_name, flavour, config='Release'):
    """
    Build Android library using Gradle.
    Returns the path to the generated AAR file.
    """
    original_dir = os.getcwd()
    os.chdir(dir_project)

    print(dir_project)
    bin = './gradlew' if Platform.is_mac_os() else 'gradlew.bat'

    try:
        command = f"{bin} :{module_name}:clean :{module_name}:assemble{flavour}{config}"
        exec_shell(command, "Can't build Android aar")
        aar_path = os.path.join(module_name, 'build', 'outputs', 'aar',
                                f"{module_name}-{flavour.lower()}-{config.lower()}.aar")
        return resolve_path(os.path.abspath(aar_path))
    finally:
        os.chdir(original_dir)


def write_project_properties(file, properties):
    """Write key-value pairs to a properties file."""
    with open(file, 'w') as f:
        for name, value in properties.items():
            f.write(f"{name}={value}\n")


def override_configuration_define(file_script, configuration):
    """
    Modify the configuration define in the LunarConsole.cs script.
    Switches between LUNAR_CONSOLE_FREE and LUNAR_CONSOLE_FULL.
    """
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
    """
    Extract package version from Constants.cs file.
    Returns version string in format "X.Y.Z" or with optional suffix.
    """
    file_version = Path(dir_project) / "Scripts" / "Constants.cs"
    source = file_version.read_text()

    match = re.search(r'Version\s+=\s+"(\d+\.\d+\.\d+\w?)"', source)
    return match.group(1) if match else None

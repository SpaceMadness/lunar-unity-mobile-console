import sys
import os

class Platform:
    @staticmethod
    def unity_export():
        if Platform.is_mac_os():
            return '/Applications/Unity-Export/Unity.app/Contents/MacOS/Unity'
        return r'C:\Program Files\Unity-Export\Editor\Unity.exe'

    @staticmethod
    def unity_publish():
        if Platform.is_mac_os():
            return '/Applications/Unity-Publish/Unity.app/Contents/MacOS/Unity'
        return r'C:\Program Files\Unity-Publish\Editor\Unity.exe'

    @staticmethod
    def unity_log():
        if Platform.is_mac_os():
            return os.path.expanduser('~/Library/Logs/Unity/Editor.log')
        return os.path.expanduser('~/AppData/Local/Unity/Editor/Editor.log')

    @staticmethod
    def is_mac_os():
        return sys.platform == 'darwin'

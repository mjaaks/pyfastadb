import subprocess
import os
import time
import shutil

##  PYFASTADB
##  Version 0.1 (alpha)
##  Made by mjaaks
##
##  Simple, yet extensive, python wrapper for adb and fastboot
##
##  @2025

##  // Setup assists //

def find_adb(return_as_bool=False, custom_path=None):
    adb_path = None
    if custom_path is not None:
        if custom_path.lower().endswith("adb.exe") and os.path.isfile(custom_path):
            adb_path = custom_path
        else:
            if os.path.exists(os.path.join(custom_path, "adb.exe")):
                adb_path = os.path.join(custom_path, "adb.exe")
    else:
        adb_path = shutil.which('adb')
    if return_as_bool:
        if adb_path is None:
            return False
        else:
            return True
    return adb_path

def find_fastboot(return_as_bool=False, custom_path=None):
    fastboot_path = None
    if custom_path is not None:
        if custom_path.lower().endswith("fastboot.exe") and os.path.isfile(custom_path):
            fastboot_path = custom_path
        else:
            if os.path.exists(os.path.join(custom_path, "fastboot.exe")):
                fastboot_path = os.path.join(custom_path, "fastboot.exe")
    else:
        fastboot_path = shutil.which('fastboot')
    if return_as_bool:
        if fastboot_path is None:
            return False
        else:
            return True
    return fastboot_path

##  // Error Handling //

class Error(Exception):
    pass

##  // Adb class //

class adb:
    def __init__(self, adb_path=None):
        self._adb_path = adb_path

    def adb_command(self, command):
        res = subprocess.run([self._adb_path, command], capture_output=True, text=True)
        if res.returncode != 0:
            raise Error(res.stderr)
        return res

    def device_adb_command(self, device, command):
        res = subprocess.run([self._adb_path, "-s", device.serial, *command.split()], capture_output=True, text=True)
        if res.returncode != 0:
            raise Error(res.stderr)
        return res

##  // Fastboot class //

class fastboot:
    def __init__(self, fastboot_path=None):
        self._fastboot_path = fastboot_path

    def fastboot_command(self, command):
        res = subprocess.run([self._fastboot_path, command], capture_output=True, text=True)
        if res.returncode != 0:
            raise Error(res.stderr)
        return res

    def device_fastboot_command(self, device, command):
        res = subprocess.run([self._fastboot_path, "-s", device.serial, *command.split()], capture_output=True, text=True)
        if res.returncode != 0:
            raise Error(res.stderr)
        return res

##  // Client Class //

class Client:
    def __init__(self, adb_path=None, fastboot_path=None):
        self._adb_path = adb_path
        self._fastboot_path = fastboot_path
        if find_adb(custom_path=self._adb_path, return_as_bool=True) == False:
            raise Error('adb_path is not a valid path to adb.exe')
        if find_fastboot(custom_path=self._fastboot_path, return_as_bool=True) == False:
            raise Error('fastboot_path is not a valid path to fastboot.exe')
        self.adb = adb(self._adb_path)
        self.fastboot = fastboot(self._fastboot_path)

    ##  // More setup assists //

    def get_adb_devices(self):
        res = self.adb.adb_command("devices")
        res = res.stdout.strip().splitlines()
        dev = []
        for i in res[1:]:
            i = i.split()
            dev.append((i[0], i[1]))
        return dev or None

    def get_fastboot_devices(self):
        res = self.fastboot.fastboot_command("devices")
        res = res.stdout.strip().splitlines()
        dev = []
        for i in res:
            i = i.split()
            dev.append((i[0], i[1]))
        return dev or None

    def start(self):
        self.adb.adb_command("start-server")

    def kill(self):
        self.adb.adb_command("kill-server")

##  // Device Class //

class Device:
    def __init__(self, client, serial):
        self.serial = serial
        self._adb_path = client._adb_path
        self._fastboot_path = client._fastboot_path
        self._client = client
        self.adb = adb(self._adb_path)

    def reboot(self, reboot_type=""):
        self.adb.device_adb_command(self, f"reboot {reboot_type}")

    def wait_for_state(self, state):
        match state:
            case "device": self.adb.device_adb_command(self, "wait-for-device")
            case "recovery": self.adb.device_adb_command(self, "wait-for-recovery")
            case "sideload": self.adb.device_adb_command(self, "wait-for-sideload")
            case "bootloader":
                while True:
                    dev = self._client.get_fastboot_devices() or []
                    for i in dev:
                        if i[0] == self.serial: return
                time.sleep(0.25)
            case _: raise Error("state arg for wait_for_state is invalid")

    def push(self, source, destination):
        self.adb.device_adb_command(self, f"push {source} {destination}")

    def pull(self, source, destination):
        self.adb.device_adb_command(self, f"pull {source} {destination}")
from cx_Freeze import setup, Executable
import sys
import os

build_options = {
    "packages": ["cv2", "psutil", "wmi", "time", "sys", "PyQt5"],
    "excludes": [],
    "include_files": [
        "test.mp4",
        "icon.ico",
        "battery_report.txt"
    ]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        script="main.py",
        base=base,
        target_name="BatteryTestApp.exe",
        icon="icon.ico"
    )
]

setup(
    name="Battery Test",
    version="1.2",
    description="Battery Duration Test - Developed by Yousef Mohamad ",
    author="Yousef Mohamad",
    author_email="yousef.mohamad.abdala@hotmail.com",
    options={"build_exe": build_options},
    executables=executables
)

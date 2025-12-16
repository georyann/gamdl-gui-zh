
# Windows 打包脚本
# 请在 Windows 电脑上安装 Python 后运行此脚本
# pip install pyinstaller
# python build_windows.py

import PyInstaller.__main__
import os
import shutil

print("开始构建 Windows 版本...")

if os.path.exists('dist/Gamdl-GUI-ZH'):
    shutil.rmtree('dist/Gamdl-GUI-ZH')

params = [
    'gui_app.py',
    '--name=Gamdl-GUI-ZH',
    '--windowed',
    '--onedir',
    '--clean',
    '--noconfirm',
    '--distpath=dist/windows'
]

PyInstaller.__main__.run(params)
print("构建完成！请查看 dist/windows 目录")

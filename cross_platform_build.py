#!/usr/bin/env python3
"""
跨平台构建辅助工具
1. 构建 macOS 应用程序
2. 生成 Windows 打包脚本
3. 生成 GitHub Actions 自动化构建配置
"""

import os
import sys
import shutil
import platform

def build_macos():
    """构建 macOS 应用程序"""
    if platform.system() != 'Darwin':
        print("跳过 macOS 构建 (当前不是 macOS 系统)")
        return

    print("\n正在构建 macOS 应用程序...")
    
    # 清理旧文件
    if os.path.exists('dist/Gamdl-GUI-ZH.app'):
        shutil.rmtree('dist/Gamdl-GUI-ZH.app')
        
    import PyInstaller.__main__
    
    params = [
        'gui_app.py',
        '--name=Gamdl-GUI-ZH',
        '--windowed',
        '--onedir',
        '--clean',
        '--noconfirm',
        '--distpath=dist/macos'
    ]
    
    try:
        PyInstaller.__main__.run(params)
        print("✅ macOS 应用程序构建成功！")
        print("文件位置: dist/macos/Gamdl-GUI-ZH.app")
    except Exception as e:
        print(f"❌ macOS 构建失败: {e}")

def create_windows_script():
    """生成 Windows 打包脚本"""
    content = """
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
"""
    with open('build_windows.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\n✅ 已生成 Windows 打包脚本: build_windows.py")

def create_github_workflow():
    """生成 GitHub Actions 配置文件"""
    workflow_dir = '.github/workflows'
    if not os.path.exists(workflow_dir):
        os.makedirs(workflow_dir)
        
    content = """name: Build Gamdl GUI

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]
  workflow_dispatch:

jobs:
  build:
    name: Build for ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller
        pip install -r requirements.txt || pip install .
        
    - name: Build with PyInstaller
      run: |
        pyinstaller --name=Gamdl-GUI-ZH --windowed --onedir --clean --noconfirm gui_app.py
        
    - name: Upload Artifacts
      uses: actions/upload-artifact@v4
      with:
        name: Gamdl-GUI-ZH-${{ matrix.os }}
        path: dist/Gamdl-GUI-ZH
"""
    with open(f'{workflow_dir}/build.yml', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\n✅ 已生成 GitHub Actions 配置: .github/workflows/build.yml")
    print("提示: 将代码推送到 GitHub 后，Actions 会自动为您构建所有平台的程序。")

if __name__ == "__main__":
    # 确保安装了 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        os.system(f"{sys.executable} -m pip install pyinstaller")

    build_macos()
    create_windows_script()
    create_github_workflow()

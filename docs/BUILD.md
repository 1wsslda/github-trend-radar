# Build Guide

## 面向普通使用者

如果你只是想重新打包可执行文件或安装包，最简单的入口是：

```cmd
scripts/build_all_click.cmd
```

它会自动完成两件事：

1. 生成单文件程序 `artifacts/dist/GitSonar.exe`
2. 生成安装包 `artifacts/dist/installer/GitSonarSetup.exe`

## 构建入口

### 一键打包

- 文件：`scripts/build_all_click.cmd`
- 适合：日常更新代码后快速重新产出 EXE 和安装包

### 仅打包 EXE

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

输出：

- `artifacts/dist/GitSonar.exe`

### 打包安装包

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_setup.ps1
```

输出：

- `artifacts/dist/installer/GitSonarSetup.exe`

`scripts/build_setup.ps1` 会先调用 `scripts/build_exe.ps1`，再调用 `packaging/GitSonar.iss` 生成安装包。

## 环境要求

当前项目主要面向 Windows。

- Windows 11
- Python 3.14
- Inno Setup 6

Python 依赖较少，核心包括：

- `requests`
- `beautifulsoup4`
- `pystray`
- `Pillow`
- `PyInstaller`

## 脚本行为说明

构建脚本当前会自动处理这些常见动作：

- 缺少 Python 包时自动安装
- 打包前关闭旧进程
- 清理 `build/` 与 `__pycache__/`
- 自动调用 PyInstaller
- 打安装包时自动尝试定位 Inno Setup

## 当前品牌迁移状态

本项目源码和构建产物已经统一到 `GitSonar`：

- 入口脚本：`src/gitsonar/__main__.py`
- 安装脚本：`packaging/GitSonar.iss`
- 可执行文件：`GitSonar.exe`
- 安装包：`GitSonarSetup.exe`

旧版本遗留的数据目录如果存在，会在首次运行时自动尝试合并到新的 `%LOCALAPPDATA%\GitSonar` 目录中。

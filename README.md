<div align="center">

# 🎵 AutoMidi

**智能音频转MIDI桌面应用**

[![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)](https://github.com/northland-studio/automidi)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

*将任意音频文件智能转录为高质量MIDI文件*

[功能特性](#功能特性) • [安装指南](#安装指南) • [使用方法](#使用方法) • [技术架构](#技术架构)

</div>

---

## 📖 项目简介

AutoMidi 是一款专业的音频转MIDI桌面应用程序，采用先进的深度学习技术，能够将任意音频文件自动转录为高质量的MIDI文件。支持音源分离、批量处理、MIDI编辑等专业功能，适用于音乐制作、音频分析、教育研究等多种场景。

### 🎯 核心优势

- **🧠 智能转录** - 基于 Spotify basic-pitch 深度学习模型，转录准确率高
- **🎸 音源分离** - 集成 demucs 算法，可将音频分离为人声/鼓/贝斯/其他轨道
- **⚡ 高效处理** - 支持 ONNX 推理优化，处理速度快
- **🎨 专业编辑** - 内置钢琴卷帘编辑器，支持音符精细调整
- **📊 智能分析** - 自动检测 BPM、调性、和弦进行

---

## ✨ 功能特性

### 核心功能

| 功能 | 描述 |
|------|------|
| 🎵 音频加载 | 支持 WAV、MP3、FLAC、OGG、M4A 等主流格式 |
| 🎹 智能转录 | 自动分析音频内容，生成 MIDI 音符序列 |
| 🎚️ 参数调节 | 可调节起音阈值、帧阈值、最小音符时长 |
| 🎼 MIDI 生成 | 支持多种乐器音色，生成标准 MIDI 文件 |
| 🔊 预览播放 | 原始音频和 MIDI 实时预览播放 |
| 💾 文件导出 | 一键导出 MIDI 文件，支持自定义命名 |

### 高级功能

| 功能 | 描述 |
|------|------|
| 🎸 音源分离 | 将音频分离为 4 个独立轨道，分别转录 |
| 📦 批量处理 | 支持多文件批量转录，提高工作效率 |
| ✏️ MIDI 编辑 | 钢琴卷帘编辑器，可视化编辑音符 |
| 🎼 和弦检测 | 自动识别和弦进行，辅助音乐分析 |
| 📊 节拍分析 | 自动检测 BPM 和调性 |
| 🎨 主题切换 | 深色/浅色主题，适应不同使用环境 |
| ⌨️ 快捷键 | 常用操作快捷键支持 |
| 💿 用户预设 | 保存/加载参数配置，快速复用设置 |

---

## 🛠️ 安装指南

### 环境要求

- Python 3.10 或更高版本
- Windows 10/11（推荐）/ macOS / Linux
- 4GB+ 内存（推荐 8GB+）
- 支持 CUDA 的 GPU（可选，用于加速音源分离）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/northland-studio/automidi.git
cd automidi

# 2. 创建虚拟环境
python -m venv venv

# Windows 激活
venv\Scripts\activate

# Linux/macOS 激活
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python main.py
```

### GPU 加速支持（可选）

如果您有 NVIDIA GPU 并希望加速音源分离处理：

```bash
# 安装 CUDA 版本的 PyTorch
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

---

## 📚 使用方法

### 基本操作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  导入音频   │ -> │  调整参数   │ -> │  开始转录   │ -> │  导出MIDI   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

1. **导入音频** - 拖拽文件到窗口或点击"选择文件"
2. **调整参数** - 根据需要调整转录参数
3. **开始转录** - 点击"开始转录"按钮
4. **预览结果** - 点击"播放MIDI"预览转录效果
5. **导出文件** - 点击"导出MIDI"保存文件

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开文件 |
| `Ctrl+S` | 导出MIDI |
| `Ctrl+Q` | 退出程序 |
| `Space` | 播放/暂停 |
| `Escape` | 停止播放 |

### 音源分离使用

1. 勾选"启用音源分离"
2. 选择需要转录的轨道（人声/鼓/贝斯/其他）
3. 选择计算设备（自动/CPU/GPU）
4. 开始转录，导出时文件名自动添加轨道后缀

---

## 🏗️ 技术架构

### 技术栈

| 类别 | 技术 |
|------|------|
| GUI 框架 | PySide6 (Qt for Python) |
| 音频处理 | librosa, soundfile |
| 转录引擎 | Spotify basic-pitch |
| 音源分离 | demucs |
| MIDI 生成 | pretty_midi |
| 音频播放 | pygame |
| 推理优化 | ONNX Runtime |

### 项目结构

```
automidi/
├── main.py                     # 应用入口
├── ui/                         # 用户界面模块
│   ├── main_window.py          # 主窗口
│   ├── midi_editor.py          # MIDI编辑器
│   ├── batch_dialog.py         # 批量处理对话框
│   ├── settings_dialog.py      # 设置对话框
│   └── theme.py                # 主题管理
├── core/                       # 核心功能模块
│   ├── audio_loader.py         # 音频加载
│   ├── transcriber.py          # 转录引擎
│   ├── onnx_transcriber.py     # ONNX转录
│   ├── source_separator.py     # 音源分离
│   ├── ffmpeg_manager.py       # FFmpeg管理
│   ├── postprocess.py          # 音符后处理
│   ├── midi_generator.py       # MIDI生成
│   ├── chord_detector.py       # 和弦检测
│   ├── analyzer.py             # 音频分析
│   ├── player.py               # 播放器
│   └── logger.py               # 日志模块
├── models/                     # 模型文件
├── tools/ffmpeg/               # FFmpeg工具
├── requirements.txt            # 依赖清单
├── Plan.md                     # 开发计划
├── Reporter.md                 # 测试报告
└── README.md                   # 项目说明
```

---

## 📋 版本历史

### v2.0.1 (2026-04-25)
- 修复设置窗口预设功能错误
- 修复音源分离转录错误
- 添加 CPU/GPU 设备选择
- 添加 CUDA 可用性检测与自动回退
- 添加内置 ffmpeg 支持
- 导出时自动添加轨道后缀

### v2.0.0 (2026-04-25)
- 新增音源分离功能
- 新增 ONNX 模型优化
- 新增批量处理功能
- 新增 MIDI 编辑器
- 新增和弦检测功能
- 新增节拍/调性检测
- 新增主题切换
- 新增快捷键支持
- 新增用户预设功能

### v1.0.0 (2026-04-23)
- 初始版本发布
- 实现音频转MIDI核心功能
- 实现图形用户界面

---

## 👥 开发团队

**北域工作室 (Northland Studio)**

专注于音频处理与音乐科技软件开发

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🔗 仓库地址

- **GitHub**: https://github.com/northland-studio/automidi
- **Gitee**: https://gitee.com/northland_studio/automidi

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个 Star！**

Made with ❤️ by Northland Studio

</div>

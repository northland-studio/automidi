# AutoMidi

音频转MIDI桌面应用

## 项目简介

AutoMidi 是一款将音频文件自动转录为 MIDI 文件的桌面应用程序。用户可以通过拖拽或选择的方式导入音频文件，程序会自动分析音频内容并生成对应的 MIDI 文件，支持预览播放和参数调节。

## 功能特性

- 支持多种音频格式: WAV, MP3, FLAC, OGG, M4A
- 自动音频转录为 MIDI
- 可视化波形显示
- 转录参数可调节 (起音阈值、帧阈值、最小音符时长)
- 支持多种乐器音色选择
- 原始音频和 MIDI 预览播放
- 拖拽文件导入
- MIDI 文件导出

## 技术栈

- Python 3.10+
- PySide6 (Qt for Python) - GUI框架
- librosa - 音频处理
- soundfile - 音频文件读写
- basic-pitch - 音频转MIDI转录引擎
- pretty_midi - MIDI文件生成
- pygame - 音频播放

## 安装

### 环境要求

- Python 3.10 或更高版本
- Windows / macOS / Linux

### 安装步骤

1. 克隆仓库
```bash
git clone git@github.com:northland-studio/automidi.git
cd automidi
```

2. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动应用
```bash
python main.py
```

### 操作流程

1. 拖拽音频文件到窗口或点击"选择文件"按钮
2. 调整转录参数 (可选)
3. 点击"开始转录"按钮
4. 等待转录完成
5. 点击"播放MIDI"预览结果
6. 点击"导出MIDI"保存文件

## 项目结构

```
automidi/
├── main.py                 # 应用入口
├── ui/
│   ├── __init__.py
│   └── main_window.py      # 主窗口逻辑
├── core/
│   ├── __init__.py
│   ├── audio_loader.py     # 音频加载与预处理
│   ├── transcriber.py      # 转录引擎封装
│   ├── postprocess.py      # 音符后处理
│   ├── midi_generator.py   # MIDI 生成与导出
│   └── player.py           # 音频/MIDI 播放
├── models/                 # 存放 ONNX 模型文件
├── requirements.txt        # 依赖清单
├── Plan.md                 # 开发计划
└── README.md               # 项目说明
```

## 版本历史

### v1.0.0 (2026-04-23)
- 初始版本发布
- 实现音频转MIDI核心功能
- 实现图形用户界面
- 支持多种音频格式
- 支持参数调节和预览播放

## 开发团队

北域工作室 (Northland Studio)

## 许可证

MIT License

## 仓库地址

- GitHub: https://github.com/northland-studio/automidi
- Gitee: https://gitee.com/northland_studio/automidi

# AutoMidi

音频转MIDI桌面应用

## 项目简介

AutoMidi 是一款将音频文件自动转录为 MIDI 文件的桌面应用程序。用户可以通过拖拽或选择的方式导入音频文件，程序会自动分析音频内容并生成对应的 MIDI 文件，支持预览播放和参数调节。

## 版本信息

- 当前版本: 2.0.0
- 开发者: 北域工作室

## 功能特性

### 核心功能
- 支持多种音频格式: WAV, MP3, FLAC, OGG, M4A
- 自动音频转录为 MIDI
- 可视化波形显示
- 转录参数可调节 (起音阈值、帧阈值、最小音符时长)
- 支持多种乐器音色选择
- 原始音频和 MIDI 预览播放
- 拖拽文件导入
- MIDI 文件导出

### v2.0.0 新增功能

#### 核心拓展
- **音源分离**: 集成 demucs，将音频分离为人声/贝斯/鼓/其他轨道分别转录
- **ONNX 模型优化**: 支持 ONNX 推理，减少依赖体积
- **批量处理**: 支持同时处理多个音频文件

#### 功能增强
- **MIDI 编辑**: 钢琴卷帘编辑器，支持音符编辑
- **和弦检测**: 自动识别和弦进行
- **节拍/调性检测**: 自动检测 BPM 和调性
- **量化功能增强**: 支持多种量化网格

#### 用户体验
- **主题切换**: 支持深色/浅色主题
- **快捷键支持**: 常用操作快捷键
- **用户预设**: 保存/加载参数配置
- **个性化设置**: 独立导出路径设置

## 技术栈

- Python 3.10+
- PySide6 (Qt for Python) - GUI框架
- librosa - 音频处理
- soundfile - 音频文件读写
- basic-pitch - 音频转MIDI转录引擎
- pretty_midi - MIDI文件生成
- pygame - 音频播放
- demucs - 音源分离
- onnxruntime - ONNX推理

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

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开文件 |
| Ctrl+S | 导出MIDI |
| Ctrl+Q | 退出 |
| Space | 播放/暂停 |
| Escape | 停止播放 |

## 项目结构

```
automidi/
├── main.py                     # 应用入口
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── midi_editor.py          # MIDI编辑器
│   ├── batch_dialog.py         # 批量处理对话框
│   ├── settings_dialog.py      # 设置对话框
│   └── theme.py                # 主题管理
├── core/
│   ├── __init__.py
│   ├── audio_loader.py         # 音频加载
│   ├── transcriber.py          # 转录引擎
│   ├── onnx_transcriber.py     # ONNX转录
│   ├── source_separator.py     # 音源分离
│   ├── postprocess.py          # 音符后处理
│   ├── midi_generator.py       # MIDI生成
│   ├── chord_detector.py       # 和弦检测
│   ├── analyzer.py             # 音频分析
│   └── player.py               # 播放器
├── models/                     # 模型文件
├── requirements.txt            # 依赖清单
├── AutoMidi.spec               # PyInstaller配置
├── Plan.md                     # 开发计划
├── Reporter.md                 # 测试报告
└── README.md                   # 项目说明
```

## 打包发布

使用 PyInstaller 打包:

```bash
pyinstaller AutoMidi.spec
```

打包后的可执行文件位于 `dist/` 目录。

## 版本历史

### v2.0.0 (2026-04-23)
- 新增音源分离功能 (demucs)
- 新增 ONNX 模型优化
- 新增批量处理功能
- 新增 MIDI 编辑器
- 新增和弦检测功能
- 新增节拍/调性检测
- 新增主题切换
- 新增快捷键支持
- 新增用户预设功能
- 新增个性化设置

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

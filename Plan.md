# AutoMidi 开发计划

## 项目信息

- 项目名称: AutoMidi
- 版本: 1.0.0
- 开发者: 北域工作室
- 开始日期: 2026-04-23

## 项目目标

开发一款独立桌面软件，支持用户拖拽/选择音频文件，经自动转录后生成并导出 MIDI 文件，并可预览播放。

## 技术栈

- 语言: Python 3.10+
- GUI: PySide6 (Qt for Python)
- 音频处理: librosa, soundfile
- 转录引擎: Spotify basic-pitch
- MIDI 生成: pretty\_midi
- 播放预览: pygame

## 开发进度

### 第一阶段: 项目初始化 \[已完成]

- [x] 创建项目目录结构
- [x] 创建 requirements.txt 依赖清单
- [x] 配置开发环境

### 第二阶段: 核心模块开发 \[已完成]

- [x] 音频加载模块 (core/audio\_loader.py)
  - 支持多种音频格式 (WAV, MP3, FLAC, OGG, M4A)
  - 自动重采样到 22050Hz
  - 波形摘要生成
- [x] 转录引擎模块 (core/transcriber.py)
  - 集成 basic-pitch 进行音频转MIDI
  - 支持阈值参数调节
  - 备用转录方案 (librosa)
- [x] 音符后处理模块 (core/postprocess.py)
  - 音符时长过滤
  - 相邻音符合并
  - 力度调整
  - 量化功能
- [x] MIDI 生成模块 (core/midi\_generator.py)
  - 生成标准 MIDI 文件
  - 支持乐器选择
  - 导出功能
- [x] 播放器模块 (core/player.py)
  - 原始音频播放
  - MIDI 合成播放
  - 播放控制

### 第三阶段: 用户界面开发 \[已完成]

- [x] 主窗口界面 (ui/main\_window\.py)
  - 文件拖拽区域
  - 波形可视化
  - 音频信息显示
  - 转录选项面板
  - 控制按钮
  - 进度条
  - 状态栏
- [x] 应用入口 (main.py)

### 第四阶段: 测试与优化 \[进行中]

- [ ] 功能测试
- [ ] 性能优化
- [ ] 打包发布

## 文件结构

```
audio2midi/
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
├── requirements.txt
├── Plan.md
└── README.md
```

## 后续计划

1. 添加音源分离功能 (demucs)
2. 批量处理支持
3. ONNX 模型优化
4. PyInstaller 打包


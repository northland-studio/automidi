# AutoMidi 开发计划

## 项目信息

- 项目名称: AutoMidi
- 当前版本: 2.0.1
- 开发者: 北域工作室
- 开始日期: 2026-04-23

## 版本历史

### v1.0.0 (2026-04-23)
- 初始版本发布
- 实现音频转MIDI核心功能
- 实现图形用户界面
- 支持多种音频格式
- 支持参数调节和预览播放

### v2.0.0 (2026-04-25)
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
- 新增日志模块

### v2.0.1 (2026-04-25)
- 修复设置窗口 type=dict 错误
- 修复 SeparatedTrack 访问错误
- 添加分离模型设备选择 (CPU/GPU)
- 添加 CUDA 可用性检测与自动回退
- 添加内置 ffmpeg 支持
- 优化 PyInstaller 打包配置
- 导出 MIDI 时添加轨道后缀

---

## v2.1.0 开发计划 (待定)

### 版本目标
优化性能，增强稳定性，改进用户体验。

### 开发进度

#### 第一阶段: 性能优化

##### 1. 转录性能优化
- [ ] 支持多线程转录
- [ ] 优化内存使用
- [ ] 支持流式处理大文件

##### 2. UI 性能优化
- [ ] 波形渲染优化
- [ ] MIDI 编辑器性能优化
- [ ] 减少内存占用

#### 第二阶段: 功能增强

##### 3. MIDI 编辑增强
- [ ] 撤销/重做功能
- [ ] 音符批量编辑
- [ ] MIDI 导入功能

##### 4. 导出增强
- [ ] 支持更多 MIDI 格式
- [ ] 支持导出 MusicXML
- [ ] 批量导出优化

#### 第三阶段: 用户体验

##### 5. 国际化
- [ ] 英文界面支持
- [ ] 语言切换功能

##### 6. 文档完善
- [ ] 用户手册
- [ ] API 文档
- [ ] 视频教程

---

## 文件结构 (v2.0.x)

```
automidi/
├── main.py                     # 应用入口
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── midi_editor.py          # MIDI编辑器
│   ├── settings_dialog.py      # 设置对话框
│   ├── batch_dialog.py         # 批量处理对话框
│   └── theme.py                # 主题管理
├── core/
│   ├── __init__.py
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
│   └── .gitkeep
├── tools/                      # 工具文件
│   └── ffmpeg/                 # FFmpeg目录
│       ├── .gitkeep
│       └── README.md
├── requirements.txt            # 依赖清单
├── Plan.md                     # 开发计划
├── Reporter.md                 # 测试报告
└── README.md                   # 项目说明
```

## 依赖

```
pyside6>=6.5
librosa
soundfile
resampy
pretty_midi
pygame
numpy
onnxruntime
basic-pitch
demucs
imageio-ffmpeg
```

## 远程仓库

- GitHub: https://github.com/northland-studio/automidi
- Gitee: https://gitee.com/northland_studio/automidi

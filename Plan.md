# AutoMidi 开发计划

## 项目信息

- 项目名称: AutoMidi
- 当前版本: 1.0.0
- 目标版本: 2.0.0
- 开发者: 北域工作室
- 开始日期: 2026-04-23

## 版本历史

### v1.0.0 (2026-04-23)
- 初始版本发布
- 实现音频转MIDI核心功能
- 实现图形用户界面
- 支持多种音频格式
- 支持参数调节和预览播放

---

## v2.0.0 开发计划

### 版本目标
在 v1.0.0 基础上，新增音源分离、ONNX优化、批量处理、MIDI编辑、和弦检测等高级功能，提升用户体验。

### 开发进度

#### 第一阶段: 核心拓展 [进行中]

##### 1. 音源分离模块 (core/source_separator.py)
- [ ] 集成 demucs 库
- [ ] 实现音频分离为人声/贝斯/鼓/其他轨道
- [ ] 支持选择特定轨道进行转录
- [ ] 多轨道转录结果合并
- [ ] 分离进度回调

##### 2. ONNX 模型优化 (core/onnx_transcriber.py)
- [ ] 将 basic-pitch TensorFlow 模型转换为 ONNX
- [ ] 实现 ONNX 推理引擎
- [ ] 减少 TensorFlow 依赖
- [ ] 优化推理速度
- [ ] 模型文件打包

##### 3. 批量处理功能
- [ ] 支持多文件选择
- [ ] 批量转录队列管理
- [ ] 批量导出设置
- [ ] 进度汇总显示

#### 第二阶段: 功能增强 [待开始]

##### 4. MIDI 编辑功能 (ui/midi_editor.py)
- [ ] MIDI 文件导入
- [ ] 钢琴卷帘编辑器
- [ ] 音符选择/移动/删除
- [ ] 音符属性编辑 (音高/力度/时长)
- [ ] 撤销/重做功能

##### 5. 和弦检测功能 (core/chord_detector.py)
- [ ] 实现和弦识别算法
- [ ] 显示和弦进行
- [ ] 和弦标注导出

##### 6. 节拍/调性检测 (core/analyzer.py)
- [ ] BPM 自动检测
- [ ] 调性识别
- [ ] 节拍网格显示
- [ ] 拍号检测

##### 7. 量化功能增强
- [ ] 网格量化选项 (1/4, 1/8, 1/16, 1/32)
- [ ] 量化强度调节
- [ ] 人性化摇摆功能

#### 第三阶段: 用户体验 [待开始]

##### 8. 主题切换
- [ ] 深色主题
- [ ] 浅色主题
- [ ] 自定义主题配置

##### 9. 快捷键支持
- [ ] 文件操作快捷键 (Ctrl+O, Ctrl+S)
- [ ] 播放控制快捷键 (Space, Esc)
- [ ] 编辑操作快捷键 (Ctrl+Z, Ctrl+Y)

##### 10. 用户预设功能
- [ ] 保存当前参数配置
- [ ] 加载预设配置
- [ ] 预设管理界面

##### 11. 国际化支持
- [ ] 中文界面
- [ ] 英文界面
- [ ] 语言切换功能

##### 12. 个性化设置
- [ ] 独立导出路径设置
- [ ] 默认文件名模板
- [ ] 自动保存设置

#### 第四阶段: 发布准备 [待开始]

##### 13. PyInstaller 打包
- [ ] 创建打包配置文件
- [ ] 包含所有依赖
- [ ] 包含模型文件
- [ ] 添加应用图标
- [ ] 测试打包结果

##### 14. 全栈测试
- [ ] 功能测试
- [ ] 性能测试
- [ ] 兼容性测试
- [ ] 用户测试

##### 15. 文档更新
- [ ] 更新 README.md
- [ ] 撰写 Reporter.md
- [ ] 用户手册

##### 16. 发布
- [ ] 代码提交
- [ ] 推送到远程仓库
- [ ] 创建 Release

---

## 文件结构 (v2.0.0)

```
automidi/
├── main.py                     # 应用入口
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── midi_editor.py          # MIDI编辑器 [新增]
│   ├── settings_dialog.py      # 设置对话框 [新增]
│   ├── batch_dialog.py         # 批量处理对话框 [新增]
│   ├── theme.py                # 主题管理 [新增]
│   └── resources/              # 资源文件 [新增]
│       ├── icons/
│       ├── themes/
│       └── i18n/
├── core/
│   ├── __init__.py
│   ├── audio_loader.py         # 音频加载
│   ├── transcriber.py          # 转录引擎
│   ├── onnx_transcriber.py     # ONNX转录 [新增]
│   ├── source_separator.py     # 音源分离 [新增]
│   ├── postprocess.py          # 音符后处理
│   ├── midi_generator.py       # MIDI生成
│   ├── chord_detector.py       # 和弦检测 [新增]
│   ├── analyzer.py             # 音频分析 [新增]
│   └── player.py               # 播放器
├── models/                     # 模型文件
│   ├── basic_pitch.onnx        # ONNX模型 [新增]
│   └── .gitkeep
├── i18n/                       # 国际化 [新增]
│   ├── zh_CN.ts
│   └── en_US.ts
├── requirements.txt
├── Plan.md
├── Reporter.md                 # 测试报告 [新增]
├── README.md
└── AutoMidi.spec               # PyInstaller配置 [新增]
```

## 依赖更新

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
demucs                    # [新增] 音源分离
```

## 远程仓库

- GitHub: git@github.com:northland-studio/automidi.git
- Gitee: git@gitee.com:northland_studio/automidi.git

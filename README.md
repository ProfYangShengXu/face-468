# 😏 Face 468

> 用浏览器「偷」走你的表情，塞进 Blender。

一个**零安装、纯前端**的人脸 468 关键点采集器。打开网页 → 摄像头看你一眼 → 468 个 3D 点实时追踪你的脸 → 一键导出 JSON → 扔进 Blender，你的表情就在 3D 世界里活过来了。

<p align="center">
  <img src="https://img.shields.io/badge/纯前端-零依赖-brightgreen" alt="zero deps">
  <img src="https://img.shields.io/badge/MediaPipe-WASM-blue" alt="mediapipe">
  <img src="https://img.shields.io/badge/Blender-5.x-orange" alt="blender">
  <img src="https://img.shields.io/badge/炫技-拉满-ff0066" alt="cool">
</p>

---

## 🎬 30 秒上车

```bash
# 1. 打开采集器（没错，就双击）
open index.html

# 2. 浏览器里操作
#    授权摄像头 → 按 R 开始录制 → 做个鬼脸 → 再按 R 停止 → 按 E 导出

# 3. Blender 里导入
#    Scripting 工作空间 → 打开 blender/watch_and_drive.py → Run Script
#    → 选 face_capture.json → 按空格播放
```

你的面部网格 + 468 个追踪点 + 7 个发光标记球就在 Blender 时间轴上动起来了。

---

## 🧠 原理（一句话）

```
摄像头 ──→ MediaPipe Face Mesh ──→ 468 个 3D 关键点 ──→ JSON ──→ Blender
          (Google WASM 推理)       (每帧 ~1.4KB)      (紧凑格式)   (顶点动画)
```

没后端。没 Python 服务。没 `npm install`。就一个 HTML 文件和一段 Blender 脚本。

---

## 📦 文件清单

```
face-468/
├── index.html                      # 采集器本体 (双击即用)
├── blender/
│   └── watch_and_drive.py          # Blender 导入脚本
├── docs/
│   ├── PROJECT.md                  # 技术文档
│   └── delivery/logs/              # 开发日志
└── ops/
    └── RUNBOOK.md                  # 运维手册
```

---

## ⌨ 快捷键

| 键 | 功能 |
|----|------|
| `R` | 开始/停止录制 |
| `E` | 导出 JSON |
| `M` | 切换面部网格 |
| `D` | 切换关键点显示 |

---

## 🎨 Blender 里你会看到

| 对象 | 说明 |
|------|------|
| `FaceMesh` | 绿色半透明面部网格，468 顶点实时动画 |
| `LM_000` ~ `LM_467` | 468 个追踪空物体，可用来驱动 Rig |
| `LM_nose_tip` | 🔴 金色鼻尖标记球 |
| `LM_upper_lip` / `LM_lower_lip` | 🔴 红色嘴唇标记球 |
| `LM_lip_left` / `LM_lip_right` | 🔴 嘴角标记球 |
| `LM_left_eye` / `LM_right_eye` | 🔵 蓝色眼角标记球 |

---

## 🔧 调参

Blender 脚本顶部几个变量，看着改：

```python
FACE_SCALE    = 0.8     # 脸宽
FACE_HEIGHT   = 0.7     # 脸高
DEPTH_SCALE   = 0.8     # 深度 (鼻子突出程度)
OVERALL_SCALE = 2.0     # 整体放大，只改这一个也行
```

---

## ⚠️ 注意事项

- 需要 **HTTPS** 或 **localhost** 才能调用摄像头（`file://` 协议不行——浏览器安全策略）
- 首次加载 MediaPipe WASM 约 4MB，需等 5-10 秒（浏览器会缓存，下次秒开）
- Blender 脚本兼容 **4.x ~ 5.x**

---

## 🪪 技术栈

`getUserMedia` · `Canvas 2D` · `MediaPipe Face Mesh (WASM)` · `requestAnimationFrame` · `bpy`

---

<p align="center">
  <sub>Made with ❤️ and zero npm packages</sub>
</p>

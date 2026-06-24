# Face 468 — 面部关键点采集器

> 用户原话：「做人脸468关键点采集器，正好电脑有blender，完成后可以导入到blender」

## 是什么

一个**零安装、纯前端**的人脸 468 关键点实时采集工具。打开浏览器 → 授权摄像头 → 实时看到面部网格叠加 → 录制 → 一键导出 JSON → 在 Blender 中导入并驱动 3D 面部模型。

## 架构

```
┌──────────────────────────────────────────────────────┐
│  index.html (单文件，~500 行)                          │
│                                                      │
│  getUserMedia ──→ <video> ──→ MediaPipe Face Mesh     │
│                      │            │                  │
│                      ▼            ▼                  │
│                  Canvas 2D    468 关键点 (x,y,z)       │
│                  (镜像预览)         │                  │
│                      │        环形缓冲区 (N 秒)         │
│                      │            │                  │
│                      └────┬───────┘                  │
│                           ▼                          │
│                    导出 face_capture.json              │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│  blender/watch_and_drive.py                          │
│                                                      │
│  读取 JSON → 创建 468 个 Empty → 时间轴关键帧动画       │
│  (可选 WATCH_MODE: 自动监听文件变化重建动画)             │
└──────────────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 摄像头 | Web `getUserMedia` API | 浏览器原生 |
| 人脸关键点 | MediaPipe Face Mesh (WASM) | CDN 加载，468 点 3D 坐标 |
| 渲染 | Canvas 2D + FACEMESH_TESSELATION | 三角形网格叠加 |
| 数据格式 | JSON（紧凑 `[[x,y,z],...]` 格式） | Blender Python 原生消费 |
| Blender 端 | `bpy` Python API | Empty 对象 + 关键帧动画 |

## 主流程逻辑链

1. **启动** → 页面加载 → CDN 拉取 MediaPipe WASM → `getUserMedia` 请求摄像头
2. **推理循环** → `faceMesh.send({image: video})` → `onResults` 回调 → 获得 468 个 `{x,y,z}` 归一化坐标
3. **渲染** → Canvas 镜像绘制视频 → 遍历 `FACEMESH_TESSELATION` 三角边 → 绿色半透明线条叠加
4. **录制** → 用户点击录制 → 每帧关键点 `[[x,y,z],...]` 追加到环形缓冲区 → 超出缓冲时长自动裁旧
5. **导出** → `normalizedBuffer()` 归一化时间戳 → `JSON.stringify` → Blob 下载
6. **Blender** → 脚本读取 JSON → 468 个 Empty 逐帧 `keyframe_insert(location)` → 播放时间轴

## 数据格式

```json
{
  "meta": {
    "version": "1.0",
    "landmark_count": 468,
    "fps": 30,
    "frame_count": 300,
    "duration_sec": 10.0
  },
  "frames": [
    {
      "t": 0.0,
      "lm": [[0.512, 0.423, -0.031], [0.513, 0.421, -0.029], ...]
    }
  ]
}
```

- `t`: 秒（已归一化，首帧为 0.0）
- `lm[i]`: `[x, y, z]` — MediaPipe 原始归一化坐标（x∈[0,1], y∈[0,1], z∈[-0.1,0.1]）
- Blender 脚本内部做坐标变换：x 居中缩放、y 翻转、z 映射深度

## 运行命令

```bash
# 浏览器采集端 — 直接打开即可
open index.html

# Blender 端
# 1. 打开 Blender → Scripting 工作空间
# 2. 打开 blender/watch_and_drive.py → Run Script
# 3. 选择导出的 face_capture.json
# 4. 按空格键播放动画

# 本地服务器（可选，用于局域网访问或 HTTPS 需求）
python3 -m http.server 8080
```

## 文件清单

```
webcam-face-capture/
├── index.html                          # 采集器主程序
├── blender/
│   └── watch_and_drive.py              # Blender 导入脚本
├── docs/
│   ├── PROJECT.md                      # 本文档
│   └── delivery/logs/
│       └── 2025-07-17-facemesh-capture.md  # 开发日志
└── ops/
    └── RUNBOOK.md                      # 运维手册
```

## 变更索引

| 日期 | 变更 | 日志 |
|------|------|------|
| 2025-07-17 | 项目初始化，index.html + Blender 脚本 | [日志](delivery/logs/2025-07-17-facemesh-capture.md) |

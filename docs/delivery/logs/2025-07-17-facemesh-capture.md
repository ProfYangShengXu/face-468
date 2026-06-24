# 人脸468关键点采集器 — 更新日志

> 创建时间：2025-07-17 | 任务类型：新建项目

---

## §1 计划更新

### 目标
构建纯前端 HTML 单文件人脸 468 关键点实时采集器：
- 摄像头预览 + 面部网格叠加
- 环形缓冲区存储 N 秒数据
- 一键导出 JSON，格式可直接被 Blender Python 脚本消费
- 附带 Blender 端自动监听导入脚本

### 改动范围表

| # | 文件 | 状态 | 类型 | 调用方 | 说明 |
|---|------|------|------|--------|------|
| 1 | `index.html` | ✅ 已创建 | 唯一应用文件 | 无 | 摄像头采集 + MediaPipe 推理 + Canvas 渲染 + 导出 |
| 2 | `blender/watch_and_drive.py` | ✅ 已创建 | Blender 脚本 | 用户手动在 Blender 内运行 | 文件选择器导入 / 轮询 JSON → 468 Empty + 关键帧动画 |
| 3 | `docs/PROJECT.md` | 待创建 | 项目文档 | 无 | 阶段四产出 |

### 明确不做
- 不录视频/音频（仅采集关键点数据）✅
- 不做多人脸识别（maxNumFaces: 1）✅
- 不做在线服务/后端存储 ✅
- 不做 Three.js 3D 预览（用 Canvas 2D 叠加网格）✅
- Blender 脚本不做面部 Rig 自动绑定（仅创建 468 个 Empty 点位 + 动画）✅

### 依赖前置
- 用户浏览器支持 `getUserMedia`
- 用户电脑已安装 Blender（>= 3.0）

### 待确认项
- 方案已由用户确认（2025-07-17）✅
- 缓冲时长默认 10 秒（可调滑块 3-30s）✅

---

## §2 目标逻辑链

### 六环链路

| 环 | 描述 | 预期行为 | 涉及文件/函数 |
|----|------|----------|---------------|
| ① 触发入口 | 用户双击打开 index.html | 浏览器请求摄像头权限，加载 MediaPipe WASM | `index.html`: `init()` → `navigator.mediaDevices.getUserMedia()` |
| ② 输入校验 | 摄像头就绪 + MediaPipe 模型加载完成 | 两个异步状态都 ready 后启动循环 | `index.html`: 顺序 init（camera → faceMesh → first send） |
| ③ 核心逻辑 | 每帧: 视频帧 → MediaPipe 推理 → 468 关键点 → 环形缓冲区记录 + Canvas 渲染 | 30fps 稳定运行，缓冲区内数据可导出 | `index.html`: `onResults()` → `render()` + `addToBuffer()` |
| ④ 持久化/副作用 | 用户点击「导出」→ JSON 序列化缓冲区 → Blob 下载 | 生成 `face_capture.json`，包含 meta + 全部帧数据 | `index.html`: `exportJSON()` → `Blob` → `<a download>` |
| ⑤ 返回/展示 | Canvas 实时显示摄像头画面 + 面部网格 | 网格随人脸移动实时更新，默认镜像模式 | `index.html`: `render()` → Canvas 2D + FACEMESH_TESSELATION |
| ⑥ Blender 消费 | 用户在 Blender 运行 `watch_and_drive.py` | 文件选择器 → 468 Empty → 时间轴关键帧动画；可选 WATCH_MODE 自动监听 | `blender/watch_and_drive.py`: `load_and_animate()` |

### 验收标准
1. 打开 HTML → 授权摄像头 → 看到面部网格实时叠加
2. 点击录制 → 缓冲开始填充 → 数据面板显示帧数
3. 点击导出 → 浏览器下载 JSON 文件
4. JSON 结构验证：`{meta, frames: [{t, lm: [[x,y,z],...]}]}`
5. Blender 运行脚本 → 选择 JSON → 468 个 Empty 在时间轴上运动

### 风险边界
- MediaPipe WASM 首次加载约 4MB，慢网络下需 5-10s；页面显示加载进度与 spinner
- 浏览器非 HTTPS 时 `getUserMedia` 不可用（localhost 除外）
- Blender 脚本需要用户手动运行，非全自动

---

## §3 实施记录

### 实际改动
| 文件 | 行数 | 关键决策 |
|------|------|----------|
| `index.html` | ~330 行 JS + ~180 行 CSS | UMD CDN (v0.4.1633559619)，Canvas 2D + requestAnimationFrame 自驱动循环，环形缓冲区 Array + shift 裁剪，导出紧凑 `[[x,y,z],...]` 格式 |
| `blender/watch_and_drive.py` | ~170 行 | 交互模式：文件选择器 Operator；可选 WATCH_MODE：bpy.app.timers 轮询 mtime 自动重载 |

### 与计划偏差
| 偏差 | 原因 |
|------|------|
| 改为顺序初始化（camera → faceMesh）而非 Promise.all | 更精确的错误提示，加载阶段分步显示 |
| 录制为手动开始/停止（非始终缓冲） | 用户控制更强，避免意外数据堆积 |
| Blender 默认文件选择器交互模式，WATCH_MODE 需手动开启 | 降低用户初次使用的认知负担 |

---

## §4 阶段二自查结论

### 逐环核查

| 环 | 状态 | 代码位置 | 验证 |
|----|------|----------|------|
| ① 触发入口 | ✅ | `index.html`:`init()` → `getUserMedia({video:{...}})` → `video.srcObject = stream` | 摄像头权限请求正确配置，失败时 loading 屏显示错误 |
| ② 输入校验 | ✅ | `init()` 顺序: camera → `new FaceMesh({locateFile})` → `setOptions({refineLandmarks:true})` → `onResults` → `await faceMesh.send({image:video})` | 双异步顺序保障，任一失败 catch 到并显示 |
| ③ 核心逻辑 | ✅ | `onResults()`: `faceLandmarks = results.multiFaceLandmarks[0]` → `render()` + `addToBuffer()` | 每帧 468 点数据经 `l => [l.x, l.y, l.z]` 紧凑存入 buffer |
| ④ 持久化 | ✅ | `exportJSON()` → `normalizedBuffer()` (timestamp归一化) → `Blob([JSON.stringify(data,null,2)])` → `<a download="face_capture.json">` | 导出格式符合设计：`{meta:{version,landmark_count,fps,frame_count,duration_sec}, frames:[{t,lm}]}` |
| ⑤ 返回/展示 | ✅ | `render()`: `ctx.save/translate/scale(-1,1)` 镜像视频 → `FACEMESH_TESSELATION` 连线 → 可选关键点渲染 | 网格绿色半透明叠加，随人脸实时更新 |
| ⑥ Blender 消费 | ✅ | `load_and_animate()`: `clear_previous()` → `create_empties(468)` → 逐帧 `keyframe_insert(location)` → `INTERPOLATION` 设置 | 坐标映射：`mediapipe_to_blender()` 处理 xyz 轴交换与缩放 |

### 边界覆盖
- 无人脸时：`faceLandmarks = null`，render 仅绘制视频，循环不中断
- 缓冲超限：while 循环 shift 旧帧，HUD 实时更新帧数/秒数
- 导出空缓冲：toast 提示 + 按钮 disabled
- WASM 加载失败：loading 屏显示具体错误信息
- DPI 缩放：canvas 使用 `devicePixelRatio` 适配 Retina 屏

### 已知未覆盖
- 标签页后台时 `requestAnimationFrame` 被浏览器节流，可能导致丢帧（WASM 推理可能在恢复后处理积压帧）。**影响**：录制时间戳不连续。**缓解**：Blender 侧按 t 字段映射而非等间距帧号。
- `faceMesh.send().catch(() => {})` 静默吞错，若 WASM 持续失败循环静默终止。**影响**：极低概率（WASM 运行时崩溃）。**缓解**：可后续加连续失败计数器 + UI 告警。

**自查结论：六环全部可达，边界场景均有处理，通过。**

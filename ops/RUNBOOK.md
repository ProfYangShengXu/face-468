# RUNBOOK — Face 468 面部关键点采集器

## 启动

```bash
# 方式 1：直接打开（推荐）
open index.html          # macOS
start index.html         # Windows
xdg-open index.html      # Linux

# 方式 2：本地服务器（如需 HTTPS 或同一局域网访问）
python3 -m http.server 8080
# → 浏览器打开 http://localhost:8080
```

## 测试

本项目为纯前端 HTML，无构建/测试框架。

| 检查项 | 方法 | 预期 |
|--------|------|------|
| 页面加载 | 双击 index.html | 看到加载动画 → 摄像头授权提示 |
| 面部网格 | 授权后面对摄像头 | 绿色三角网格覆盖在面部 |
| 录制 | 点击「开始录制」→ 等待 5 秒 → 点击「停止」 | 帧数和秒数累加 |
| 导出 | 点击「导出 JSON」 | 浏览器下载 face_capture.json |
| JSON 结构 | 用记事本/VSCode 打开 JSON | 包含 meta + frames 数组 |
| Blender 导入 | 在 Blender Scripting 工作空间运行 blender/watch_and_drive.py | 弹出文件选择器 → 选择 JSON → 468 个 LM_xxx Empty 出现在场景中 |
| Blender 动画 | 按空格键播放 | 468 个 Empty 随录制的人脸运动 |

## 快捷键

| 键 | 功能 |
|----|------|
| R | 开始/停止录制 |
| E | 导出 JSON |
| M | 切换网格显示 |
| D | 切换关键点显示 |

## 交付前自检

- [x] HTML 文件可独立运行（无跨域依赖，CDN 公网可达）
- [x] 摄像头权限请求正常
- [x] 面部网格渲染正常（依赖 FaceMesh.FACEMESH_TESSELATION 常量）
- [x] 录制/停止/清空/导出功能正常
- [x] 缓冲滑块可调，实时裁切旧帧
- [x] Blender 脚本语法正确（Python 3.7+ bpy）
- [x] 坐标映射：MediaPipe → Blender 右手系转换正确

"""
Face 468 — Blender 自动导入驱动脚本
=====================================
在 Blender 中运行此脚本 (Scripting 工作空间 → 打开 → 运行脚本)，
选择浏览器导出的 face_capture.json，自动创建面部网格 + 468 个 Empty
并在时间轴上生成关键帧动画。

用法（交互模式，默认）：
  1. Blender → Scripting / Text Editor 工作空间
  2. 打开此文件 → 点击 ▶ Run Script
  3. 选择 face_capture.json → 等待构建 → 按空格键播放

用法（自动监听模式）：
  将 WATCH_MODE 改为 True。
"""

import bpy
import json
import os

# ═══════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════

# 缩放：MediaPipe 归一化坐标 → Blender 单位 (米)
#   face 在画面中约占 x:[0.25, 0.75] y:[0.15, 0.85]
#   真实人脸约 14cm 宽 × 20cm 高 → Blender 0.14 × 0.20
FACE_SCALE    = 0.8     # X 缩放 (调大=脸更宽)
FACE_HEIGHT   = 0.7     # Y (→ Blender Z) 缩放 (调大=脸更高)
DEPTH_SCALE   = 0.8     # Z (→ Blender Y) 深度缩放
OVERALL_SCALE = 2.0     # 整体放大倍数，改这一个就行

PREFIX        = "LM"    # Empty 命名前缀
MESH_NAME     = "FaceMesh"
INTERPOLATION = 'LINEAR'
MAX_LANDMARKS = 500       # 清理时遍历的最大 Empty 数量

# 自动监听模式
WATCH_MODE = False
WATCH_PATH = os.path.join(
    os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser("~"),
    "face_capture.json"
)
WATCH_INTERVAL = 1.0


# ═══════════════════════════════════════════════
#  Operator 类
# ═══════════════════════════════════════════════

class Face468_OT_Import(bpy.types.Operator):
    """导入 Face 468 JSON 数据并构建面部动画"""
    bl_idname = "import_test.face468"
    bl_label = "导入 Face 468 JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})  # type: ignore

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        load_and_animate(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ═══════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════

def get_collection():
    """获取可靠的目标 collection (兼容 Blender 3.x ~ 5.x)。"""
    col = bpy.context.collection
    if col is None:
        col = bpy.context.scene.collection
    return col


def mediapipe_to_blender(lm):
    """MediaPipe 归一化坐标 → Blender 右手坐标系 (米)。"""
    bx = (lm[0] - 0.5) * FACE_SCALE * OVERALL_SCALE
    bz = (0.5 - lm[1]) * FACE_HEIGHT * OVERALL_SCALE
    by = -lm[2] * DEPTH_SCALE * OVERALL_SCALE
    return (bx, by, bz)


def clear_previous():
    """清理旧的面部网格和 Empty。"""
    # 清理 Mesh
    mesh_obj = bpy.data.objects.get(MESH_NAME)
    if mesh_obj:
        mesh_data = mesh_obj.data
        bpy.data.objects.remove(mesh_obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

    # 清理 Empty
    to_remove = []
    for i in range(MAX_LANDMARKS):
        name = f"{PREFIX}_{i:03d}"
        obj = bpy.data.objects.get(name)
        if obj:
            to_remove.append(obj)
    if to_remove:
        for obj in to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)
        print(f"[Face468] 清理了 {len(to_remove)} 个旧 Empty")


# ═══════════════════════════════════════════════
#  主逻辑
# ═══════════════════════════════════════════════

def load_and_animate(json_path):
    """读取 JSON → 创建面部 Mesh + Empty → 设置关键帧动画。"""
    print(f"[Face468] 加载 {json_path} …")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta        = data.get('meta', {})
    frames      = data.get('frames', [])
    tessellation = data.get('tessellation', [])  # [[i,j], ...] 三角边
    fps         = meta.get('fps', 30)
    lm_count    = meta.get('landmark_count', 468)

    if not frames:
        print("[Face468] ❌ JSON 中无帧数据")
        return

    print(f"[Face468] {len(frames)} 帧 × {lm_count} 关键点 @ {fps} fps, "
          f"{len(tessellation)} 条拓扑边, 时长 {meta.get('duration_sec', 0):.1f}s")

    # 清理旧数据
    clear_previous()

    # ── 1. 创建面部 Mesh（可见的面） ──
    print(f"[Face468] 创建面部网格 …")
    coll = get_collection()

    mesh_data = bpy.data.meshes.new(f"{MESH_NAME}_data")
    # 从第一帧创建初始顶点
    first_lm = frames[0]['lm']
    verts = [mediapipe_to_blender(lm) for lm in first_lm]
    mesh_data.from_pydata(verts, [], tessellation)  # 顶点, [], 边
    mesh_data.update()

    mesh_obj = bpy.data.objects.new(MESH_NAME, mesh_data)
    coll.objects.link(mesh_obj)

    # 设置材质 — 半透明绿色
    mat = bpy.data.materials.new(name=f"{MESH_NAME}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.0, 0.9, 0.3, 1.0)
        bsdf.inputs['Alpha'].default_value = 0.5
    mat.blend_method = 'BLEND'
    mesh_obj.data.materials.append(mat)

    # 设置线框显示
    mesh_obj.show_wire = True
    mesh_obj.show_in_front = True

    print(f"[Face468] 网格 {len(verts)} 顶点, {len(tessellation)} 边")

    # ── 2. 创建 468 个 Empty（用于 Rig 驱动） ──
    print(f"[Face468] 创建 {lm_count} 个 Empty …")
    empties = []
    for i in range(lm_count):
        name = f"{PREFIX}_{i:03d}"
        obj = bpy.data.objects.new(name, None)
        coll.objects.link(obj)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.empty_display_size = 0.005
        obj.show_name = False
        obj.location = verts[i]
        empties.append(obj)

    # ── 3. 关键部位标记球 ──
    # MediaPipe landmark 索引 (近似)
    FEATURE_POINTS = {
        'nose_tip':      (1,   (1.0, 0.8, 0.2)),   # 金色鼻尖
        'upper_lip':     (13,  (1.0, 0.2, 0.2)),   # 红上唇
        'lower_lip':     (14,  (1.0, 0.3, 0.3)),   # 红下唇
        'lip_left':      (61,  (1.0, 0.1, 0.1)),   # 深红左嘴角
        'lip_right':     (291, (1.0, 0.1, 0.1)),   # 深红右嘴角
        'left_eye':      (33,  (0.2, 0.6, 1.0)),   # 蓝左眼
        'right_eye':     (263, (0.2, 0.6, 1.0)),   # 蓝右眼
    }
    markers = {}
    for name, (idx, color) in FEATURE_POINTS.items():
        if idx >= lm_count:
            continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004, location=verts[idx])
        sphere = bpy.context.object
        sphere.name = f"{PREFIX}_{name}"
        # 材质
        mat = bpy.data.materials.new(name=f"Marker_{name}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (*color, 1.0)
            bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 2.0
        sphere.data.materials.append(mat)
        markers[name] = sphere
    print(f"[Face468] {len(markers)} 个标记球 (鼻尖/嘴唇/眼角)")

    # ── 4. 场景设置 ──
    bpy.context.scene.render.fps = fps
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = max(len(frames) - 1, 0)

    # ── 5. 逐帧 K 帧：Mesh 顶点 + Empty 位置 + 标记球 ──
    print(f"[Face468] 设置关键帧动画 ({len(frames)} 帧) …")
    print(f"[Face468] ⏳ Mesh 顶点动画较慢，请耐心等待 …")

    for fi, frame_data in enumerate(frames):
        lm_list = frame_data['lm']

        # 更新并 Keyframe Mesh 顶点
        for i, lm in enumerate(lm_list):
            if i >= len(mesh_data.vertices):
                break
            mesh_data.vertices[i].co = mediapipe_to_blender(lm)
        mesh_data.update()
        # 逐顶点 K 帧
        for v in mesh_data.vertices:
            v.keyframe_insert(data_path="co", frame=fi)

        # 更新并 Keyframe Empty
        for i, lm in enumerate(lm_list):
            if i >= len(empties):
                break
            empties[i].location = mediapipe_to_blender(lm)
            empties[i].keyframe_insert(data_path="location", frame=fi)

        # 更新并 Keyframe 标记球
        for name, (idx, _) in FEATURE_POINTS.items():
            if name in markers and idx < len(lm_list):
                markers[name].location = mediapipe_to_blender(lm_list[idx])
                markers[name].keyframe_insert(data_path="location", frame=fi)

        if (fi + 1) % 50 == 0 or fi == len(frames) - 1:
            print(f"  … {fi + 1}/{len(frames)} 帧")

    # 恢复网格到首帧
    for i, lm in enumerate(frames[0]['lm']):
        if i < len(mesh_data.vertices):
            mesh_data.vertices[i].co = mediapipe_to_blender(lm)
    mesh_data.update()

    # ── 5. 插值类型 ──
    def set_interp(action):
        curves = getattr(action, 'fcurves', None)
        if curves is None:
            curves = getattr(action, 'curves', None)
        if curves is None:
            return
        for fc in curves:
            for kp in fc.keyframe_points:
                kp.interpolation = INTERPOLATION

    try:
        for obj in empties:
            if obj.animation_data and obj.animation_data.action:
                set_interp(obj.animation_data.action)
        if mesh_data.animation_data and mesh_data.animation_data.action:
            set_interp(mesh_data.animation_data.action)
    except Exception as e:
        print(f"[Face468] ⚠ 插值设置跳过: {e}")

    # ── 6. 选中网格，跳到首帧 ──
    bpy.context.scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    print(f"[Face468] ✅ 完成 — 1 面部网格 + {len(empties)} Empty, {len(frames)} 帧")
    print(f"[Face468] 💡 按空格键播放 / 选中 FaceMesh 在视图中缩放查看")


# ═══════════════════════════════════════════════
#  自动监听 (WATCH_MODE)
# ═══════════════════════════════════════════════

_watch_last_mtime = 0.0


def watch_loop():
    """bpy.app.timers 回调：检测文件 mtime 变化并自动重载。"""
    global _watch_last_mtime
    try:
        mtime = os.path.getmtime(WATCH_PATH)
        if mtime > _watch_last_mtime:
            _watch_last_mtime = mtime
            print(f"[Face468] 🔄 文件更新，自动重载 …")
            load_and_animate(WATCH_PATH)
    except FileNotFoundError:
        pass
    return WATCH_INTERVAL


# ═══════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════

def main():
    bpy.utils.register_class(Face468_OT_Import)

    if WATCH_MODE:
        global _watch_last_mtime
        _watch_last_mtime = os.path.getmtime(WATCH_PATH) if os.path.exists(WATCH_PATH) else 0
        print(f"[Face468] 👁 监听模式 — {WATCH_PATH}")
        if os.path.exists(WATCH_PATH):
            load_and_animate(WATCH_PATH)
        else:
            print(f"[Face468] ⚠ 文件不存在，等待首次导出 …")
        bpy.app.timers.register(watch_loop)
    else:
        print("[Face468] 📂 请选择 face_capture.json …")
        bpy.ops.import_test.face468('INVOKE_DEFAULT')


if __name__ == "__main__":
    main()

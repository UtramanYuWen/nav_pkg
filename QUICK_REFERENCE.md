# 🎯 nav_pkg 快速参考卡

## 📍 地图切换四种方式

### 方式 1️⃣ ：自动加载最新地图（推荐）
```bash
# 系统自动扫描并加载最新的地图
# 配置: config/voice_nav_params.yaml → auto_load_latest_map: true
roslaunch nav_pkg voice_nav_simple.launch
```

### 方式 2️⃣ ：查看并切换到指定地图
```bash
# 列出所有可用地图
rosrun nav_pkg switch_map.py --list

# 切换到最新地图
rosrun nav_pkg switch_map.py --latest

# 切换到指定地图
rosrun nav_pkg switch_map.py map_20250213_120000

# 查看当前地图
rosrun nav_pkg switch_map.py --current
```

### 方式 3️⃣ ：修改配置文件（永久改变）
```bash
# 编辑配置文件
vim ~/catkin_ws/src/nav_pkg/config/voice_nav_params.yaml

# 修改以下部分:
# voice_navigation_manager:
#   semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints/map_YYYYMMDD_HHMMSS"
#   auto_load_latest_map: false

# 保存后重新启动
roslaunch nav_pkg voice_nav_simple.launch
```

### 方式 4️⃣ ：启动时通过参数指定
```bash
# 一次性使用某个地图
roslaunch nav_pkg voice_nav_simple.launch \
  semantic_maps_path:=/home/robot/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/map_20250213_120000
```

---

## 🗂️ 文件结构一览

```
nav_pkg/
├── README.md                              ← 从这里开始
├── XFYUN_WATERPLUS_GUIDE.md               ← 🎤 讯飞语音配置 (必读!)
├── PROJECT_UPLOAD_GUIDE.md                ← 地图切换详细指南
├── PROJECT_CLEANUP_COMPLETE.md            ← 项目整理总结
├── ARCHITECTURE.md                        ← 系统架构说明
│
├── config/voice_nav_params.yaml           ← ⭐ 主配置文件
├── scripts/switch_map.py                  ← ⭐ 地图切换工具
├── scripts/voice_nav_manager.py           ← 地图和导航管理
├── scripts/speech_recognition_node.py     ← 🎤 语音识别 (调用iat_node)
│
└── launch/voice_nav_simple.launch         ← ⭐ 推荐启动文件
```

---

## 🚀 常用命令速查表

| 任务 | 命令 |
|------|------|
| 启动系统 | `roslaunch nav_pkg voice_nav_simple.launch` |
| 查看可用地图 | `rosrun nav_pkg switch_map.py --list` |
| 切换到最新地图 | `rosrun nav_pkg switch_map.py --latest` |
| 切换到指定地图 | `rosrun nav_pkg switch_map.py map_20250213_120000` |
| 查看当前地图 | `rosrun nav_pkg switch_map.py --current` |
| 语法检查 | `roslaunch nav_pkg voice_nav_simple.launch --dry-run` |
| 检查系统环境 | `bash system_check.sh` |

---

## 🎤 语音命令示例

```
支持的房间名称 (说以下任一个):
• "去卧室" / "卧室" / "bedroom"
• "去客厅" / "客厅" / "living room"
• "去厨房" / "厨房" / "kitchen"
• "去卫生间" / "卫生间" / "bathroom"
• "去书房" / "书房" / "study"
• ...等60+个房间别名

例: "我想去卧室" → 机器人开始导航到卧室
```

---

## 🔗 与 clip_sam_semantic_mapping 集成

**自动扫描地图位置**:
```
~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/
  ├── map_20250210_100000/
  │   ├── waypoints.xml     ← 房间坐标
  │   ├── map.yaml
  │   └── map.pgm
  ├── map_20250211_150000/
  └── map_20250213_120000/
```

**配置位置**:
```
config/voice_nav_params.yaml 第59行:
  semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints"
```

---

## 💡 关键参数说明

### voice_nav_params.yaml 中的关键设置

```yaml
voice_navigation_manager:
  # 地图源路径 (必配)
  semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints"
  
  # 是否自动加载最新地图 (推荐: true)
  auto_load_latest_map: true
  
  # 导航超时时间 (秒)
  navigation_timeout: 60
  
  # 地图检查间隔 (秒)
  map_discovery_interval: 10
```

### 修改后需要重启系统
```bash
# 修改配置后执行
roslaunch nav_pkg voice_nav_simple.launch
```

---

## ⚙️ 项目配置文件清单

| 配置文件 | 用途 | 是否需要修改 |
|---------|------|-----------|
| `voice_nav_params.yaml` | 系统主配置 | ⚡ 可能 |
| `costmap_common_params.yaml` | 代价地图参数 | ❌ 通常不需要 |
| `global_costmap_params.yaml` | 全局规划参数 | ❌ 通常不需要 |
| `local_costmap_params.yaml` | 局部规划参数 | ❌ 通常不需要 |
| `planner_params.yaml` | 规划器参数 | ❌ 通常不需要 |

---

## 🎯 最常见的使用场景

### 场景1: 生成新地图后，自动使用最新版本
```bash
# 1. 生成地图
roslaunch clip_sam_semantic_mapping wpb_stage_robocup_custom.launch

# 2. 启动语音导航（自动使用最新地图）
roslaunch nav_pkg voice_nav_simple.launch

# 完成！系统会自动加载最新生成的map_YYYYMMDD_HHMMSS
```

### 场景2: 切换回之前的某个地图版本
```bash
# 1. 查看旧版本地图
rosrun nav_pkg switch_map.py --list

# 2. 切换到旧版本
rosrun nav_pkg switch_map.py map_20250210_100000

# 3. 重新启动导航
roslaunch nav_pkg voice_nav_simple.launch
```

### 场景3: 对比两个不同的地图版本
```bash
# 终端1: 使用地图版本A
export XFYUN_APP_ID="xxx" XFYUN_API_KEY="xxx"
roslaunch nav_pkg voice_nav_simple.launch

# 终端2: 使用地图版本B (修改配置后)
export XFYUN_APP_ID="xxx" XFYUN_API_KEY="xxx"
roslaunch nav_pkg voice_nav_simple.launch
```

---

## 📋 文件重要性排序

### ⭐⭐⭐⭐⭐ 必须了解
1. `README.md` - 项目简介
2. **`XFYUN_WATERPLUS_GUIDE.md`** - 🎤 讯飞语音配置 (首次必读!)
3. `config/voice_nav_params.yaml` - 主配置
4. `launch/voice_nav_simple.launch` - 启动文件
5. `scripts/switch_map.py` - 地图切换工具

### ⭐⭐⭐ 应该了解
6. `PROJECT_UPLOAD_GUIDE.md` - 地图切换详细指南
7. `scripts/voice_nav_manager.py` - 导航管理
8. `scripts/speech_recognition_node.py` - 语音识别 (使用iat_node)

### ⭐⭐ 参考
9. `ARCHITECTURE.md` - 系统架构
10. `PROJECT_CLEANUP_COMPLETE.md` - 项目总结

---

## 🆘 快速排查

| 问题 | 解决方案 |
|------|---------|
| **讯飞凭证错误** | 详见 `XFYUN_WATERPLUS_GUIDE.md` 的"配置步骤"部分 |
| **iat_node找不到** | 运行 `catkin_make` 编译xfyun_waterplus包 |
| **语音不识别** | 1) 检查凭证; 2) 检查麦克风; 3) 查看 `XFYUN_WATERPLUS_GUIDE.md` FAQ |
| 找不到地图 | 运行 `rosrun nav_pkg switch_map.py --list` 检查 |
| 系统启动失败 | 运行 `bash system_check.sh` 检查环境 |
| 导航不工作 | 检查地图是否加载成功 |
| TF框架错误 | 已在launch文件中修复，无需处理 |

---

## 🎤 讯飞语音快速配置

```bash
# 1️⃣ 从官网获取凭证 (首次)
# https://www.xfyun.cn/ → 注册 → 创建应用 → 获取APP_ID/API_KEY/API_SECRET

# 2️⃣ 编辑 ~/.bashrc
nano ~/.bashrc

# 添加以下三行:
export XFYUN_APP_ID="your_app_id"
export XFYUN_API_KEY="your_api_key"
export XFYUN_API_SECRET="your_api_secret"

# 3️⃣ 应用配置
source ~/.bashrc

# 4️⃣ 编译项目
cd ~/catkin_ws && catkin_make

# 5️⃣ 启动系统
roslaunch nav_pkg voice_nav_simple.launch

# 详细文档见: XFYUN_WATERPLUS_GUIDE.md
```

## 📞 重要链接

- **讯飞官网**: https://www.xfyun.cn/ (获取API凭证)
- **地图生成项目**: https://github.com/UtramanYuWen/clip_sam_semantic_mapping
- **ROS文档**: http://wiki.ros.org/

---

**更多详细信息见各文档头部！** 📚

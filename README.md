# 🎤 nav_pkg - ROS语音导航系统

**集成讯飞IAT语音识别 + ROS Move_Base导航 + clip_sam语义地图**

一个完整的语音导航解决方案，与 [`clip_sam_semantic_mapping`](https://github.com/UtramanYuWen/clip_sam_semantic_mapping) 紧密配合。
- 自动扫描和加载clip_sam生成的语义地图
- 支持多个地图版本管理
- 实时语音控制机器人导航

## ⚡ 30秒快速开始

**无需API凭证配置！** 系统内置讯飞凭证支持，开箱即用 ✅

```bash
# 1. 启动语音导航（自动加载最新的clip_sam地图）
roslaunch nav_pkg voice_nav_simple.launch

# 2. 等待系统初始化（约10秒）
#    系统将自动扫描 ~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/
#    并加载最新的地图版本

# 3. 对着麦克风说话
# "去卧室"  → 机器人自动导航到卧室
# "去客厅"  → 机器人自动导航到客厅
# "我看不清楚" → 系统提取不到房间名称，可再试一遍
```

> 💡 **新增**: 系统支持零配置启动！不需要从讯飞官网获取API凭证也能使用

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🎤 **语音识别** | 讯飞IAT实时中文识别 |
| 🏠 **房间理解** | 支持60+个房间别名 |
| 🗺️ **多版本地图** | 自动加载clip_sam生成的地图 |
| 🤖 **智能导航** | Move_Base + DWA避障 |
| 🔄 **地图切换** | `switch_map.py` 快速切换版本 |

## 📂 项目结构

```
nav_pkg/
├── scripts/                    # 核心脚本
│   ├── speech_recognition_node.py      讯飞IAT语音识别
│   ├── semantic_room_extractor.py      房间关键词提取
│   ├── voice_nav_manager.py            导航管理
│   └── switch_map.py                   地图版本切换
├── config/                     # 配置文件
│   └── voice_nav_params.yaml           主配置
├── launch/                     # 启动文件
│   ├── voice_nav_simple.launch         推荐使用
│   └── voice_nav_complete.launch       完整版
└── rviz/                       # 可视化
    └── nav.rviz                导航可视化
```

## 🗺️ 地图版本切换

```bash
# 1. 查看所有可用地图
rosrun nav_pkg switch_map.py --list

# 2. 切换到最新地图
rosrun nav_pkg switch_map.py --latest

# 3. 切换到指定地图
rosrun nav_pkg switch_map.py map_20250213_120000

# 详细说明见: PROJECT_UPLOAD_GUIDE.md
```

## 🔧 安装和配置

### 系统依赖
```bash
# ROS导航依赖
sudo apt-get install ros-noetic-move-base ros-noetic-dwa-local-planner

# 讯飞SDK依赖 (xfyun_waterplus包已包含)
cd ~/catkin_ws && catkin_make
```

### 讯飞凭证配置 (可选)

> 📌 **注意**: 如果xfyun_waterplus已内置默认凭证或你的系统已配置，可以跳过此步骤

如需使用自己的讯飞API凭证，详见 **[XFYUN_WATERPLUS_GUIDE.md](XFYUN_WATERPLUS_GUIDE.md)**：

```bash
# 1. 从讯飞官网 https://www.xfyun.cn/ 获取凭证 (可选)

# 2. 编辑 ~/.bashrc 添加:
export XFYUN_APP_ID="your_app_id"
export XFYUN_API_KEY="your_api_key"
export XFYUN_API_SECRET="your_api_secret"

# 3. 应用配置
source ~/.bashrc
```

系统会优先使用环境变量中的凭证，如果未设置则使用内置或系统配置。

## 📚 详细文档

| 文档 | 用途 |
|------|------|
| **[XFYUN_WATERPLUS_GUIDE.md](XFYUN_WATERPLUS_GUIDE.md)** | 🎤 讯飞语音识别完整指南 |
| **PROJECT_UPLOAD_GUIDE.md** | 📍 地图切换完整指南 |
| **ARCHITECTURE.md** | 📋 系统架构设计 |
| **PROJECT_CLEANUP_COMPLETE.md** | ✅ 项目整理总结 |

## 🎯 支持的房间

客厅、卧室、厨房、卫生间、书房、餐厅、走廊、办公室等60+种房间。

## 🔗 与clip_sam_semantic_mapping的关系

### 工作流程

```
clip_sam_semantic_mapping (上游项目)
    ↓
生成语义地图: results/waypoints/map_YYYYMMDD_HHMMSS/
    ├─ waypoints.xml (房间定义)
    ├─ map.yaml + map.pgm (地图文件)
    └─ map.json (元数据)
    ↓
nav_pkg (本项目, 下游应用)
    ├─ 自动扫描检测地图
    ├─ 支持多版本管理
    ├─ 语音导航到房间
    └─ 实时地图切换
```

### 配置说明

在 `config/voice_nav_params.yaml` 中配置clip_sam路径：

```yaml
voice_navigation_manager:
  semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints"
  auto_load_latest_map: true
```

### 依赖关系

- **必须**: clip_sam_semantic_mapping 已生成至少一个地图版本
- **位置**: `~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/`
- **格式**: `map_YYYYMMDD_HHMMSS/` 目录结构

## 🆘 故障排除

```bash
# 检查系统环境
bash system_check.sh

# 查看项目清理说明
cat PROJECT_CLEANUP_COMPLETE.md

# 查看地图切换指南
cat PROJECT_UPLOAD_GUIDE.md
```

## 🤝 与clip_sam_semantic_mapping的协作

两个项目配合实现完整的**语义地图导航系统**：

| 项目 | 功能 | 输出 |
|------|------|------|
| [clip_sam_semantic_mapping](https://github.com/UtramanYuWen/clip_sam_semantic_mapping) | 生成语义地图和房间定义 | `results/waypoints/map_*` |
| nav_pkg (本项目) | 语音导航到指定房间 | 机器人自动导航执行 |

### 实际工作流程

```bash
# 1. clip_sam生成地图
cd ~/catkin_ws/src/clip_sam_semantic_mapping
python3 clip_sam.py --scene_name "my_home"
# 输出: results/waypoints/map_20250115_143022/

# 2. nav_pkg自动检测和加载
cd ~/catkin_ws
roslaunch nav_pkg voice_nav_simple.launch
# 自动使用最新地图

# 3. 用户语音导航
# 说: "去卧室"
# 系统自动: 识别 → 提取房间 → 规划路径 → 执行导航
```

## 📊 项目信息

| 项 | 值 |
|----|---|
| 文件数 | 13 |
| 项目大小 | ~150 KB |
| Python脚本 | 5 |
| 配置文件 | 5 |
| 启动文件 | 2 |
| 文档文件 | 4 |
| 完成度 | 100% ✅ |

## 📝 许可证

[Apache 2.0](LICENSE)

---

**现在就开始使用语音控制您的机器人吧！** 🚀

#### 相关项目
- 📦 [clip_sam_semantic_mapping](https://github.com/UtramanYuWen/clip_sam_semantic_mapping) - 语义地图生成
- 🎤 [讯飞开发平台](https://www.xfyun.cn/) - 语音识别API
- 🤖 [ROS](http://wiki.ros.org/) - 机器人操作系统

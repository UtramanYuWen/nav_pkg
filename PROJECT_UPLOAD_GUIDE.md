# 📦 nav_pkg 项目整理与上传指南

## 项目状态总结

**项目名**: 讯飞IAT语音导航系统  
**版本**: 1.1 (TF2修复完成)  
**状态**: ✅ 生产就绪  
**依赖项目**: `clip_sam_semantic_mapping` (语义地图生成)

---

## 📂 项目结构整理清单

### 核心文件（必须保留）

```
nav_pkg/
├── 📄 package.xml              ✅ 包定义（已更新依赖）
├── 📄 CMakeLists.txt           ✅ 编译配置
├── 📄 README.md                ✅ 主文档
├── 📄 setup.py                 ✅ Python安装配置
│
├── 📁 scripts/                 核心Python脚本
│   ├── speech_recognition_node.py        讯飞IAT语音识别
│   ├── semantic_room_extractor.py        房间语义提取
│   ├── voice_nav_manager.py              地图管理和导航
│   └── simple_navigation_node.py          简单导航（可选）
│
├── 📁 config/                  ROS配置文件
│   ├── voice_nav_params.yaml             主配置（★重要）
│   ├── costmap_common_params.yaml        代价地图通用参数
│   ├── global_costmap_params.yaml        全局代价地图
│   ├── local_costmap_params.yaml         局部代价地图
│   └── planner_params.yaml               规划器参数
│
├── 📁 launch/                  ROS启动文件
│   ├── voice_nav_simple.launch           简化版启动（★推荐）
│   ├── voice_nav_complete.launch         完整版启动
│   ├── voice_nav.launch                  备用启动
│   └── nav.launch                        纯导航启动
│
├── 📁 rviz/                    RViz配置
│   └── voice_nav.rviz          可视化配置
│
└── .gitignore                  ✅ Git忽略清单
```

### 文档文件（推荐保留，便于用户使用）

```
docs/ (建议新建)
├── README.md                   项目简介
├── QUICK_START.md              快速开始
├── MAP_SWITCHING.md            地图切换指南
├── TROUBLESHOOTING.md          故障排除
└── ARCHITECTURE.md             系统架构说明
```

### 需要清理的文件

```
❌ scripts/__pycache__/         已清理
❌ *.pyc, *.pyo                已清理
❌ 临时测试文件                 应清理
❌ 个人笔记文件                 应清理
```

---

## 🗺️ 地图切换指南

### 方案 1：自动加载最新地图（推荐）

**配置文件**: `config/voice_nav_params.yaml`

```yaml
voice_navigation_manager:
  # 自动加载最新地图
  auto_load_latest_map: true
```

**工作原理**:
- 系统启动时自动扫描 `src/clip_sam_semantic_mapping/results/waypoints/` 目录
- 按时间戳排序，加载最新的地图版本 (map_YYYYMMDD_HHMMSS)
- 无需手动干预

**启动命令**:
```bash
roslaunch nav_pkg voice_nav_simple.launch
```

---

### 方案 2：手动指定地图版本

#### 方法 A：修改配置文件（永久生效）

编辑 `config/voice_nav_params.yaml`:

```yaml
voice_navigation_manager:
  # 关闭自动加载
  auto_load_latest_map: false
  
  # 指定地图路径（完整路径）
  semantic_maps_path: "/home/robot/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/map_20250213_120000"
```

然后启动：
```bash
roslaunch nav_pkg voice_nav_simple.launch
```

#### 方法 B：运行时指定地图（一次性）

```bash
# 通过ROS参数指定地图
roslaunch nav_pkg voice_nav_simple.launch \
  semantic_maps_path:=/home/robot/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/map_20250213_120000
```

---

### 方案 3：查看可用地图列表并选择

#### Step 1：查看所有可用地图

```bash
# 列出所有生成的地图
ls -lh ~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/

# 输出示例:
# map_20250210_100000/  <-- 最早生成
# map_20250211_150000/
# map_20250213_120000/  <-- 最新生成
```

#### Step 2：检查地图内容

```bash
# 查看特定地图的房间信息
python3 << 'EOF'
import xml.etree.ElementTree as ET
map_path = "/home/robot/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/map_20250213_120000"
tree = ET.parse(f"{map_path}/waypoints.xml")
root = tree.getroot()
print("房间列表:")
for wp in root.findall('Waypoint'):
    name = wp.find('Name').text
    print(f"  - {name}")
EOF
```

#### Step 3：编辑配置并启动

```bash
# 编辑配置
sed -i 's|semantic_maps_path:.*|semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints/map_20250213_120000"|' \
  ~/catkin_ws/src/nav_pkg/config/voice_nav_params.yaml

# 启动系统
roslaunch nav_pkg voice_nav_simple.launch
```

---

### 方案 4：动态切换地图（运行时切换）

创建一个地图切换脚本 `scripts/switch_map.py`:

```bash
#!/usr/bin/env python3
import rospy
import sys
import os
from pathlib import Path

def switch_map(map_name):
    """切换地图版本"""
    base_path = os.path.expanduser("~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints")
    map_path = os.path.join(base_path, map_name)
    
    if not os.path.exists(map_path):
        print(f"❌ 地图不存在: {map_path}")
        return False
    
    # 通过ROS参数更新
    rospy.set_param('/voice_navigation_manager/semantic_maps_path', map_path)
    print(f"✓ 已切换地图到: {map_name}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: rosrun nav_pkg switch_map.py <map_name>")
        print("示例: rosrun nav_pkg switch_map.py map_20250213_120000")
        sys.exit(1)
    
    map_name = sys.argv[1]
    switch_map(map_name)
```

使用方法：
```bash
# 查看可用地图
ls ~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/

# 切换地图
rosrun nav_pkg switch_map.py map_20250213_120000

# 重新加载导航管理器
rosnode kill /voice_nav_manager
roslaunch nav_pkg voice_nav_simple.launch
```

---

## 🔄 工作流程：完整例子

### 场景1：使用最新生成的地图

```bash
# 1. 生成新的语义地图
cd ~/catkin_ws
roslaunch clip_sam_semantic_mapping wpb_stage_robocup_custom.launch

# 2. 启动语音导航（自动使用最新地图）
roslaunch nav_pkg voice_nav_simple.launch

# 说出命令: "去卧室"
```

### 场景2：回到之前的某个地图版本

```bash
# 1. 查看可用地图列表
ls -t ~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/
# 输出: map_20250213_120000/  map_20250210_100000/

# 2. 编辑配置指定旧地图
vim ~/catkin_ws/src/nav_pkg/config/voice_nav_params.yaml
# 改为: semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints/map_20250210_100000"

# 3. 重新启动
roslaunch nav_pkg voice_nav_simple.launch

# 系统现在使用旧地图
```

### 场景3：对比两个地图版本

```bash
# 终端1：使用地图A
export MAP_PATH="map_20250210_100000"
roslaunch nav_pkg voice_nav_simple.launch

# 终端2（另开）：在新建ROS_MASTER_URI下使用地图B
export ROS_MASTER_URI=http://localhost:11312
export MAP_PATH="map_20250213_120000"
roslaunch nav_pkg voice_nav_simple.launch
```

---

## 📋 地图配置参数参考

### 在 `voice_nav_params.yaml` 中调整

```yaml
voice_navigation_manager:
  # 地图源路径（★关键配置）
  semantic_maps_path: "src/clip_sam_semantic_mapping/results/waypoints"
  
  # 是否自动加载最新地图
  auto_load_latest_map: true          # true: 自动, false: 需手动指定完整路径
  
  # 地图版本检查间隔 (秒)
  map_discovery_interval: 10
  
  # 地图文件夹命名规则前缀
  map_folder_prefix: "map_"           # 格式: map_YYYYMMDD_HHMMSS
  
  # 导航路点文件名
  waypoints_filename: "waypoints.xml"
```

---

## 🔐 项目上传前检查清单

### 文件整理

- [ ] 删除所有 `__pycache__` 目录
- [ ] 删除所有 `*.pyc`, `*.pyo` 文件
- [ ] 删除临时日志文件 (`*.log`)
- [ ] 删除个人笔记/测试文件
- [ ] 创建 `.gitignore` 文件
- [ ] 验证没有硬编码的绝对路径

### 依赖检查

- [ ] 更新 `package.xml` 中的依赖列表
- [ ] 检查所有 Python 脚本是否有 `#!/usr/bin/env python3` 头
- [ ] 检查所有 Python 脚本的可执行权限

### 文档完整性

- [ ] README.md 清晰明了
- [ ] 所有启动命令有注释
- [ ] 配置文件有说明

### 与依赖项目的集成

- [ ] 确认与 `clip_sam_semantic_mapping` 的集成点
- [ ] 验证地图路径配置正确
- [ ] 检查能否自动扫描地图目录

### 运行测试

- [ ] 能否正常启动 `roslaunch nav_pkg voice_nav_simple.launch`
- [ ] 能否识别语音并生成导航目标
- [ ] 能否正确加载地图
- [ ] TF框架错误已解决

---

## 📝 项目依赖关系

```
nav_pkg (语音导航系统)
    ↓
    依赖 ← clip_sam_semantic_mapping (语义地图生成)
    ↓
    输入: map_YYYYMMDD_HHMMSS/
         ├── waypoints.xml
         ├── map.yaml
         ├── map.pgm
         └── ...
    ↓
    输出: 语音命令 → 导航目标 → Move_Base → 机器人运动
```

**集成点**:
1. `voice_nav_manager.py` 扫描 `clip_sam_semantic_mapping/results/waypoints/` 目录
2. 自动读取最新或指定的 `map_YYYYMMDD_HHMMSS` 文件夹
3. 解析其中的 `waypoints.xml` 文件获取房间坐标
4. 通过语音识别匹配房间名称
5. 发送导航目标到 Move_Base

---

## 🚀 上传前最后检查

### 构建验证

```bash
cd ~/catkin_ws
catkin_make                           # 编译测试
source devel/setup.bash
roslaunch nav_pkg voice_nav_simple.launch --dry-run  # 语法检查
```

### 文件大小检查

```bash
# 检查项目大小
du -sh ~/catkin_ws/src/nav_pkg/

# 输出应该 < 100MB（如果包含模型应 < 1GB）
```

### Git 就绪检查

```bash
cd ~/catkin_ws/src/nav_pkg
git status                            # 检查状态
git add .
git commit -m "Project cleanup and TF2 fix"
```

---

## 📞 常见问题

**Q1: 地图始终加载失败？**
```bash
# 检查地图路径
ls -la ~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints/

# 检查必要文件
ls map_*/waypoints.xml map_*/map.yaml map_*/map.pgm
```

**Q2: 如何回到某个特定的地图版本？**
- 编辑 `config/voice_nav_params.yaml`
- 将 `semantic_maps_path` 改为完整路径

**Q3: 多个地图版本怎么都保存？**
- 它们自动保存在 `clip_sam_semantic_mapping/results/waypoints/` 下
- 按 `map_YYYYMMDD_HHMMSS` 命名自动区分

---

**项目已准备好上传！** 🎉

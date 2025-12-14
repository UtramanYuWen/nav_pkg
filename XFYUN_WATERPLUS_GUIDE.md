# 讯飞语音识别集成说明

## 概述

本项目使用 **xfyun_waterplus** 包提供讯飞IAT (Intelligent Audio Technology) 实时语音听写功能。

### 系统架构

```
麦克风输入
    ↓
xfyun_waterplus iat_node (C++ 程序)
    ├─ 调用讯飞云服务
    └─ 发布到 /xfyun/iat 话题
    ↓
speech_recognition_node.py (Python)
    ├─ 订阅 /xfyun/iat
    └─ 发布到 /speech_recognition/text
    ↓
semantic_room_extractor.py (Python)
    └─ 提取房间名称
    ↓
voice_nav_manager.py (Python)
    └─ 导航到目标房间
```

---

## 依赖说明

### 1. 项目依赖 (package.xml)

```xml
<!-- 讯飞语音识别依赖 - 使用xfyun_waterplus包 -->
<exec_depend>xfyun_waterplus</exec_depend>
```

### 2. xfyun_waterplus 包

位置: `/home/robot/catkin_ws/src/xfyun_waterplus`

该包包含:
- `iat_node` - 讯飞IAT C++可执行程序
- 讯飞SDK库
- 相关配置文件

### 3. 编译要求

```bash
# 第一次编译时需要编译xfyun_waterplus
cd ~/catkin_ws
catkin_make

# 编译完成后的二进制文件位置
~/catkin_ws/devel/lib/xfyun_waterplus/iat_node
```

---

## 配置步骤

### 步骤1: 凭证配置 (可选)

> 📌 **重要**: xfyun_waterplus包通常包含内置凭证或系统级配置，**默认情况下无需手动配置** 

**如果你需要使用自己的凭证** (例如换用自己的讯飞API账户)，请按如下步骤操作:

访问 https://www.xfyun.cn/ 并完成:

1. 注册账号
2. 实名认证  
3. 创建应用 (选择"语音听写"业务)
4. 获取凭证:
   - `XFYUN_APP_ID`
   - `XFYUN_API_KEY`
   - `XFYUN_API_SECRET`

### 步骤2: 设置环境变量 (仅当需要自定义凭证时)

编辑 `~/.bashrc`:

```bash
nano ~/.bashrc

# 在文件末尾添加:
export XFYUN_APP_ID="your_app_id_here"
export XFYUN_API_KEY="your_api_key_here"
export XFYUN_API_SECRET="your_api_secret_here"

# 保存并应用
source ~/.bashrc
```

### 步骤3: 验证环境变量 (可选)

```bash
# 查看是否设置了自定义凭证
echo "APP_ID: ${XFYUN_APP_ID:-[使用系统内置]}"
echo "API_KEY: ${XFYUN_API_KEY:-[使用系统内置]}"
echo "API_SECRET: ${XFYUN_API_SECRET:-[使用系统内置]}"

# 若显示 [使用系统内置] 则表示系统使用内置凭证
```

### 步骤4: 编译项目

```bash
cd ~/catkin_ws
catkin_make

# 或只编译nav_pkg
catkin_make -DCATKIN_WHITELIST_PACKAGES="nav_pkg;xfyun_waterplus"
```

---

## 启动系统

### 方案A: 启动导航系统 (推荐)

```bash
# 终端1: 启动ROS master
roscore

# 终端2: 启动完整的语音导航系统
roslaunch nav_pkg voice_nav_complete.launch
```

### 方案B: 启动简化版本

```bash
# 只启动语音识别和导航管理器，不启动Gazebo仿真
roslaunch nav_pkg voice_nav_simple.launch
```

---

## 文件组成

### 核心文件

| 文件 | 说明 | 来源 |
|------|------|------|
| `launch/voice_nav_simple.launch` | 简化版launch | nav_pkg |
| `launch/voice_nav_complete.launch` | 完整版launch | nav_pkg |
| `scripts/speech_recognition_node.py` | 语音识别节点 | nav_pkg |
| `scripts/semantic_room_extractor.py` | 房间提取器 | nav_pkg |
| `scripts/voice_nav_manager.py` | 导航管理器 | nav_pkg |
| `config/voice_nav_params.yaml` | 参数配置 | nav_pkg |

### 讯飞相关文件

| 文件 | 说明 | 来源 |
|------|------|------|
| `src/xfyun_waterplus/src/iat_node.cpp` | 讯飞IAT程序源码 | xfyun_waterplus |
| `devel/lib/xfyun_waterplus/iat_node` | 编译后的可执行文件 | xfyun_waterplus (编译) |
| `config/xfyun_config.yaml` | 讯飞配置模板 | nav_pkg |

---

## 话题说明

### 讯飞输出

```
话题: /xfyun/iat
类型: std_msgs/String
内容: 识别结果文本 (中文)
例子: "去卧室" / "返回客厅" / "停止"
```

### 识别节点输出

```
话题: /speech_recognition/text
类型: std_msgs/String
内容: 经过处理的识别结果
```

### 房间提取输出

```
话题: /semantic_room_extractor/room_command
类型: std_msgs/String
内容: 提取的房间名称或命令
例子: "bedroom" / "living_room"
```

---

---

## 凭证工作原理

### 凭证来源（优先级从高到低）

1. **用户环境变量** - 最高优先级
   - 如果设置了 `XFYUN_APP_ID` 等环境变量，将使用这些凭证

2. **系统级配置** - 中等优先级  
   - xfyun_waterplus可能有系统级配置文件

3. **内置凭证** - 最低优先级
   - xfyun_waterplus二进制文件可能包含内置的演示/开发凭证

### 为什么不设置凭证也能使用？

xfyun_waterplus包通常包含：
- 内置的演示凭证，用于开发和测试
- 或系统级别已配置的凭证
- 这使得用户无需手动配置即可快速开始

### 何时需要配置自己的凭证？

- 使用了官网获取的正式API账户
- 需要更高的服务量限制
- 需要用自己的账户进行费用计算
- 系统要求验证身份

---

## 常见问题

### Q1: 编译失败，提示找不到xfyun_waterplus

**原因**: 讯飞包未在工作空间中

**解决**:
```bash
# 确保xfyun_waterplus在src目录
ls ~/catkin_ws/src/xfyun_waterplus/

# 如果不存在，需要克隆或复制该包
```

### Q2: 运行iat_node失败，提示"讯飞凭证错误"

**原因**: 内置/系统凭证失效或网络问题

**解决**:
```bash
# 验证凭证
echo $XFYUN_APP_ID
echo $XFYUN_API_KEY

# 重新设置
export XFYUN_APP_ID="correct_id"
export XFYUN_API_KEY="correct_key"
export XFYUN_API_SECRET="correct_secret"
```

### Q3: 无法识别语音

**原因**: 多种可能
- 麦克风未连接或权限不足
- 网络连接不稳定
- 讯飞服务暂时不可用

**解决**:
```bash
# 检查麦克风
arecord -l

# 测试麦克风
arecord -d 5 test.wav
aplay test.wav

# 检查网络
ping iat-api.xfyun.cn
```

### Q4: 节点启动时提示"二进制文件未找到"

**原因**: xfyun_waterplus未编译

**解决**:
```bash
cd ~/catkin_ws
catkin_make -j4
# 等待编译完成
```

---

## 参数配置

### voice_nav_params.yaml 中的讯飞相关配置

```yaml
speech_recognition:
  language: "zh_CN"              # 语言: 中文
  sample_rate: 16000             # 采样率: 16kHz
  recognition_timeout: 10        # 识别超时: 10秒
  confidence_threshold: 0.5       # 信心度阈值
```

---

## 运行示例

### 完整的语音导航演示

```bash
# 1. 启动系统
roslaunch nav_pkg voice_nav_complete.launch

# 2. 等待系统初始化 (1-2秒)

# 3. 在麦克风前说出中文房间名
# 示例:
#   "去卧室" → 机器人导航到卧室
#   "返回客厅" → 机器人返回客厅
#   "导航到厨房" → 机器人前往厨房

# 4. 系统流程:
#   语音 → 讯飞识别 → 房间提取 → 导航执行
```

---

## 依赖清单

### 编译时依赖
- `catkin` - ROS构建系统
- `xfyun_waterplus` - 讯飞C++SDK包

### 运行时依赖
- `xfyun_waterplus` - 提供iat_node可执行文件
- `move_base` - 路径规划和导航
- `amcl` - 定位
- `map_server` - 地图服务

### Python依赖
- `rospy` - ROS Python客户端
- `std_msgs` - ROS标准消息

---

## 故障排查清单

- [ ] `echo $XFYUN_APP_ID` 显示正确的ID
- [ ] xfyun_waterplus编译成功: `ls ~/catkin_ws/devel/lib/xfyun_waterplus/iat_node`
- [ ] 麦克风连接正常: `arecord -l`
- [ ] 网络连通: `ping iat-api.xfyun.cn`
- [ ] 讯飞凭证在https://www.xfyun.cn/官网有效
- [ ] `rostopic echo /xfyun/iat` 能看到识别结果
- [ ] `rostopic echo /speech_recognition/text` 能看到处理后的结果

---

## 重要说明

⚠️ **讯飞凭证安全**:
- 不要将 `XFYUN_APP_ID` 和 `XFYUN_API_KEY` 提交到版本控制系统
- 不要在launch文件中硬编码凭证
- 使用环境变量或配置文件管理凭证

⚠️ **网络要求**:
- 系统需要连接互联网才能使用讯飞云服务
- 不支持离线语音识别
- 考虑网络延迟 (通常100-500ms)

---

**版本**: 1.0  
**最后修改**: 2025-01-15  
**状态**: 生产就绪 ✓

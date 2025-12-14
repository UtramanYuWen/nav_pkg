#!/bin/bash
# 简单的系统检查脚本

echo "🎤 离线语音导航 - 系统检查"
echo ""

# 检查 Pocketsphinx
echo -n "Pocketsphinx... "
if command -v pocketsphinx &> /dev/null; then
    echo "✓ 已安装"
else
    echo "✗ 未安装"
    echo "  安装: sudo apt-get install pocketsphinx"
fi

# 检查 PyAudio
echo -n "PyAudio... "
if python3 -c "import pyaudio" 2>/dev/null; then
    echo "✓ 已安装"
else
    echo "✗ 未安装"
    echo "  安装: sudo apt-get install python3-pyaudio"
fi

# 检查麦克风
echo -n "麦克风... "
if arecord -l 2>/dev/null | grep -q "card"; then
    echo "✓ 已检测"
else
    echo "⚠️  未检测"
fi

# 检查 ROS
echo -n "ROS... "
if [ ! -z "$ROS_DISTRO" ]; then
    echo "✓ $ROS_DISTRO"
else
    echo "⚠️  未加载"
fi

echo ""
echo "✓ 检查完成"

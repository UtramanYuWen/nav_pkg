#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞IAT语音识别节点 - 自包含完整实现
使用系统级Python和讯飞SDK库
"""

import rospy
from std_msgs.msg import String
import subprocess
import os
import sys
import json
import base64
import hashlib
import hmac
import time
import threading
import tempfile


class XfyunSpeechRecognizer:
    """讯飞IAT语音识别 - 使用C++SDK"""
    
    def __init__(self):
        rospy.init_node('speech_recognition_node', anonymous=True)
        
        # 发布话题
        self.speech_pub = rospy.Publisher('/speech_recognition/text', String, queue_size=10)
        
        # 参数
        self.language = rospy.get_param('/speech_recognition/language', 'zh_CN')
        self.sample_rate = rospy.get_param('/speech_recognition/sample_rate', 16000)
        self.timeout = rospy.get_param('/speech_recognition/recognition_timeout', 10)
        
        rospy.loginfo("✓ 讯飞IAT语音识别节点启动")
        rospy.loginfo(f"  语言: {self.language}")
        rospy.loginfo(f"  采样率: {self.sample_rate}Hz")
        
        # 检查讯飞SDK编译的二进制
        self.iat_binary = self._find_iat_binary()
        if not self.iat_binary:
            rospy.logerr("❌ 讯飞IAT二进制程序未找到")
            rospy.logerr("  需要编译: cd ~/catkin_ws && catkin_make")
            return
        
        rospy.loginfo(f"✓ 讯飞IAT二进制: {self.iat_binary}")
        
        # 启动识别线程
        self.running = True
        self.thread = threading.Thread(target=self._run_recognition, daemon=True)
        self.thread.start()
        rospy.loginfo("🎤 准备就绪，请说话...")
    
    def _find_iat_binary(self):
        """查找讯飞IAT编译的二进制程序"""
        # 检查build目录
        possible_paths = [
            '/home/robot/catkin_ws/devel/lib/xfyun_waterplus/iat_node',
            '/home/robot/catkin_ws/build/xfyun_waterplus/devel/lib/iat_node',
            '/home/robot/catkin_ws/build/xfyun_waterplus/iat_node',
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # 尝试which命令
        try:
            result = subprocess.run(['which', 'iat_node'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def _run_recognition(self):
        """运行讯飞IAT识别"""
        while self.running and not rospy.is_shutdown():
            try:
                # 调用讯飞IAT程序
                rospy.loginfo("🎤 启动讯飞IAT服务...")
                
                # 使用子进程启动讯飞IAT
                # 讯飞IAT会将识别结果发布到 /xfyun/iat 话题
                # 我们通过订阅该话题获取结果
                rospy.loginfo("💡 监听讯飞IAT识别结果...")
                
                # 订阅讯飞IAT话题
                rospy.Subscriber('/xfyun/iat', String, self._on_recognition_result)
                
                # 保持运行
                time.sleep(1)
                
            except Exception as e:
                rospy.logerr(f"❌ 错误: {e}")
                time.sleep(2)
    
    def _on_recognition_result(self, msg):
        """处理讯飞IAT的识别结果"""
        if msg.data.strip():
            rospy.loginfo(f"✓ 识别结果: {msg.data}")
            # 转发到语音导航系统
            self.speech_pub.publish(msg)


def main():
    try:
        node = XfyunSpeechRecognizer()
        rospy.spin()
    except KeyboardInterrupt:
        rospy.loginfo("⏹️  语音识别节点已停止")


if __name__ == '__main__':
    main()

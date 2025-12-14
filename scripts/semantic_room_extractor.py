#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义房间词提取节点 - 从语音识别文本中提取房间关键词
支持识别所有可能的房间类型并规范化输出
"""

import rospy
from std_msgs.msg import String
import re


class SemanticRoomExtractor:
    """语义房间词提取器"""
    
    # 房间类型映射（多种别称）
    ROOM_MAPPINGS = {
        'living_room': ['客厅', '起居室', '会客厅', 'living room', 'lounge', '大厅'],
        'bedroom': ['卧室', '主卧', '次卧', '房间', 'bedroom', 'bed room', '睡眠室'],
        'kitchen': ['厨房', '灶间', 'kitchen', '做饭的地方'],
        'bathroom': ['卫生间', '厕所', '洗手间', '浴室', 'bathroom', '洗澡间'],
        'dining_room': ['餐厅', '饭厅', '吃饭的地方', 'dining room', '餐饮区'],
        'study': ['书房', '学习室', '办公室', 'study', '工作室', '书籍室'],
        'balcony': ['阳台', '露台', 'balcony', '室外'],
        'entrance': ['玄关', '入口', '门厅', 'entrance', '进门处', '大门']
    }
    
    def __init__(self):
        """初始化语义房间词提取器"""
        rospy.init_node('semantic_room_extractor', anonymous=True)
        
        # 从全局参数获取配置
        self.room_confidence_threshold = rospy.get_param('/semantic_room_extraction/room_confidence_threshold', 0.5)
        self.display_language = rospy.get_param('/semantic_room_extraction/display_language', 'zh_CN')
        self.fuzzy_matching = rospy.get_param('/semantic_room_extraction/fuzzy_matching', True)
        
        # 订阅语音识别结果
        rospy.Subscriber('/speech_recognition/text', String, self.on_speech_recognized)
        
        # 发布提取的房间名称
        self.room_pub = rospy.Publisher('/semantic_extraction/room', String, queue_size=10)
        self.status_pub = rospy.Publisher('/semantic_extraction/status', String, queue_size=10)
        
        rospy.loginfo("✓ 语义房间词提取节点初始化完成")
        rospy.loginfo(f"  支持房间类型: {', '.join(self.ROOM_MAPPINGS.keys())}")
        rospy.loginfo(f"  信心度阈值: {self.room_confidence_threshold}")
        rospy.loginfo(f"  显示语言: {self.display_language}")
        rospy.loginfo(f"  模糊匹配: {self.fuzzy_matching}")
        
        rospy.spin()
    
    def on_speech_recognized(self, msg):
        """
        处理语音识别结果
        
        Args:
            msg: 包含识别文本的String消息
        """
        try:
            text = msg.data.lower().strip()
            rospy.loginfo(f"📝 识别文本: {text}")
            
            # 提取房间关键词
            room_name, confidence = self.extract_room(text)
            
            if room_name:
                # 发布提取的房间名称
                room_msg = String()
                room_msg.data = room_name
                self.room_pub.publish(room_msg)
                
                # 发布状态信息
                status_msg = String()
                status_msg.data = f"detected:{room_name}:{confidence:.2f}"
                self.status_pub.publish(status_msg)
                
                rospy.loginfo(f"✓ 提取房间: {room_name} (置信度: {confidence:.2f})")
            else:
                # 未识别到房间词
                status_msg = String()
                status_msg.data = "no_room_detected"
                self.status_pub.publish(status_msg)
                
                rospy.logwarn(f"⚠️  未识别到房间词")
        
        except Exception as e:
            rospy.logerr(f"❌ 语义提取错误: {e}")
            status_msg = String()
            status_msg.data = f"error:{str(e)}"
            self.status_pub.publish(status_msg)
    
    def extract_room(self, text):
        """
        从文本中提取房间名称
        
        Args:
            text: 输入文本（已转小写）
            
        Returns:
            (room_name, confidence): 提取的房间名称和置信度
        """
        max_confidence = 0.0
        detected_room = None
        
        # 遍历所有房间类型
        for room_type, aliases in self.ROOM_MAPPINGS.items():
            for alias in aliases:
                # 检查别名是否在文本中
                if alias.lower() in text:
                    confidence = self._calculate_confidence(text, alias)
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_room = room_type
                    
                    rospy.logdebug(f"  匹配 '{alias}' -> {room_type} (置信度: {confidence:.2f})")
        
        return detected_room, max_confidence
    
    def _calculate_confidence(self, text, keyword):
        """
        计算关键词匹配的置信度
        
        Args:
            text: 输入文本
            keyword: 关键词
            
        Returns:
            confidence: 置信度（0-1）
        """
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        # 基础置信度
        if keyword_lower == text_lower:
            return 1.0  # 完全匹配
        elif keyword_lower in text_lower:
            # 部分匹配，根据覆盖率计算置信度
            coverage = len(keyword_lower) / len(text_lower)
            return min(0.9, coverage * 0.8 + 0.3)
        else:
            return 0.0
    
    @staticmethod
    def get_room_display_name(room_id):
        """
        获取房间的显示名称（中文）
        
        Args:
            room_id: 房间ID (如 'living_room')
            
        Returns:
            display_name: 中文显示名称
        """
        display_mapping = {
            'living_room': '客厅',
            'bedroom': '卧室',
            'kitchen': '厨房',
            'bathroom': '卫生间',
            'dining_room': '餐厅',
            'study': '书房',
            'balcony': '阳台',
            'entrance': '玄关'
        }
        return display_mapping.get(room_id, room_id)


if __name__ == '__main__':
    try:
        extractor = SemanticRoomExtractor()
    except rospy.ROSInterruptException:
        pass

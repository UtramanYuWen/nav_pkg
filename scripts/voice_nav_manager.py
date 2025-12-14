#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音导航管理器 - 管理多个地图版本和语音导航
支持：
  1. 扫描clip_sam_semantic_mapping生成的多个地图版本
  2. 通过语音命令选择地图
  3. 基于语义房间词进行导航
  4. 发布导航目标到move_base
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
import os
import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class VoiceNavManager:
    """语音导航管理器"""
    
    def __init__(self):
        """初始化语音导航管理器"""
        rospy.init_node('voice_nav_manager', anonymous=True)
        
        # 从全局参数获取配置
        maps_path = rospy.get_param(
            '/voice_navigation_manager/semantic_maps_path',
            'src/clip_sam_semantic_mapping/results/waypoints'
        )
        
        # 处理路径：支持相对路径和绝对路径
        if maps_path.startswith('/'):
            # 绝对路径
            self.semantic_maps_base = maps_path
        elif maps_path.startswith('~'):
            # 家目录路径
            self.semantic_maps_base = os.path.expanduser(maps_path)
        else:
            # 相对于ROS工作空间的路径
            ros_workspace = os.environ.get('ROS_WORKSPACE', os.path.expanduser('~/catkin_ws'))
            self.semantic_maps_base = os.path.join(ros_workspace, maps_path)
        
        self.map_discovery_interval = rospy.get_param('/voice_navigation_manager/map_discovery_interval', 10)
        self.navigation_timeout = rospy.get_param('/voice_navigation_manager/navigation_timeout', 60)
        self.goal_tolerance_distance = rospy.get_param('/voice_navigation_manager/goal_tolerance_distance', 0.5)
        self.auto_load_latest_map = rospy.get_param('/voice_navigation_manager/auto_load_latest_map', True)
        self.map_folder_prefix = rospy.get_param('/voice_navigation_manager/map_folder_prefix', 'map_')
        self.waypoints_filename = rospy.get_param('/voice_navigation_manager/waypoints_filename', 'waypoints.xml')
        self.log_level = rospy.get_param('/voice_navigation_manager/log_level', 'INFO')
        
        # 订阅房间提取结果
        rospy.Subscriber('/semantic_extraction/room', String, self.on_room_extracted)
        rospy.Subscriber('/semantic_extraction/status', String, self.on_extraction_status)
        
        # 发布导航目标
        self.nav_goal_pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=10)
        self.status_pub = rospy.Publisher('/voice_navigation/status', String, queue_size=10)
        self.map_list_pub = rospy.Publisher('/voice_navigation/available_maps', String, queue_size=10)
        
        # 状态
        self.current_map = None
        self.available_maps = []
        self.current_waypoints = {}
        self.extraction_status = "idle"
        
        rospy.loginfo("✓ 语音导航管理器初始化完成")
        rospy.loginfo(f"  地图路径: {self.semantic_maps_base}")
        rospy.loginfo(f"  导航超时: {self.navigation_timeout}秒")
        rospy.loginfo(f"  目标容差: {self.goal_tolerance_distance}米")
        rospy.loginfo(f"  自动加载最新地图: {self.auto_load_latest_map}")
        rospy.loginfo(f"  日志级别: {self.log_level}")
        
        # 启动时扫描可用地图
        self._scan_available_maps()
        
        rospy.spin()
    
    def _scan_available_maps(self):
        """扫描并列出所有可用的地图版本"""
        try:
            waypoints_path = Path(self.semantic_maps_base)
            
            if not waypoints_path.exists():
                rospy.logwarn(f"⚠️  航点路径不存在: {self.semantic_maps_base}")
                return
            
            # 查找所有地图文件夹 (格式: map_YYYYMMDD_HHMMSS)
            map_folders = [d for d in waypoints_path.iterdir() 
                          if d.is_dir() and d.name.startswith(self.map_folder_prefix)]
            
            # 按时间戳排序（最新的在前）
            map_folders.sort(key=lambda x: x.name, reverse=True)
            
            self.available_maps = []
            
            for map_folder in map_folders:
                map_info = self._read_map_info(map_folder)
                if map_info:
                    self.available_maps.append(map_info)
            
            rospy.loginfo(f"✓ 扫描到 {len(self.available_maps)} 个地图版本")
            for i, map_info in enumerate(self.available_maps[:3]):  # 显示最新的3个
                rospy.loginfo(f"  {i+1}. {map_info['name']} - {map_info['timestamp']}")
            
            # 发布可用地图列表
            if self.available_maps:
                self._publish_map_list()
                # 自动选择最新的地图
                self._load_map(self.available_maps[0]['path'])
        
        except Exception as e:
            rospy.logerr(f"❌ 扫描地图失败: {e}")
    
    def _read_map_info(self, map_folder):
        """
        读取地图信息
        
        Args:
            map_folder: 地图文件夹路径
            
        Returns:
            map_info: 包含地图信息的字典
        """
        try:
            # 检查必要文件
            waypoints_file = map_folder / 'waypoints.xml'
            yaml_file = map_folder / 'map.yaml'
            pgm_file = map_folder / 'map.pgm'
            
            if not all([waypoints_file.exists(), yaml_file.exists(), pgm_file.exists()]):
                return None
            
            # 解析时间戳
            folder_name = map_folder.name  # map_YYYYMMDD_HHMMSS
            timestamp = folder_name.replace('map_', '')
            
            # 解析航点中的房间信息
            rooms = self._extract_rooms_from_waypoints(waypoints_file)
            
            return {
                'name': folder_name,
                'path': str(map_folder),
                'timestamp': timestamp,
                'waypoints_file': str(waypoints_file),
                'yaml_file': str(yaml_file),
                'pgm_file': str(pgm_file),
                'rooms': rooms
            }
        
        except Exception as e:
            rospy.logwarn(f"⚠️  读取地图信息失败: {map_folder.name} - {e}")
            return None
    
    def _extract_rooms_from_waypoints(self, waypoints_file):
        """
        从XML航点文件中提取房间列表
        
        Args:
            waypoints_file: 航点XML文件路径
            
        Returns:
            rooms: 房间列表，每个房间包含坐标信息
        """
        try:
            tree = ET.parse(waypoints_file)
            root = tree.getroot()
            
            # 读取map.yaml以获得坐标转换参数
            map_dir = waypoints_file.parent
            yaml_file = map_dir / 'map.yaml'
            
            resolution = 0.05  # 默认分辨率
            origin_x = -10.0   # 默认原点
            origin_y = -10.0
            
            if yaml_file.exists():
                try:
                    import yaml
                    with open(yaml_file, 'r') as f:
                        map_config = yaml.safe_load(f)
                    resolution = map_config.get('resolution', 0.05)
                    origin = map_config.get('origin', [-10.0, -10.0, 0.0])
                    origin_x = origin[0]
                    origin_y = origin[1]
                except Exception as e:
                    rospy.logwarn(f"⚠️  无法读取map.yaml: {e}")
            
            rooms = {}
            
            for waypoint in root.findall('Waypoint'):
                name_elem = waypoint.find('Name')
                pos_x_elem = waypoint.find('Pos_x')
                pos_y_elem = waypoint.find('Pos_y')
                
                if name_elem is not None and pos_x_elem is not None and pos_y_elem is not None:
                    room_name = name_elem.text.lower().strip()
                    # 像素坐标转米制坐标: world_coord = origin + pixel_coord * resolution
                    pixel_x = float(pos_x_elem.text)
                    pixel_y = float(pos_y_elem.text)
                    
                    meter_x = origin_x + pixel_x * resolution
                    meter_y = origin_y + pixel_y * resolution
                    
                    rooms[room_name] = {
                        'x': meter_x,
                        'y': meter_y,
                        'z': 0.0
                    }
                    
                    rospy.logdebug(f"房间坐标: {room_name} -> pixel({pixel_x}, {pixel_y}) -> meter({meter_x:.3f}, {meter_y:.3f})")
            
            return rooms
        
        except Exception as e:
            rospy.logwarn(f"⚠️  解析航点文件失败: {e}")
            return {}
    
    def _load_map(self, map_path):
        """
        加载指定的地图版本
        
        Args:
            map_path: 地图文件夹路径
        """
        try:
            for map_info in self.available_maps:
                if map_info['path'] == map_path:
                    self.current_map = map_info
                    self.current_waypoints = map_info['rooms']
                    
                    rospy.loginfo(f"✓ 已加载地图: {map_info['name']}")
                    rospy.loginfo(f"  包含房间: {', '.join(self.current_waypoints.keys())}")
                    
                    # 发布状态
                    status_msg = String()
                    status_msg.data = f"map_loaded:{map_info['name']}"
                    self.status_pub.publish(status_msg)
                    
                    # 发布地图的YAML文件路径供map_server使用
                    # （这部分需要额外的ROS节点来加载地图）
                    
                    break
        
        except Exception as e:
            rospy.logerr(f"❌ 加载地图失败: {e}")
    
    def on_room_extracted(self, msg):
        """
        处理提取的房间信息
        
        Args:
            msg: 包含房间ID的String消息
        """
        try:
            room_id = msg.data.strip()
            rospy.loginfo(f"🏠 收到房间指令: {room_id}")
            
            if not self.current_map:
                rospy.logwarn("⚠️  未加载地图，无法导航")
                status_msg = String()
                status_msg.data = "no_map_loaded"
                self.status_pub.publish(status_msg)
                return
            
            # 在当前地图中查找房间
            # room_id格式: living_room, bedroom等
            # waypoints中的格式: living room, bedroom等（小写中文或英文）
            
            matched_room = None
            matched_coords = None
            
            # 尝试匹配
            for room_name, coords in self.current_waypoints.items():
                # 转换room_id为目标格式（用空格代替下划线）
                room_id_formatted = room_id.replace('_', ' ')
                
                if room_id_formatted in room_name or room_name in room_id_formatted:
                    matched_room = room_name
                    matched_coords = coords
                    break
            
            if matched_coords:
                # 发送导航目标到move_base
                self._send_navigation_goal(matched_room, matched_coords)
                
                status_msg = String()
                status_msg.data = f"navigating_to:{matched_room}"
                self.status_pub.publish(status_msg)
            else:
                rospy.logwarn(f"⚠️  未在地图中找到房间: {room_id}")
                status_msg = String()
                status_msg.data = f"room_not_found:{room_id}"
                self.status_pub.publish(status_msg)
        
        except Exception as e:
            rospy.logerr(f"❌ 房间导航失败: {e}")
    
    def on_extraction_status(self, msg):
        """
        处理语义提取状态
        
        Args:
            msg: 状态消息
        """
        self.extraction_status = msg.data
    
    def _send_navigation_goal(self, room_name, coords):
        """
        发送导航目标到move_base（由simple_navigation_node处理）
        
        Args:
            room_name: 房间名称
            coords: 坐标字典 {'x': float, 'y': float, 'z': float}
        """
        try:
            goal = PoseStamped()
            goal.header.frame_id = "map"
            goal.header.stamp = rospy.Time.now()
            
            # 位置
            goal.pose.position.x = coords['x']
            goal.pose.position.y = coords['y']
            goal.pose.position.z = coords['z']
            
            # 朝向（四元数，默认朝向前方）
            goal.pose.orientation.x = 0.0
            goal.pose.orientation.y = 0.0
            goal.pose.orientation.z = 0.0
            goal.pose.orientation.w = 1.0
            
            # 发布导航目标（由simple_navigation_node订阅并处理）
            self.nav_goal_pub.publish(goal)
            
            rospy.loginfo(f"🎯 发送导航目标: {room_name} ({coords['x']:.2f}, {coords['y']:.2f})")
        
        except Exception as e:
            rospy.logerr(f"❌ 发送导航目标失败: {e}")
    
    def _publish_map_list(self):
        """发布可用地图列表"""
        try:
            map_list = []
            for i, map_info in enumerate(self.available_maps[:5]):  # 最多显示5个
                map_list.append(f"{i+1}. {map_info['name']} - {','.join(map_info['rooms'].keys())}")
            
            msg = String()
            msg.data = '\n'.join(map_list)
            self.map_list_pub.publish(msg)
        
        except Exception as e:
            rospy.logwarn(f"⚠️  发布地图列表失败: {e}")


if __name__ == '__main__':
    try:
        manager = VoiceNavManager()
    except rospy.ROSInterruptException:
        pass

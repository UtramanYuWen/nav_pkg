#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图版本快速切换工具
Quick map version switching tool

用法 / Usage:
  1. 列出所有可用地图
     rosrun nav_pkg switch_map.py --list
  
  2. 切换到指定地图
     rosrun nav_pkg switch_map.py map_20250213_120000
  
  3. 切换到最新地图
     rosrun nav_pkg switch_map.py --latest
  
  4. 查看当前地图
     rosrun nav_pkg switch_map.py --current
"""

import rospy
import sys
import os
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class MapSwitcher:
    def __init__(self):
        """初始化地图切换工具"""
        self.base_path = os.path.expanduser(
            "~/catkin_ws/src/clip_sam_semantic_mapping/results/waypoints"
        )
    
    def list_maps(self):
        """列出所有可用地图"""
        base = Path(self.base_path)
        
        if not base.exists():
            print(f"❌ 路径不存在: {self.base_path}")
            return []
        
        # 查找所有地图文件夹
        maps = sorted(
            [d for d in base.iterdir() if d.is_dir() and d.name.startswith("map_")],
            key=lambda x: x.name,
            reverse=True  # 最新的在前
        )
        
        if not maps:
            print(f"❌ 未找到地图文件夹")
            return []
        
        print(f"\n📊 找到 {len(maps)} 个地图版本:\n")
        print("序号 │ 地图版本              │ 房间数 │ 文件大小 │ 生成时间")
        print("─" * 70)
        
        for i, map_dir in enumerate(maps[:10]):  # 显示最新10个
            try:
                # 获取房间数
                rooms = self._count_rooms(map_dir)
                
                # 获取文件大小
                size = sum(
                    f.stat().st_size 
                    for f in map_dir.rglob('*') 
                    if f.is_file()
                )
                size_str = self._format_size(size)
                
                # 获取生成时间
                timestamp = map_dir.name.replace("map_", "")
                time_str = self._format_timestamp(timestamp)
                
                marker = "⭐ " if i == 0 else "   "
                print(f"{marker}{i+1:2d} │ {map_dir.name:20s} │   {rooms:2d}   │ {size_str:>8s} │ {time_str}")
                
            except Exception as e:
                print(f"   {i+1:2d} │ {map_dir.name:20s} │ ❌ 读取失败")
        
        print()
        return [m.name for m in maps]
    
    def _count_rooms(self, map_dir):
        """计算地图中的房间数"""
        try:
            waypoints_file = map_dir / "waypoints.xml"
            if waypoints_file.exists():
                tree = ET.parse(waypoints_file)
                root = tree.getroot()
                return len(root.findall('Waypoint'))
        except:
            pass
        return 0
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}GB"
    
    def _format_timestamp(self, timestamp):
        """格式化时间戳"""
        try:
            # 格式: YYYYMMDD_HHMMSS
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp
    
    def switch_to_map(self, map_name):
        """切换到指定地图"""
        map_path = Path(self.base_path) / map_name
        
        if not map_path.exists():
            print(f"❌ 地图不存在: {map_name}")
            print(f"   路径: {map_path}")
            print("\n请使用 'rosrun nav_pkg switch_map.py --list' 查看可用地图")
            return False
        
        # 检查必要文件
        required_files = ["waypoints.xml", "map.yaml", "map.pgm"]
        for file in required_files:
            if not (map_path / file).exists():
                print(f"❌ 缺少必要文件: {file}")
                return False
        
        # 尝试通过 ROS 参数更新
        try:
            rospy.init_node('map_switcher', anonymous=True, disable_signals=True)
            rospy.set_param(
                '/voice_navigation_manager/semantic_maps_path',
                str(map_path)
            )
            print(f"✅ ROS 参数已更新")
        except Exception as e:
            print(f"⚠️  ROS 节点离线，无法通过 ROS 参数更新: {e}")
        
        # 推荐手动修改配置文件
        print(f"\n📍 已切换地图到: {map_name}")
        print(f"   完整路径: {map_path}")
        
        # 获取房间信息
        rooms = self._get_rooms_in_map(map_path)
        if rooms:
            print(f"\n🏠 该地图包含的房间:")
            for room in rooms:
                print(f"   • {room}")
        
        print(f"\n➡️  下一步:")
        print(f"   1. 编辑 config/voice_nav_params.yaml")
        print(f"   2. 改为: semantic_maps_path: \"{map_path}\"")
        print(f"   3. 运行: roslaunch nav_pkg voice_nav_simple.launch")
        
        return True
    
    def _get_rooms_in_map(self, map_dir):
        """获取地图中的房间列表"""
        try:
            waypoints_file = map_dir / "waypoints.xml"
            tree = ET.parse(waypoints_file)
            root = tree.getroot()
            rooms = []
            for wp in root.findall('Waypoint'):
                name_elem = wp.find('Name')
                if name_elem is not None:
                    rooms.append(name_elem.text)
            return rooms
        except:
            return []
    
    def get_latest_map(self):
        """获取最新的地图"""
        maps = self.list_maps()
        if maps:
            return maps[0]  # 列表已按时间逆序排列
        return None
    
    def get_current_map(self):
        """获取当前正在使用的地图"""
        try:
            rospy.init_node('map_switcher', anonymous=True, disable_signals=True)
            current_path = rospy.get_param(
                '/voice_navigation_manager/semantic_maps_path',
                'Not set'
            )
            print(f"📍 当前地图路径: {current_path}")
            return current_path
        except Exception as e:
            print(f"❌ 无法获取当前地图: {e}")
            return None


def main():
    switcher = MapSwitcher()
    
    print("\n" + "="*70)
    print("🗺️  地图版本快速切换工具")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  rosrun nav_pkg switch_map.py --list              # 列出所有地图")
        print("  rosrun nav_pkg switch_map.py --latest            # 切换到最新地图")
        print("  rosrun nav_pkg switch_map.py --current           # 查看当前地图")
        print("  rosrun nav_pkg switch_map.py <map_name>         # 切换到指定地图")
        print("\n示例:")
        print("  rosrun nav_pkg switch_map.py --list")
        print("  rosrun nav_pkg switch_map.py map_20250213_120000")
        return
    
    command = sys.argv[1]
    
    if command == "--list":
        switcher.list_maps()
    
    elif command == "--latest":
        latest = switcher.get_latest_map()
        if latest:
            switcher.switch_to_map(latest)
    
    elif command == "--current":
        switcher.get_current_map()
    
    else:
        # 假设是地图名称
        switcher.switch_to_map(command)
    
    print()


if __name__ == '__main__':
    main()

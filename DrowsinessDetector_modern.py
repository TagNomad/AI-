#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, font
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time
import queue
import winsound
from ultralytics import YOLO
from config import DEEPSEEK_API_CONFIG, DROWSINESS_THRESHOLDS, ALERT_CONFIG
import requests
import json
import os

class ModernDrowsinessDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 智能驾驶安全监测系统 v3.0")
        self.root.configure(bg='#0F0F10')
        self.root.resizable(False, False)
        
        # 设置窗口图标（如果有）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
        # 调试模式标志
        self.debug_mode = True  # 开启调试模式
        
        # 初始化变量
        self.running = False
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.current_frame = None
        self.detection_count = 0
        self.fps_counter = 0
        self.last_alert_time = 0
        self.alert_cooldown = DROWSINESS_THRESHOLDS['alert_cooldown']
        
        # 车辆状态
        self.vehicle_speed = 80  # 模拟车速
        
        # 设计主题颜色
        self.colors = {
            'bg': '#0F0F10',
            'card_bg': '#1A1A1C',
            'primary': '#00D4FF',
            'accent': '#FF006E',
            'success': '#00FF9F',
            'warning': '#FFB800',
            'danger': '#FF0054',
            'text': '#FFFFFF',
            'text_secondary': '#A8A8AA',
            'border': '#2D2D30'
        }
        
        # 检测状态变量
        self.reset_statistics()
        
        # 状态标记
        self.left_eye_state = "未检测"
        self.right_eye_state = "未检测"
        self.yawn_state = "未检测"
        self.left_eye_still_closed = False
        self.right_eye_still_closed = False
        self.yawn_in_progress = False
        
        # 加载模型
        self.load_models()
        
        # 创建现代化GUI
        self.create_modern_gui()
        
        # 初始化摄像头（延迟初始化）
        self.root.after(100, self.init_camera)
        
    def reset_statistics(self):
        """重置所有统计数据"""
        self.left_eye_state = "未检测"
        self.right_eye_state = "未检测"
        self.yawn_state = "未检测"
        self.left_eye_still_closed = False
        self.right_eye_still_closed = False
        self.yawn_in_progress = False
        self.blinks = 0
        self.microsleeps = 0.0
        self.yawns = 0
        self.yawn_duration = 0.0
        
        # 新增：眨眼检测相关变量
        self.blink_start_time = None
        self.last_eye_open_time = time.time()
        self.continuous_closed_time = 0.0
        
        self.detection_count = 0
        self.fps_counter = 0
        self.fps_start_time = None
        self.last_alert_time = 0
        self.alert_cooldown = DROWSINESS_THRESHOLDS['alert_cooldown']
        
    def load_models(self):
        """加载YOLO模型"""
        try:
            print("🔄 正在加载AI模型...")
            self.detectyawn = YOLO("runs/detectyawn/train/weights/best.pt")
            self.detecteye = YOLO("runs/detecteye/train/weights/best.pt")
            print("✅ AI模型加载成功！")
            self.model_loaded = True
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.model_loaded = False
            messagebox.showerror("错误", f"模型加载失败: {e}")
            
    def create_modern_gui(self):
        """创建现代化的GUI界面"""
        # 设置自定义字体
        self.title_font = font.Font(family="Arial", size=32, weight="bold")
        self.header_font = font.Font(family="Arial", size=18, weight="bold")
        self.label_font = font.Font(family="Arial", size=12)
        self.value_font = font.Font(family="Arial", size=20, weight="bold")
        
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题栏
        self.create_header(main_container)
        
        # 内容区域
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # 左侧视频区域
        left_panel = tk.Frame(content_frame, bg=self.colors['bg'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_video_section(left_panel)
        
        # 右侧状态区域
        right_panel = tk.Frame(content_frame, bg=self.colors['bg'], width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self.create_status_section(right_panel)
        
        # 底部控制区域
        self.create_control_section(main_container)
        
    def create_header(self, parent):
        """创建顶部标题栏"""
        header_frame = tk.Frame(parent, bg=self.colors['card_bg'], height=100)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # 添加渐变效果边框
        header_frame.configure(relief=tk.FLAT, borderwidth=2, highlightbackground=self.colors['primary'], highlightthickness=1)
        
        # 左侧标题区域
        title_frame = tk.Frame(header_frame, bg=self.colors['card_bg'])
        title_frame.pack(side=tk.LEFT, padx=30, pady=20)
        
        # 主标题
        title_label = tk.Label(
            title_frame,
            text="🚗 智能驾驶安全监测",
            font=self.title_font,
            fg=self.colors['primary'],
            bg=self.colors['card_bg']
        )
        title_label.pack(anchor=tk.W)
        
        # 副标题
        subtitle_label = tk.Label(
            title_frame,
            text="AI-Powered Drowsiness Detection System",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        subtitle_label.pack(anchor=tk.W)
        
        # 右侧信息区域
        info_frame = tk.Frame(header_frame, bg=self.colors['card_bg'])
        info_frame.pack(side=tk.RIGHT, padx=30, pady=20)
        
        # 系统状态
        self.status_label = tk.Label(
            info_frame,
            text="⚡ 系统就绪",
            font=self.label_font,
            fg=self.colors['success'],
            bg=self.colors['card_bg']
        )
        self.status_label.pack(anchor=tk.E)
        
        # 实时时间
        self.time_label = tk.Label(
            info_frame,
            text="",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        self.time_label.pack(anchor=tk.E, pady=(5, 0))
        self.update_time()
        
    def create_video_section(self, parent):
        """创建视频显示区域"""
        # 视频卡片
        video_card = tk.Frame(parent, bg=self.colors['card_bg'], relief=tk.FLAT)
        video_card.pack(fill=tk.BOTH, expand=True)
        video_card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 视频标题栏
        video_header = tk.Frame(video_card, bg=self.colors['card_bg'], height=50)
        video_header.pack(fill=tk.X)
        video_header.pack_propagate(False)
        
        # 标题和状态
        header_content = tk.Frame(video_header, bg=self.colors['card_bg'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(
            header_content,
            text="📹 实时监控",
            font=self.header_font,
            fg=self.colors['text'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        # 检测状态指示器
        self.detection_indicator = tk.Label(
            header_content,
            text="● 待机中",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        self.detection_indicator.pack(side=tk.RIGHT)
        
        # 视频显示区域
        video_container = tk.Frame(video_card, bg='black')
        video_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.video_label = tk.Label(video_container, bg="#000000")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # 底部信息栏
        info_bar = tk.Frame(video_card, bg=self.colors['card_bg'], height=40)
        info_bar.pack(fill=tk.X)
        info_bar.pack_propagate(False)
        
        # FPS显示
        self.fps_label = tk.Label(
            info_bar,
            text="FPS: 0",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        self.fps_label.pack(side=tk.LEFT, padx=20)
        
        # 检测计数
        self.detection_count_label = tk.Label(
            info_bar,
            text="检测次数: 0",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        self.detection_count_label.pack(side=tk.RIGHT, padx=20)
        
    def create_status_section(self, parent):
        """创建状态显示区域"""
        # 滚动容器
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 疲劳等级卡片（特殊样式）
        fatigue_card = self.create_fatigue_card(scrollable_frame)
        
        # 分隔线
        separator = tk.Frame(scrollable_frame, bg=self.colors['border'], height=2)
        separator.pack(fill=tk.X, pady=10)
        
        # 实时数据标题
        tk.Label(
            scrollable_frame,
            text="📊 实时数据监控",
            font=self.header_font,
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack(pady=(10, 5))
        
        # 统计数据卡片
        self.stats_cards = {}
        stats_data = [
            ("👁️ 眨眼次数", "blinks", "0 次", self.colors['primary']),
            ("😴 闭眼时长", "microsleeps", "0.00 秒", self.colors['warning']),
            ("🥱 打哈欠", "yawns", "0 次", self.colors['accent']),
            ("⏱️ 哈欠时长", "yawn_duration", "0.00 秒", self.colors['danger'])
        ]
        
        for icon_title, key, value, color in stats_data:
            card = self.create_data_card(scrollable_frame, icon_title, value, color)
            self.stats_cards[key] = card
            
        # 系统信息
        tk.Label(
            scrollable_frame,
            text="⚙️ 系统信息",
            font=self.header_font,
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack(pady=(20, 5))
        
        # 模型状态
        self.model_status_card = self.create_info_card(
            scrollable_frame, 
            "🤖 AI模型", 
            "已加载" if hasattr(self, 'model_loaded') and self.model_loaded else "未加载"
        )
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_fatigue_card(self, parent):
        """创建疲劳等级卡片"""
        card = tk.Frame(parent, bg=self.colors['card_bg'])
        card.pack(fill=tk.X, pady=5)
        card.configure(highlightbackground=self.colors['primary'], highlightthickness=2)
        
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill=tk.X, padx=20, pady=15)
        
        # 标题
        tk.Label(
            content,
            text="⚠️ 疲劳等级",
            font=self.header_font,
            fg=self.colors['text'],
            bg=self.colors['card_bg']
        ).pack()
        
        # 等级显示
        self.fatigue_label = tk.Label(
            content,
            text="正常",
            font=font.Font(family="Arial", size=36, weight="bold"),
            fg=self.colors['success'],
            bg=self.colors['card_bg']
        )
        self.fatigue_label.pack(pady=10)
        
        # 等级条
        self.create_level_bar(content)
        
        return card
        
    def create_level_bar(self, parent):
        """创建等级指示条"""
        bar_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        bar_frame.pack(fill=tk.X, pady=5)
        
        # 创建三个等级块
        levels = [
            ("正常", self.colors['success']),
            ("警告", self.colors['warning']), 
            ("危险", self.colors['danger'])
        ]
        
        self.level_indicators = []
        for i, (text, color) in enumerate(levels):
            indicator = tk.Frame(bar_frame, bg=color if i == 0 else self.colors['border'], height=5)
            indicator.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
            self.level_indicators.append(indicator)
            
    def create_data_card(self, parent, title, value, color):
        """创建数据卡片"""
        card = tk.Frame(parent, bg=self.colors['card_bg'])
        card.pack(fill=tk.X, pady=5)
        card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill=tk.X, padx=15, pady=10)
        
        # 左侧色块
        color_bar = tk.Frame(content, bg=color, width=4)
        color_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 数据内容
        data_frame = tk.Frame(content, bg=self.colors['card_bg'])
        data_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 标题
        tk.Label(
            data_frame,
            text=title,
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        ).pack(anchor=tk.W)
        
        # 数值
        value_label = tk.Label(
            data_frame,
            text=value,
            font=self.value_font,
            fg=self.colors['text'],
            bg=self.colors['card_bg']
        )
        value_label.pack(anchor=tk.W)
        
        return {'card': card, 'value_label': value_label}
        
    def create_info_card(self, parent, title, value):
        """创建信息卡片"""
        card = tk.Frame(parent, bg=self.colors['card_bg'])
        card.pack(fill=tk.X, pady=5)
        card.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        content = tk.Frame(card, bg=self.colors['card_bg'])
        content.pack(fill=tk.X, padx=15, pady=8)
        
        tk.Label(
            content,
            text=f"{title}: ",
            font=self.label_font,
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        value_label = tk.Label(
            content,
            text=value,
            font=self.label_font,
            fg=self.colors['primary'],
            bg=self.colors['card_bg']
        )
        value_label.pack(side=tk.LEFT)
        
        return {'card': card, 'value_label': value_label}
        
    def create_control_section(self, parent):
        """创建控制按钮区域"""
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # 按钮样式
        button_style = {
            'font': self.header_font,
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 40,
            'pady': 15,
            'bd': 0
        }
        
        # 按钮容器
        button_container = tk.Frame(control_frame, bg=self.colors['bg'])
        button_container.pack()
        
        # 开始按钮
        self.start_button = tk.Button(
            button_container,
            text="▶ 开始检测",
            bg=self.colors['primary'],
            fg=self.colors['bg'],
            activebackground=self.colors['accent'],
            command=self.start_detection,
            **button_style
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_button = tk.Button(
            button_container,
            text="⏸ 停止检测",
            bg=self.colors['danger'],
            fg='white',
            activebackground='#CC0033',
            command=self.stop_detection,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        self.reset_button = tk.Button(
            button_container,
            text="🔄 重置数据",
            bg=self.colors['text_secondary'],
            fg='white',
            activebackground='#636366',
            command=self.reset_data,
            **button_style
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
    def init_camera(self):
        """初始化摄像头"""
        try:
            # 尝试不同的摄像头索引
            for i in range(4):
                print(f"📷 尝试打开摄像头 {i}...")
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    # 设置摄像头参数
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    print(f"✅ 摄像头 {i} 初始化成功")
                    self.status_label.config(text="⚡ 摄像头就绪", fg=self.colors['success'])
                    # 显示默认画面
                    self.show_default_video()
                    return
                self.cap.release()
                
            print("❌ 未找到可用摄像头")
            self.status_label.config(text="❌ 摄像头未连接", fg=self.colors['danger'])
            self.show_no_camera_message()
            
        except Exception as e:
            print(f"❌ 摄像头初始化错误: {e}")
            self.show_no_camera_message()
            
    def show_default_video(self):
        """显示默认视频画面"""
        # 创建一个科技感的默认画面
        default_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 添加网格背景
        for y in range(0, 480, 20):
            cv2.line(default_frame, (0, y), (640, y), (20, 20, 20), 1)
        for x in range(0, 640, 20):
            cv2.line(default_frame, (x, 0), (x, 480), (20, 20, 20), 1)
            
        # 添加文字
        cv2.putText(default_frame, "CAMERA READY", (180, 230), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 212, 255), 2)
        cv2.putText(default_frame, "Press START to begin", (200, 270), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 1)
        self.display_frame(default_frame)
        
    def show_no_camera_message(self):
        """显示无摄像头消息"""
        # 创建一个错误提示画面
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, "NO CAMERA DETECTED", (130, 230), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
        cv2.putText(error_frame, "Please connect a camera", (180, 270), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 1)
        self.display_frame(error_frame)
        
    def start_detection(self):
        """开始检测"""
        if not hasattr(self, 'model_loaded') or not self.model_loaded:
            messagebox.showerror("错误", "AI模型未加载！")
            return
            
        if not self.cap or not self.cap.isOpened():
            # 再次尝试初始化摄像头
            self.init_camera()
            if not self.cap or not self.cap.isOpened():
                messagebox.showerror("错误", "无法打开摄像头！")
                return
                
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🔴 正在检测", fg=self.colors['danger'])
        self.detection_indicator.config(text="● 检测中", fg=self.colors['success'])
        
        # 重置FPS计算
        self.fps_start_time = time.time()
        self.fps_counter = 0
        
        # 启动视频处理线程
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        
        # 启动数据更新
        self.update_display()
        
        print("🚀 检测已启动")
        
    def stop_detection(self):
        """停止检测"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⚡ 系统就绪", fg=self.colors['success'])
        self.detection_indicator.config(text="● 待机中", fg=self.colors['text_secondary'])
        print("⏹️ 检测已停止")
        
    def reset_data(self):
        """重置数据"""
        self.reset_statistics()
        self.detection_count = 0
        self.update_status_display()
        print("🔄 数据已重置")
        
    def video_loop(self):
        """视频处理循环"""
        while self.running:
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # 存储当前帧
                        self.current_frame = frame.copy()
                        
                        # 处理检测
                        self.process_frame(frame)
                        
                        # 在帧上绘制信息
                        self.draw_overlay(frame)
                        
                        # 将帧放入队列
                        if not self.frame_queue.full():
                            self.frame_queue.put(frame)
                            
                        # 更新FPS
                        self.fps_counter += 1
                        
                    else:
                        print("⚠️ 无法读取摄像头画面")
                        time.sleep(0.1)
                        
                time.sleep(0.020)  # 提高处理速度，约50fps
                
            except Exception as e:
                print(f"❌ 视频循环错误: {e}")
                time.sleep(0.1)
                
    def process_frame(self, frame):
        """处理单帧进行检测"""
        try:
            # 记录检测开始时间
            start_time = time.time()
            
            # 眼睛检测 - 降低置信度阈值
            print("👁️ 执行眼睛检测...")
            eye_results = self.detecteye.predict(frame, verbose=False, conf=0.15)
            self.process_eye_detection(eye_results)
            
            # 打哈欠检测 - 降低置信度阈值
            print("🥱 执行打哈欠检测...")
            yawn_results = self.detectyawn.predict(frame, verbose=False, conf=0.15)
            self.process_yawn_detection(yawn_results)
            
            # 更新统计
            self.update_statistics()
            
            # 更新检测计数
            self.detection_count += 1
            
            # 记录检测时间
            detection_time = time.time() - start_time
            print(f"⏱️ 检测耗时: {detection_time:.3f}秒")
            
        except Exception as e:
            print(f"❌ 检测处理错误: {e}")
            import traceback
            traceback.print_exc()
            
    def draw_overlay(self, frame):
        """在帧上绘制覆盖信息"""
        h, w = frame.shape[:2]
        
        # 添加半透明黑色背景条
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 40), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 添加状态文字 - 更详细的显示
        eye_display = self.left_eye_state if self.left_eye_state != "未检测" else "等待检测"
        yawn_display = self.yawn_state if self.yawn_state != "未检测" else "等待检测"
        status_text = f"眼睛: {eye_display} | 嘴部: {yawn_display}"
        cv2.putText(frame, status_text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (w-100, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
    def process_eye_detection(self, results):
        """处理眼睛检测结果"""
        try:
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                if len(boxes) > 0:
                    confidences = boxes.conf.cpu().numpy()
                    class_ids = boxes.cls.cpu().numpy()
                    
                    # 打印所有检测结果（调试模式）
                    if self.debug_mode:
                        for i, (conf, cls) in enumerate(zip(confidences, class_ids)):
                            print(f"  检测框{i}: class={int(cls)}, conf={conf:.3f}")
                    
                    # 获取最高置信度的检测结果
                    max_confidence_index = np.argmax(confidences)
                    class_id = int(class_ids[max_confidence_index])
                    confidence = confidences[max_confidence_index]
                    
                    print(f"👁️ 眼睛检测: class={class_id}, conf={confidence:.2f}")
                    
                    # 进一步降低阈值，使检测更敏感
                    # class=0 是闭眼，class=1 是睁眼
                    if class_id == 0:  # 闭眼
                        if confidence > 0.2:
                            self.left_eye_state = self.right_eye_state = "闭眼"
                            print("👁️ 检测到闭眼状态")
                        elif confidence > 0.1:
                            self.left_eye_state = self.right_eye_state = "疑似闭眼"
                            print("👁️ 检测到疑似闭眼状态")
                        else:
                            # 即使置信度很低，如果检测到class=0，也认为是倾向闭眼
                            self.left_eye_state = self.right_eye_state = "可能闭眼"
                            print("👁️ 检测到可能闭眼状态（低置信度）")
                    else:  # class=1 睁眼
                        if confidence > 0.2:
                            self.left_eye_state = self.right_eye_state = "睁眼"
                        elif confidence > 0.1:
                            self.left_eye_state = self.right_eye_state = "疑似睁眼"
                        else:
                            self.left_eye_state = self.right_eye_state = "可能睁眼"
                else:
                    print("👁️ 未检测到眼睛")
                    self.left_eye_state = self.right_eye_state = "未检测"
            else:
                self.left_eye_state = self.right_eye_state = "未检测"
                
        except Exception as e:
            print(f"❌ 眼睛检测处理错误: {e}")
            import traceback
            traceback.print_exc()
            
    def process_yawn_detection(self, results):
        """处理打哈欠检测结果"""
        try:
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                if len(boxes) > 0:
                    confidences = boxes.conf.cpu().numpy()
                    class_ids = boxes.cls.cpu().numpy()
                    
                    # 获取最高置信度的检测结果
                    max_confidence_index = np.argmax(confidences)
                    class_id = int(class_ids[max_confidence_index])
                    confidence = confidences[max_confidence_index]
                    
                    print(f"🥱 打哈欠检测: class={class_id}, conf={confidence:.2f}")
                    
                    # 降低置信度阈值到0.3
                    if class_id == 0 and confidence > 0.3:  # 打哈欠
                        self.yawn_state = "打哈欠"
                    elif class_id == 1 and confidence > 0.3:  # 不打哈欠
                        self.yawn_state = "正常"
                    else:
                        # 如果置信度较低，根据类别给出倾向性判断
                        if confidence > 0.2:
                            if class_id == 0:
                                self.yawn_state = "疑似打哈欠"
                            else:
                                self.yawn_state = "正常"
                else:
                    print("🥱 未检测到嘴部")
                    self.yawn_state = "未检测"
            else:
                self.yawn_state = "未检测"
                
        except Exception as e:
            print(f"❌ 打哈欠检测处理错误: {e}")
            
    def update_statistics(self):
        """更新统计数据"""
        print(f"📊 更新统计: 眼睛={self.left_eye_state}, 打哈欠={self.yawn_state}")
        
        # 眨眼和闭眼检测 - 增加对多种闭眼状态的处理
        closed_states = ["闭眼", "疑似闭眼", "可能闭眼"]
        if self.left_eye_state in closed_states and self.right_eye_state in closed_states:
            if not self.left_eye_still_closed:
                self.left_eye_still_closed = True
                self.blinks += 1
                print(f"👁️ 眨眼次数: {self.blinks}")
            
            # 根据闭眼状态的确定性，调整累积速度
            if self.left_eye_state == "闭眼":
                self.microsleeps += 0.06  # 确定闭眼，快速累积
            elif self.left_eye_state == "疑似闭眼":
                self.microsleeps += 0.04  # 疑似闭眼，中速累积
            else:  # 可能闭眼
                self.microsleeps += 0.02  # 可能闭眼，慢速累积
                
            print(f"😴 累计闭眼时间: {self.microsleeps:.2f}秒")
        else:
            self.left_eye_still_closed = False
            # 逐渐减少闭眼时间
            if self.microsleeps > 0:
                self.microsleeps = max(0, self.microsleeps - 0.02)
            
        # 打哈欠检测 - 增加对"疑似打哈欠"的处理
        if self.yawn_state in ["打哈欠", "疑似打哈欠"]:
            if not self.yawn_in_progress:
                self.yawn_in_progress = True
                self.yawns += 1
                print(f"🥱 打哈欠次数: {self.yawns}")
            # 增加打哈欠时间累积速度
            self.yawn_duration += 0.05  # 从0.04增加到0.05
            print(f"🥱 打哈欠持续时间: {self.yawn_duration:.2f}秒")
        else:
            self.yawn_in_progress = False
            if self.yawn_duration > 0:
                self.yawn_duration = max(0, self.yawn_duration - 0.02)
            
        # 检查疲劳等级
        self.check_fatigue_level()
        
        # 如果在调试模式，打印更多信息
        if self.debug_mode and (self.blinks > 0 or self.microsleeps > 0):
            print(f"📊 当前统计: 眨眼={self.blinks}次, 闭眼={self.microsleeps:.2f}秒, 打哈欠={self.yawns}次")
        
    def check_fatigue_level(self):
        """检查疲劳等级并发出警告"""
        current_time = time.time()
        
        is_drowsy = (
            self.microsleeps > DROWSINESS_THRESHOLDS['microsleep_threshold'] or
            self.yawn_duration > DROWSINESS_THRESHOLDS['yawn_duration_threshold'] or
            self.yawns > DROWSINESS_THRESHOLDS['yawn_count_threshold']
        )
        
        if is_drowsy and (current_time - self.last_alert_time) > self.alert_cooldown:
            print("⚠️ 检测到疲劳状态！")
            self.show_api_warning()
            self.last_alert_time = current_time
            
    def show_api_warning(self):
        """显示基于API的智能警告"""
        try:
            # 生成状态报告
            status = {
                "vehicle_speed": f"{self.vehicle_speed} km/h",
                "drowsiness_detected": "是",
                "drowsiness_details": f"闭眼{self.microsleeps:.1f}秒，打哈欠{self.yawns}次",
                "yawning_duration": f"{self.yawn_duration:.1f}秒"
            }
            
            # 调用API获取警告
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_CONFIG['api_key']}"
            }
            
            prompt = f"""
            驾驶员疲劳状态报告：
            - 车速: {status['vehicle_speed']}
            - 疲劳检测: {status['drowsiness_detected']}
            - 详情: {status['drowsiness_details']}
            - 打哈欠持续: {status['yawning_duration']}
            
            请生成一个简洁有力的安全提醒(不超过30字)。
            """
            
            response = requests.post(
                DEEPSEEK_API_CONFIG['api_endpoint'],
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 50
                },
                timeout=3
            )
            
            if response.status_code == 200:
                message = response.json()["choices"][0]["message"]["content"]
            else:
                message = "检测到疲劳状态，请立即休息！"
                
        except:
            message = "⚠️ 疲劳驾驶警告！请立即停车休息！"
            
        # 显示弹窗
        self.show_modern_alert(message)
        
        # 播放警告音
        threading.Thread(target=self.play_alert_sound, daemon=True).start()
        
    def show_modern_alert(self, message):
        """显示现代化的警告弹窗"""
        alert = tk.Toplevel(self.root)
        alert.title("⚠️ 安全警告")
        alert.geometry("350x180")  # 缩小窗口尺寸
        alert.configure(bg=self.colors['danger'])
        alert.resizable(False, False)
        
        # 居中显示
        alert.transient(self.root)
        alert.grab_set()
        
        # 使窗口始终在最前
        alert.attributes('-topmost', True)
        
        # 警告内容
        content_frame = tk.Frame(alert, bg=self.colors['danger'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 警告图标
        tk.Label(
            content_frame,
            text="⚠️",
            font=font.Font(size=36),  # 缩小图标
            fg='white',
            bg=self.colors['danger']
        ).pack()
        
        # 警告消息
        tk.Label(
            content_frame,
            text=message,
            font=font.Font(size=14),  # 缩小字体
            fg='white',
            bg=self.colors['danger'],
            wraplength=320
        ).pack(pady=10)
        
        # 确认按钮
        tk.Button(
            content_frame,
            text="确定",
            font=font.Font(size=12, weight="bold"),
            bg='white',
            fg=self.colors['danger'],
            relief=tk.FLAT,
            padx=30,
            pady=5,
            command=alert.destroy
        ).pack()
        
        # 自动关闭
        alert.after(4000, alert.destroy)  # 缩短自动关闭时间
        
    def play_alert_sound(self):
        """播放警告音"""
        try:
            for _ in range(3):
                winsound.Beep(ALERT_CONFIG['sound_frequency'], 200)
                time.sleep(0.1)
        except:
            pass
            
    def update_display(self):
        """更新显示（主线程）"""
        if self.running:
            # 更新视频
            if not self.frame_queue.empty():
                try:
                    frame = self.frame_queue.get_nowait()
                    self.display_frame(frame)
                except queue.Empty:
                    pass
                    
            # 更新状态 - 确保总是更新
            self.update_status_display()
            
            # 更新FPS
            self.update_fps()
            
        # 继续更新 - 即使停止检测也要保持界面更新
        self.root.after(30, self.update_display)  # 从50ms改为30ms，约33fps
        
    def update_fps(self):
        """更新FPS显示"""
        if hasattr(self, 'fps_start_time'):
            elapsed = time.time() - self.fps_start_time
            if elapsed > 1.0:
                fps = self.fps_counter / elapsed
                self.fps_label.config(text=f"FPS: {fps:.1f}")
                self.fps_counter = 0
                self.fps_start_time = time.time()
                
    def update_status_display(self):
        """更新状态显示"""
        # 更新疲劳等级
        if (self.microsleeps > DROWSINESS_THRESHOLDS['microsleep_threshold'] or
            self.yawn_duration > DROWSINESS_THRESHOLDS['yawn_duration_threshold'] or
            self.yawns > DROWSINESS_THRESHOLDS['yawn_count_threshold']):
            self.fatigue_label.config(text="危险", fg=self.colors['danger'])
            # 更新等级条
            for i, indicator in enumerate(self.level_indicators):
                indicator.config(bg=self.colors['danger'] if i <= 2 else self.colors['border'])
        elif self.microsleeps > 1 or self.yawns > 1:
            self.fatigue_label.config(text="警告", fg=self.colors['warning'])
            # 更新等级条
            for i, indicator in enumerate(self.level_indicators):
                indicator.config(bg=[self.colors['success'], self.colors['warning'], self.colors['border']][i])
        else:
            self.fatigue_label.config(text="正常", fg=self.colors['success'])
            # 更新等级条
            for i, indicator in enumerate(self.level_indicators):
                indicator.config(bg=self.colors['success'] if i == 0 else self.colors['border'])
            
        # 更新统计数据
        self.stats_cards['blinks']['value_label'].config(text=f"{self.blinks} 次")
        self.stats_cards['microsleeps']['value_label'].config(text=f"{self.microsleeps:.2f} 秒")
        self.stats_cards['yawns']['value_label'].config(text=f"{self.yawns} 次")
        self.stats_cards['yawn_duration']['value_label'].config(text=f"{self.yawn_duration:.2f} 秒")
        
        # 更新检测计数
        self.detection_count_label.config(text=f"检测次数: {self.detection_count}")
        
    def display_frame(self, frame):
        """显示视频帧"""
        try:
            # 调整大小以适应显示区域
            height, width = frame.shape[:2]
            
            # 计算缩放比例
            label_width = self.video_label.winfo_width()
            label_height = self.video_label.winfo_height()
            
            if label_width > 1 and label_height > 1:
                scale = min(label_width/width, label_height/height) * 0.95
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                frame = cv2.resize(frame, (new_width, new_height))
            
            # 转换颜色空间
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL图像
            pil_image = Image.fromarray(frame_rgb)
            
            # 转换为tkinter格式
            photo = ImageTk.PhotoImage(pil_image)
            
            # 更新显示
            self.video_label.config(image=photo)
            self.video_label.image = photo
            
        except Exception as e:
            print(f"❌ 显示帧错误: {e}")
            
    def update_time(self):
        """更新时间显示"""
        current_time = time.strftime("%Y/%m/%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def on_closing(self):
        """关闭窗口时的处理"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()

def main():
    print("🚀 启动智能驾驶安全监测系统 v3.0...")
    
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ModernDrowsinessDetector(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (1280 // 2)
    y = (root.winfo_screenheight() // 2) - (820 // 2)
    root.geometry(f"1280x820+{x}+{y}")
    
    print("✅ GUI初始化完成，启动主循环...")
    root.mainloop()

if __name__ == "__main__":
    try:
        print("🚀 程序启动中...")
        import sys
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        
        # 检查依赖
        print("\n📦 检查依赖库...")
        try:
            import tkinter
            print("✅ tkinter 已安装")
        except ImportError as e:
            print(f"❌ tkinter 导入失败: {e}")
            
        try:
            import cv2
            print(f"✅ OpenCV 已安装: {cv2.__version__}")
        except ImportError as e:
            print(f"❌ OpenCV 导入失败: {e}")
            
        try:
            from ultralytics import YOLO
            print("✅ ultralytics 已安装")
        except ImportError as e:
            print(f"❌ ultralytics 导入失败: {e}")
            
        try:
            from PIL import Image
            print("✅ PIL 已安装")
        except ImportError as e:
            print(f"❌ PIL 导入失败: {e}")
            
        print("\n🚀 启动主程序...")
        main()
    except Exception as e:
        print(f"\n❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按Enter键退出...")  # 防止窗口立即关闭 
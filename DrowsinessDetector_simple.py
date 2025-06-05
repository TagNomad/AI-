#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import time
import os

# 简化的配置
SIMPLE_CONFIG = {
    'microsleep_threshold': 1.0,
    'yawn_duration_threshold': 1.5,
    'yawn_count_threshold': 2,
    'alert_cooldown': 15
}

class SimpleDrowsinessDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("智能驾驶安全监测系统 v3.0 (简化版)")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # 配色方案
        self.colors = {
            'bg': '#0A0E27',
            'card_bg': '#1A1F3A',
            'primary': '#00D4FF',
            'success': '#00FF88',
            'warning': '#FFB800',
            'danger': '#FF3366',
            'text': '#FFFFFF',
            'text_secondary': '#8892B0',
            'border': '#2A3152'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 初始化变量
        self.running = False
        self.detection_count = 0
        self.blinks = 0
        self.microsleeps = 0.0
        self.yawns = 0
        self.yawn_duration = 0.0
        self.last_alert_time = 0
        
        # 检查依赖
        self.check_dependencies()
        
        # 创建GUI
        self.create_gui()
        
    def check_dependencies(self):
        """检查依赖库"""
        self.dependencies_ok = True
        missing_libs = []
        
        try:
            import cv2
            self.cv2 = cv2
            print("✅ OpenCV 已安装")
        except ImportError:
            missing_libs.append("opencv-python")
            self.cv2 = None
            
        try:
            from ultralytics import YOLO
            self.YOLO = YOLO
            print("✅ ultralytics 已安装")
        except ImportError:
            missing_libs.append("ultralytics")
            self.YOLO = None
            
        try:
            from PIL import Image, ImageTk
            self.Image = Image
            self.ImageTk = ImageTk
            print("✅ PIL 已安装")
        except ImportError:
            missing_libs.append("pillow")
            self.Image = None
            self.ImageTk = None
            
        if missing_libs:
            self.dependencies_ok = False
            self.missing_libs = missing_libs
            
    def create_gui(self):
        """创建GUI界面"""
        # 主容器
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="🚗 智能驾驶安全监测系统",
            font=font.Font(family="Arial", size=24, weight="bold"),
            fg=self.colors['primary'],
            bg=self.colors['bg']
        )
        title_label.pack(pady=(0, 20))
        
        # 状态显示区域
        status_frame = tk.Frame(main_frame, bg=self.colors['card_bg'])
        status_frame.pack(fill=tk.X, pady=10)
        status_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # 依赖检查结果
        if not self.dependencies_ok:
            self.show_dependency_error()
        else:
            self.show_normal_interface(main_frame)
            
    def show_dependency_error(self):
        """显示依赖错误信息"""
        error_frame = tk.Frame(self.root, bg=self.colors['bg'])
        error_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(
            error_frame,
            text="❌ 缺少必要的依赖库",
            font=font.Font(family="Arial", size=18, weight="bold"),
            fg=self.colors['danger'],
            bg=self.colors['bg']
        ).pack(pady=20)
        
        tk.Label(
            error_frame,
            text="请安装以下库：",
            font=font.Font(family="Arial", size=14),
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack()
        
        for lib in self.missing_libs:
            tk.Label(
                error_frame,
                text=f"• {lib}",
                font=font.Font(family="Arial", size=12),
                fg=self.colors['warning'],
                bg=self.colors['bg']
            ).pack()
            
        tk.Label(
            error_frame,
            text="\n安装命令：",
            font=font.Font(family="Arial", size=14),
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack()
        
        install_cmd = f"pip install {' '.join(self.missing_libs)}"
        tk.Label(
            error_frame,
            text=install_cmd,
            font=font.Font(family="Courier", size=12),
            fg=self.colors['primary'],
            bg=self.colors['bg']
        ).pack(pady=10)
        
        tk.Button(
            error_frame,
            text="退出程序",
            font=font.Font(family="Arial", size=12),
            bg=self.colors['danger'],
            fg='white',
            command=self.root.destroy,
            padx=20,
            pady=10
        ).pack(pady=20)
        
    def show_normal_interface(self, parent):
        """显示正常界面"""
        # 检查模型文件
        model_status = self.check_models()
        
        # 状态信息
        info_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        info_frame.pack(fill=tk.X, pady=10)
        info_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(
            info_frame,
            text="📊 系统状态",
            font=font.Font(family="Arial", size=16, weight="bold"),
            fg=self.colors['text'],
            bg=self.colors['card_bg']
        ).pack(pady=10)
        
        # 依赖状态
        deps_text = "✅ 所有依赖库已安装" if self.dependencies_ok else "❌ 缺少依赖库"
        tk.Label(
            info_frame,
            text=deps_text,
            font=font.Font(family="Arial", size=12),
            fg=self.colors['success'] if self.dependencies_ok else self.colors['danger'],
            bg=self.colors['card_bg']
        ).pack()
        
        # 模型状态
        tk.Label(
            info_frame,
            text=model_status,
            font=font.Font(family="Arial", size=12),
            fg=self.colors['success'] if "✅" in model_status else self.colors['warning'],
            bg=self.colors['card_bg']
        ).pack(pady=(5, 10))
        
        # 统计数据
        stats_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        stats_frame.pack(fill=tk.X, pady=10)
        stats_frame.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(
            stats_frame,
            text="📈 检测统计",
            font=font.Font(family="Arial", size=16, weight="bold"),
            fg=self.colors['text'],
            bg=self.colors['card_bg']
        ).pack(pady=10)
        
        # 创建统计标签
        self.stats_labels = {}
        stats_data = [
            ("眨眼次数", "blinks"),
            ("闭眼时长", "microsleeps"),
            ("打哈欠次数", "yawns"),
            ("哈欠时长", "yawn_duration")
        ]
        
        for text, key in stats_data:
            frame = tk.Frame(stats_frame, bg=self.colors['card_bg'])
            frame.pack(fill=tk.X, padx=20, pady=2)
            
            tk.Label(
                frame,
                text=f"{text}:",
                font=font.Font(family="Arial", size=12),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                frame,
                text="0",
                font=font.Font(family="Arial", size=12, weight="bold"),
                fg=self.colors['primary'],
                bg=self.colors['card_bg']
            )
            value_label.pack(side=tk.RIGHT)
            self.stats_labels[key] = value_label
            
        # 控制按钮
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=20)
        
        button_style = {
            'font': font.Font(family="Arial", size=14, weight="bold"),
            'relief': tk.FLAT,
            'padx': 30,
            'pady': 15
        }
        
        if "✅" in model_status:
            self.start_button = tk.Button(
                control_frame,
                text="▶ 开始检测",
                bg=self.colors['primary'],
                fg=self.colors['bg'],
                command=self.start_detection,
                **button_style
            )
            self.start_button.pack(side=tk.LEFT, padx=5)
            
            self.stop_button = tk.Button(
                control_frame,
                text="⏸ 停止检测",
                bg=self.colors['danger'],
                fg='white',
                command=self.stop_detection,
                state=tk.DISABLED,
                **button_style
            )
            self.stop_button.pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(
                control_frame,
                text="⚠️ 请确保模型文件存在后重启程序",
                font=font.Font(family="Arial", size=12),
                fg=self.colors['warning'],
                bg=self.colors['bg']
            ).pack()
            
    def check_models(self):
        """检查模型文件"""
        eye_model = "runs/detecteye/train/weights/best.pt"
        yawn_model = "runs/detectyawn/train/weights/best.pt"
        
        eye_exists = os.path.exists(eye_model)
        yawn_exists = os.path.exists(yawn_model)
        
        if eye_exists and yawn_exists:
            return "✅ 模型文件完整"
        elif eye_exists:
            return "⚠️ 缺少打哈欠检测模型"
        elif yawn_exists:
            return "⚠️ 缺少眼睛检测模型"
        else:
            return "❌ 缺少所有模型文件"
            
    def start_detection(self):
        """开始检测"""
        if not self.dependencies_ok:
            messagebox.showerror("错误", "依赖库未安装完整！")
            return
            
        try:
            # 加载模型
            self.detecteye = self.YOLO("runs/detecteye/train/weights/best.pt")
            self.detectyawn = self.YOLO("runs/detectyawn/train/weights/best.pt")
            
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # 启动检测线程
            self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
            self.detection_thread.start()
            
            messagebox.showinfo("成功", "检测已启动！")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
            
    def stop_detection(self):
        """停止检测"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        messagebox.showinfo("信息", "检测已停止")
        
    def detection_loop(self):
        """检测循环（模拟）"""
        while self.running:
            # 模拟检测过程
            self.detection_count += 1
            
            # 模拟随机检测结果
            import random
            if random.random() < 0.1:  # 10%概率检测到眨眼
                self.blinks += 1
                
            if random.random() < 0.05:  # 5%概率检测到闭眼
                self.microsleeps += 0.1
                
            if random.random() < 0.03:  # 3%概率检测到打哈欠
                self.yawns += 1
                self.yawn_duration += 0.5
                
            # 更新显示
            self.root.after(0, self.update_display)
            
            time.sleep(0.1)  # 100ms间隔
            
    def update_display(self):
        """更新显示"""
        if hasattr(self, 'stats_labels'):
            self.stats_labels['blinks'].config(text=f"{self.blinks} 次")
            self.stats_labels['microsleeps'].config(text=f"{self.microsleeps:.1f} 秒")
            self.stats_labels['yawns'].config(text=f"{self.yawns} 次")
            self.stats_labels['yawn_duration'].config(text=f"{self.yawn_duration:.1f} 秒")
            
        # 检查疲劳状态
        if (self.microsleeps > SIMPLE_CONFIG['microsleep_threshold'] or
            self.yawn_duration > SIMPLE_CONFIG['yawn_duration_threshold'] or
            self.yawns > SIMPLE_CONFIG['yawn_count_threshold']):
            
            current_time = time.time()
            if current_time - self.last_alert_time > SIMPLE_CONFIG['alert_cooldown']:
                self.show_alert()
                self.last_alert_time = current_time
                
    def show_alert(self):
        """显示警告"""
        messagebox.showwarning("疲劳警告", "检测到疲劳状态，请注意休息！")

def main():
    print("🚀 启动智能驾驶安全监测系统 v3.0 (简化版)...")
    
    root = tk.Tk()
    app = SimpleDrowsinessDetector(root)
    
    # 居中显示
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (800 // 2)
    y = (root.winfo_screenheight() // 2) - (600 // 2)
    root.geometry(f"800x600+{x}+{y}")
    
    print("✅ 简化版GUI启动成功")
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按Enter键退出...") 
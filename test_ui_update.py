"""
界面更新测试程序 - 验证数据是否能实时显示在GUI上
"""
import tkinter as tk
from tkinter import ttk, font
import time
import threading

class UIUpdateTest:
    def __init__(self, root):
        self.root = root
        self.root.title("界面更新测试")
        self.root.geometry("400x300")
        
        # 数据变量
        self.blinks = 0
        self.microsleeps = 0.0
        self.running = False
        
        # 创建界面
        self.create_ui()
        
        # 启动界面更新
        self.update_display()
        
    def create_ui(self):
        # 标题
        title = tk.Label(self.root, text="实时数据更新测试", font=font.Font(size=16, weight="bold"))
        title.pack(pady=10)
        
        # 数据显示框架
        data_frame = tk.Frame(self.root)
        data_frame.pack(pady=20)
        
        # 眨眼次数
        tk.Label(data_frame, text="眨眼次数:", font=font.Font(size=12)).grid(row=0, column=0, padx=10)
        self.blinks_label = tk.Label(data_frame, text="0 次", font=font.Font(size=12, weight="bold"))
        self.blinks_label.grid(row=0, column=1, padx=10)
        
        # 闭眼时间
        tk.Label(data_frame, text="闭眼时间:", font=font.Font(size=12)).grid(row=1, column=0, padx=10, pady=10)
        self.microsleeps_label = tk.Label(data_frame, text="0.00 秒", font=font.Font(size=12, weight="bold"))
        self.microsleeps_label.grid(row=1, column=1, padx=10, pady=10)
        
        # 状态显示
        tk.Label(data_frame, text="检测状态:", font=font.Font(size=12)).grid(row=2, column=0, padx=10)
        self.status_label = tk.Label(data_frame, text="待机", font=font.Font(size=12, weight="bold"))
        self.status_label.grid(row=2, column=1, padx=10)
        
        # 控制按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame, text="开始模拟", command=self.start_simulation,
                                     font=font.Font(size=12), padx=20, pady=5)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="停止模拟", command=self.stop_simulation,
                                    font=font.Font(size=12), padx=20, pady=5, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
    def start_simulation(self):
        """开始数据模拟"""
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="运行中", fg="green")
        
        # 启动模拟线程
        self.simulation_thread = threading.Thread(target=self.simulate_data, daemon=True)
        self.simulation_thread.start()
        
    def stop_simulation(self):
        """停止数据模拟"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="已停止", fg="red")
        
    def simulate_data(self):
        """模拟数据变化"""
        while self.running:
            # 模拟眨眼
            if time.time() % 3 < 0.1:  # 每3秒眨眼一次
                self.blinks += 1
                print(f"模拟眨眼: {self.blinks}")
                
            # 模拟闭眼时间累积
            if time.time() % 5 < 2:  # 每5秒中有2秒是闭眼状态
                self.microsleeps += 0.05
                print(f"模拟闭眼: {self.microsleeps:.2f}秒")
            else:
                # 逐渐减少
                if self.microsleeps > 0:
                    self.microsleeps = max(0, self.microsleeps - 0.02)
                    
            time.sleep(0.05)  # 50ms更新一次
            
    def update_display(self):
        """更新界面显示"""
        # 更新标签
        self.blinks_label.config(text=f"{self.blinks} 次")
        self.microsleeps_label.config(text=f"{self.microsleeps:.2f} 秒")
        
        # 根据闭眼时间改变颜色
        if self.microsleeps > 3:
            self.microsleeps_label.config(fg="red")
        elif self.microsleeps > 1:
            self.microsleeps_label.config(fg="orange")
        else:
            self.microsleeps_label.config(fg="green")
            
        # 继续更新
        self.root.after(30, self.update_display)  # 30ms更新一次界面

def main():
    root = tk.Tk()
    app = UIUpdateTest(root)
    root.mainloop()

if __name__ == "__main__":
    print("启动界面更新测试程序...")
    main() 
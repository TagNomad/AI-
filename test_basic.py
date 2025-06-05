#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("=== 基础Python测试 ===")

try:
    import sys
    print(f"✅ Python版本: {sys.version}")
    print(f"✅ Python路径: {sys.executable}")
except Exception as e:
    print(f"❌ 系统信息获取失败: {e}")

try:
    import os
    print(f"✅ 当前目录: {os.getcwd()}")
except Exception as e:
    print(f"❌ 目录信息获取失败: {e}")

try:
    import tkinter as tk
    print("✅ tkinter 可用")
    
    # 创建一个简单的测试窗口
    root = tk.Tk()
    root.title("测试窗口")
    root.geometry("300x200")
    
    label = tk.Label(root, text="如果您看到这个窗口，说明tkinter正常工作！", 
                     font=("Arial", 12), wraplength=250)
    label.pack(expand=True)
    
    button = tk.Button(root, text="关闭", command=root.destroy, 
                      font=("Arial", 10))
    button.pack(pady=10)
    
    print("✅ 测试窗口已创建，请查看是否显示")
    root.mainloop()
    
except ImportError as e:
    print(f"❌ tkinter 导入失败: {e}")
except Exception as e:
    print(f"❌ tkinter 测试失败: {e}")

print("\n测试完成！")
input("按Enter键退出...") 
"""
测试眼睛检测模型的类别定义
"""
import cv2
from ultralytics import YOLO
import time

print("🔍 测试眼睛检测模型...")

# 加载模型
eye_model = YOLO('runs/detecteye/train/weights/best.pt')
print("✅ 模型加载成功")

# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ 无法打开摄像头")
    exit()

print("\n📝 测试说明：")
print("1. 请在摄像头前正常睁眼，观察输出的class值")
print("2. 然后闭上眼睛，观察输出的class值")
print("3. 按 'q' 退出测试\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        # 进行检测
        results = eye_model.predict(frame, verbose=False, conf=0.1)
        
        # 处理结果
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            if len(boxes) > 0:
                # 获取所有检测结果
                for i, (conf, cls) in enumerate(zip(boxes.conf, boxes.cls)):
                    class_id = int(cls.item())
                    confidence = conf.item()
                    print(f"检测 {i+1}: class={class_id}, confidence={confidence:.3f}")
                    
                    # 绘制边框
                    box = boxes.xyxy[i].cpu().numpy()
                    x1, y1, x2, y2 = map(int, box)
                    color = (0, 255, 0) if class_id == 0 else (0, 0, 255)
                    label = f"Class {class_id}: {confidence:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            print("未检测到眼睛")
            
        # 显示画面
        cv2.putText(frame, "Press 'q' to quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Eye Detection Test", frame)
        
        # 按键处理
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        time.sleep(0.5)  # 每0.5秒检测一次
        
except Exception as e:
    print(f"❌ 错误: {e}")
    
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ 测试结束") 
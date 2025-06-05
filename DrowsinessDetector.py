import traceback
import queue
import threading
import time
import winsound
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import sys
import requests
import json
from PySide2.QtWidgets import QApplication, QLabel, QMainWindow, QHBoxLayout, QWidget, QMessageBox
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtCore import Qt, QTimer
from config import DEEPSEEK_API_CONFIG, DROWSINESS_THRESHOLDS, UI_CONFIG, ALERT_CONFIG

class DrowsinessDetector(QMainWindow):
    def __init__(self):
        print("Initializing DrowsinessDetector...")
        super().__init__()
        print("Qt window initialized")

        print("[DEBUG] Setting initial variables...")
        self.yawn_state = ''
        self.left_eye_state =''
        self.right_eye_state= ''
        self.alert_text = ''
        self.vehicle_speed = 100  # 模拟车速，实际应从车辆系统获取
        self.last_alert_time = 0
        self.alert_cooldown = DROWSINESS_THRESHOLDS['alert_cooldown']

        self.blinks = 0
        self.microsleeps = 0
        self.yawns = 0
        self.yawn_duration = 0 

        self.left_eye_still_closed = False  
        self.right_eye_still_closed = False 
        self.yawn_in_progress = False  
        
        print("[DEBUG] Initializing MediaPipe...")
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.points_ids = [187, 411, 152, 68, 174, 399, 298]
        print("[DEBUG] MediaPipe initialized")

        print("[DEBUG] Setting up UI...")
        self.setWindowTitle(UI_CONFIG['window_title'])
        self.setGeometry(100, 100, UI_CONFIG['window_width'], UI_CONFIG['window_height'])
        self.setStyleSheet("background-color: white;")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("border: 2px solid black;")
        self.video_label.setFixedSize(UI_CONFIG['video_width'], UI_CONFIG['video_height'])
        self.layout.addWidget(self.video_label)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("background-color: white; border: 1px solid black; padding: 10px;")
        self.layout.addWidget(self.info_label)

        self.update_info()
        print("[DEBUG] UI setup completed")
        
        print("[DEBUG] Loading YOLO models...")
        print("[DEBUG] Loading yawn detection model...")
        self.detectyawn = YOLO("runs/detectyawn/train/weights/best.pt")
        print("[DEBUG] Yawn model loaded successfully")
        
        print("[DEBUG] Loading eye detection model...")
        self.detecteye = YOLO("runs/detecteye/train/weights/best.pt")
        print("[DEBUG] Eye model loaded successfully")
        
        print("[DEBUG] Initializing camera...")
        # Try different camera indices if 0 doesn't work
        for i in range(3):
            print(f"[DEBUG] Trying camera index {i}...")
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                print(f"Using camera index {i}")
                break
            print(f"[DEBUG] Camera index {i} failed")
        else:
            print("Error: Could not open any camera")
            sys.exit(1)
        time.sleep(1.000)
        print("[DEBUG] Camera initialized successfully")

        print("[DEBUG] Setting up threads...")
        self.frame_queue = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()

        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.process_thread = threading.Thread(target=self.process_frames)

        self.capture_thread.start()
        self.process_thread.start()
        print("[DEBUG] Threads started")
        
        # 添加提示框计时器
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alert_status)
        self.alert_timer.start(1000)  # 每秒检查一次状态
        
        # 添加提示框状态
        self.alert_shown = False
        self.last_alert_box_time = 0
        self.alert_box_cooldown = ALERT_CONFIG['box_cooldown']
        print("[DEBUG] DrowsinessDetector initialization completed")

    def generate_status_report(self):
        status = {
            "vehicle_speed": f"{self.vehicle_speed} km/h",
            "drowsiness_detected": "是" if self.microsleeps > 3 else "否",
            "drowsiness_details": f"闭眼累计{round(self.microsleeps,2)}秒" if self.microsleeps > 0 else "正常",
            "distraction_detected": "否",  # 可以根据实际检测扩展
            "yawning_status": f"已打哈欠{self.yawns}次" if self.yawns > 0 else "正常"
        }
        return status

    def get_deepseek_alert(self, status):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_CONFIG['api_key']}"
        }
        
        prompt = f"""
        驾驶员状态汇报：
        - 车辆速度: {status['vehicle_speed']}（高速公路）
        - 疲劳检测: {status['drowsiness_detected']}（{status['drowsiness_details']}）
        - 分心检测: {status['distraction_detected']}
        - 打哈欠状态: {status['yawning_status']}
        请以简洁礼貌的语气向驾驶员发出安全提醒。
        """
        
        try:
            response = requests.post(
                DEEPSEEK_API_CONFIG['api_endpoint'],
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                timeout=5  # 设置超时时间
            )
            
            if response.status_code == 200:
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    print("API响应格式错误")
                    return "请注意行车安全，建议及时休息。"
            else:
                print(f"API请求失败: {response.status_code}")
                return "请注意行车安全，如感觉疲劳请及时休息。"
        except Exception as e:
            print(f"DeepSeek API调用错误: {e}")
            return "请注意行车安全，如感觉疲劳请及时休息。"

    def update_info(self):
        current_time = time.time()
        status = self.generate_status_report()
        
        # 检查是否需要发出警告
        alert_needed = (
            round(self.yawn_duration, 2) > DROWSINESS_THRESHOLDS['yawn_duration_threshold'] or 
            round(self.microsleeps, 2) > DROWSINESS_THRESHOLDS['microsleep_threshold'] or
            self.yawns > DROWSINESS_THRESHOLDS['yawn_count_threshold']
        )
        
        # 确保警告不会太频繁
        if alert_needed and (current_time - self.last_alert_time) > self.alert_cooldown:
            self.alert_text = self.get_deepseek_alert(status)
            self.last_alert_time = current_time
            self.play_sound_in_thread()

        info_text = (
            f"<div style='font-family: Arial, sans-serif; color: #333;'>"
            f"<h2 style='text-align: center; color: #4CAF50;'>驾驶状态监测</h2>"
            f"<hr style='border: 1px solid #4CAF50;'>"
            f"<p style='color: {'red' if alert_needed else 'green'}; font-weight: bold;'>"
            f"⚠️ {self.alert_text if self.alert_text else '驾驶状态正常'}</p>"
            f"<p><b>🚗 车速:</b> {status['vehicle_speed']}</p>"
            f"<p><b>👁️ 眨眼次数:</b> {self.blinks}</p>"
            f"<p><b>💤 闭眼时长:</b> {round(self.microsleeps,2)} 秒</p>"
            f"<p><b>😮 打哈欠次数:</b> {self.yawns}</p>"
            f"<p><b>⏳ 当前哈欠持续时间:</b> {round(self.yawn_duration,2)} 秒</p>"
            f"<hr style='border: 1px solid #4CAF50;'>"
            f"</div>"
        )
        self.info_label.setText(info_text)

    def predict_eye(self, eye_frame, eye_state):
        results_eye = self.detecteye.predict(eye_frame)
        boxes = results_eye[0].boxes
        if len(boxes) == 0:
            return eye_state

        confidences = boxes.conf.cpu().numpy()  
        class_ids = boxes.cls.cpu().numpy()  
        max_confidence_index = np.argmax(confidences)
        class_id = int(class_ids[max_confidence_index])

        if class_id == 1 :
            eye_state = "Close Eye"
        elif class_id == 0 and confidences[max_confidence_index] > 0.30:
            eye_state = "Open Eye"
                            
        return eye_state

    def predict_yawn(self, yawn_frame):
        results_yawn = self.detectyawn.predict(yawn_frame)
        boxes = results_yawn[0].boxes

        if len(boxes) == 0:
            return self.yawn_state

        confidences = boxes.conf.cpu().numpy()  
        class_ids = boxes.cls.cpu().numpy()  
        max_confidence_index = np.argmax(confidences)
        class_id = int(class_ids[max_confidence_index])

        if class_id == 0:
            self.yawn_state = "Yawn"
        elif class_id == 1 and confidences[max_confidence_index] > 0.50 :
            self.yawn_state = "No Yawn"
                            

    def capture_frames(self):
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if ret:
                if self.frame_queue.qsize() < 2:
                    self.frame_queue.put(frame)
            else:
                break

    def process_frames(self):
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)        
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(image_rgb)

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        ih, iw, _ = frame.shape
                        points = []

                        for point_id in self.points_ids:
                            lm = face_landmarks.landmark[point_id]
                            x, y = int(lm.x * iw), int(lm.y * ih)
                            points.append((x, y))

                        if len(points) != 0:
                            x1, y1 = points[0]  
                            x2, _ = points[1]  
                            _, y3 = points[2]  

                            x4, y4 = points[3]  
                            x5, y5 = points[4]  

                            x6, y6 = points[5]  
                            x7, y7 = points[6]  

                            x6, x7 = min(x6, x7), max(x6, x7)
                            y6, y7 = min(y6, y7), max(y6, y7)

                            mouth_roi = frame[y1:y3, x1:x2]
                            right_eye_roi = frame[y4:y5, x4:x5]
                            left_eye_roi = frame[y6:y7, x6:x7]

                            try:
                                self.left_eye_state = self.predict_eye(left_eye_roi, self.left_eye_state)
                                self.right_eye_state = self.predict_eye(right_eye_roi, self.right_eye_state)
                                self.predict_yawn(mouth_roi)

                            except Exception as e:
                                print(f"Error al realizar la predicción: {e}")

                            if self.left_eye_state == "Close Eye" and self.right_eye_state == "Close Eye":
                                if not self.left_eye_still_closed and not self.right_eye_still_closed:
                                    self.left_eye_still_closed, self.right_eye_still_closed = True , True
                                    self.blinks += 1 
                                self.microsleeps += 45 / 1000
                            else:
                                if self.left_eye_still_closed and self.right_eye_still_closed :
                                    self.left_eye_still_closed, self.right_eye_still_closed = False , False
                                self.microsleeps = 0

                            if self.yawn_state == "Yawn":
                                if not self.yawn_in_progress:
                                    self.yawn_in_progress = True
                                    self.yawns += 1  
                                self.yawn_duration += 45 / 1000
                            else:
                                if self.yawn_in_progress:
                                    self.yawn_in_progress = False
                                    self.yawn_duration = 0

                            self.update_info()
                            self.display_frame(frame)

            except queue.Empty:
                continue

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_event.set()

    def display_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.video_label.setPixmap(QPixmap.fromImage(p))

    def play_alert_sound(self):
        winsound.Beep(
            ALERT_CONFIG['sound_frequency'],
            ALERT_CONFIG['sound_duration']
        )

    def play_sound_in_thread(self):
        sound_thread = threading.Thread(target=self.play_alert_sound)
        sound_thread.start()
        
    def show_alert_on_frame(self, frame, text="Alerta!"):
        font = cv2.FONT_HERSHEY_SIMPLEX
        position = (50, 50)
        font_scale = 1
        font_color = (0, 0, 255) 
        line_type = 2

        cv2.putText(frame, text, position, font, font_scale, font_color, line_type)

    def check_alert_status(self):
        current_time = time.time()
        alert_needed = (
            round(self.yawn_duration, 2) > DROWSINESS_THRESHOLDS['yawn_duration_threshold'] or 
            round(self.microsleeps, 2) > DROWSINESS_THRESHOLDS['microsleep_threshold'] or
            self.yawns > DROWSINESS_THRESHOLDS['yawn_count_threshold']
        )
        
        if alert_needed and not self.alert_shown and (current_time - self.last_alert_box_time) > self.alert_box_cooldown:
            self.show_alert_dialog()
            self.last_alert_box_time = current_time
            self.alert_shown = True
        elif not alert_needed:
            self.alert_shown = False

    def show_alert_dialog(self):
        status = self.generate_status_report()
        alert_message = self.get_deepseek_alert(status)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("疲劳驾驶警告")
        msg.setText(alert_message)
        
        # 设置详细信息
        details = f"""
驾驶状态详情：
- 车速：{status['vehicle_speed']}
- 疲劳状态：{status['drowsiness_details']}
- 打哈欠：{status['yawning_status']}
        """
        msg.setDetailedText(details)
        
        # 设置按钮
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("我知道了")
        
        # 设置样式
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #333;
                font-size: 12pt;
                min-width: 300px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 在新线程中显示对话框
        threading.Thread(target=lambda: msg.exec_()).start()
        self.play_sound_in_thread()

    def closeEvent(self, event):
        self.stop_event.set()
        self.alert_timer.stop()
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    print("[DEBUG] Starting DrowsinessDetector main...")
    try:
        app = QApplication(sys.argv)
        print("[DEBUG] QApplication created")
        window = DrowsinessDetector()
        print("[DEBUG] DrowsinessDetector window created")
        window.show()
        print("[DEBUG] Window shown, entering app.exec_()")
        sys.exit(app.exec_())
    except Exception as e:
        print("启动时发生异常:", e)
        traceback.print_exc()
    finally:
        print("[DEBUG] Main block finished.")

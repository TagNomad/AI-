"""
配置文件
"""
import os
# from dotenv import load_dotenv

# 尝试加载环境变量
# load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_CONFIG = {
    "api_endpoint": "https://api.deepseek.ai/v1/chat/completions",  # 更新为正确的API端点
    "api_key": "sk-41b8d9d2752747dda3239d9d9baaeca6"
}

# 疲劳检测阈值配置
DROWSINESS_THRESHOLDS = {
    "microsleep_threshold": 3.5,  # 闭眼超过3.5秒视为疲劳（从3秒降低）
    "yawn_duration_threshold": 8.0,  # 哈欠持续超过8秒视为疲劳（从7秒降低）
    "yawn_count_threshold": 4,  # 连续打哈欠超过4次视为疲劳（从3次降低）
    "alert_cooldown": 60  # 提醒间隔时间（秒）（从30秒降低）
}

# 界面显示配置
UI_CONFIG = {
    "window_title": "驾驶状态监测系统",
    "window_width": 1200,  # 增加窗口宽度以适应信息显示
    "window_height": 600,
    "video_width": 640,
    "video_height": 480
}

# 提示框配置
ALERT_CONFIG = {
    "box_cooldown": 15,  # 提示框显示间隔（秒）
    "sound_frequency": 1000,  # 警告音频率
    "sound_duration": 500  # 警告音持续时间（毫秒）
} 
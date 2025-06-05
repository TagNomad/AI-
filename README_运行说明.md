# 智能驾驶安全监测系统 v3.0 - 运行说明

## 系统要求

### 硬件要求
- 摄像头（内置或USB摄像头）
- Windows 10/11 操作系统
- 至少4GB内存

### 软件要求
- Python 3.8 或更高版本
- 必需的Python库：
  - opencv-python
  - ultralytics
  - pillow
  - numpy
  - requests

## 快速启动

### 方法1：双击批处理文件（推荐）
1. 找到 `启动疲劳检测系统.bat` 文件
2. 双击运行
3. 如果出现错误，请查看控制台输出的错误信息

### 方法2：命令行运行
```bash
python DrowsinessDetector_modern.py
```

## 常见问题解决

### 1. "未找到Python"错误
**解决方案：**
- 确保已安装Python 3.8+
- 将Python添加到系统PATH环境变量
- 或编辑批处理文件，将`set PYTHON_PATH=python`改为您的Python完整路径

### 2. "ModuleNotFoundError"错误
**解决方案：**
安装缺失的库：
```bash
pip install opencv-python ultralytics pillow numpy requests
```

### 3. "模型文件缺失"错误
**解决方案：**
确保以下文件存在：
- `runs/detecteye/train/weights/best.pt`
- `runs/detectyawn/train/weights/best.pt`

### 4. "摄像头无法打开"错误
**解决方案：**
- 检查摄像头是否正确连接
- 确保没有其他程序占用摄像头
- 在Windows设置中检查摄像头权限

### 5. PowerShell执行策略问题
如果在PowerShell中运行时遇到权限问题：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 程序功能说明

### 检测功能
- **眼睛状态检测**：检测睁眼/闭眼状态
- **打哈欠检测**：检测是否在打哈欠
- **疲劳等级评估**：根据闭眼时长和打哈欠次数评估疲劳程度

### 警告阈值（已优化）
- 闭眼超过1秒
- 打哈欠持续1.5秒
- 2次打哈欠

### 界面说明
- **左侧**：实时视频显示，顶部显示检测状态
- **右侧**：疲劳等级、实时统计数据
- **底部**：控制按钮（开始/停止/重置）

## 性能优化建议

1. **确保良好的光照条件**
2. **摄像头正对面部**
3. **保持适当的距离（50-80cm）**
4. **避免戴墨镜或帽子遮挡**

## 技术支持

如遇到其他问题，请查看：
- `开发日志.md` - 详细的开发历程和技术细节
- 控制台输出的错误信息
- 确保所有依赖都已正确安装

## 注意事项

⚠️ **安全提醒**：
- 本系统仅作为辅助工具
- 不能完全依赖系统进行疲劳判断
- 驾驶时请保持警觉，适时休息

---
最后更新：2025年 
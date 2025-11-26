# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: MARK_gui.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import sys
import math
import numpy as np
from Nova_Voice_Assistant import Assistant
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QProgressBar, QSpacerItem, 
                              QSizePolicy, QMessageBox, QDialog, QInputDialog, 
                              QPushButton, QDialogButtonBox, QGraphicsDropShadowEffect)
from PyQt5.QtCore import (QTimer, Qt, QPointF, QRectF, QSize, QPropertyAnimation, 
                          QEasingCurve, pyqtProperty, QParallelAnimationGroup, 
                          QSequentialAnimationGroup, pyqtSignal)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, 
                         QRadialGradient, QLinearGradient, QConicalGradient, 
                         QPolygonF, QPainterPath, QPixmap, QImage, QIcon)
from Nova_Voice_Assistant import entrypoint
import cv2
from livekit.rtc import VideoBufferType
import socket
import psutil
import time
from datetime import datetime, timedelta
from livekit import rtc
from livekit.agents.utils import images
import asyncio
import logging
import os
import json
import subprocess
import traceback
import threading
import tempfile
from pathlib import Path
import pickle
from dotenv import load_dotenv, set_key, find_dotenv
import firebase_admin
from firebase_admin import credentials, db

# Conditional imports
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    import torch
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print('❌ Please install facenet-pytorch: pip install facenet-pytorch torch torchvision')
    sys.exit(1)
import os
import time
import cv2
import numpy as np
from dotenv import load_dotenv, set_key, find_dotenv
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QDialogButtonBox
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
import firebase_admin
from firebase_admin import credentials
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    import torch
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print('❌ Please install facenet-pytorch: pip install facenet-pytorch torch torchvision')
    sys.exit(1)

# Internal helper functions
def _exception_handler(loop, context):
    """Handle exceptions in the asyncio loop"""
    msg = context.get('exception', context['message'])
    print(f'❌ Error in async task: {msg}')

async def _async_init():
    """Async initialization for the application"""
    try:
        print('🔄 Initializing MARK AI...')
        await asyncio.sleep(0)
    except Exception as e:
        print(f'❌ Initialization error: {e}')
        raise

def start_nova_voice_assistant():
    """
    GUI start hote hi Nova_Voice_Assistant ko alag process me chala deta hai.
    """
    script_path = os.path.join(os.path.dirname(__file__), "Nova_Voice_Assistant.py")

    # yaha "worker" CLI command pass kar rahe hain, jo LiveKit Agents ke CLI me hota hai
    try:
        subprocess.Popen(
            [sys.executable, script_path, "start"],
            stdout=subprocess.DEVNULL,   # agar logs dekhne hain to iss line ko comment kar de
            stderr=subprocess.STDOUT,
        )
        print("🟢 Nova_Voice_Assistant background me start ho gaya.")
    except Exception as e:
        print(f"❌ Nova_Voice_Assistant start error: {e}")

class MARK_AI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.camera = None
        self.camera_available = False
        self.assistant = None

        # timers
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.update_network_info)
        self.network_timer.start(3000)

        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_feed)
        self.camera_timer.start(30)

        # livekit video source state
        self._video_source = None
        self._frame_counter = 0
        self._send_interval = 5
        self._last_frame_sent = 0.0
        self._min_frame_interval = 1.0 / self._send_interval if self._send_interval > 0 else 0.1

        # yahi pe UI build karao – ye time_label, camera_label, network_ip_widget, etc. banayega
        self.init_ui()


    def init_camera(self):
        """Initialize camera with multiple attempts"""  # inserted
        try:
            for i in range(3):
                self.camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        self.camera_available = True
                        print(f'✅ Camera initialized successfully on index {i}')
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.camera.set(cv2.CAP_PROP_FPS, 20)
                        break
                    self.camera.release()
                else:  # inserted
                    if self.camera:
                        self.camera.release()
            if not self.camera_available:
                print('❌ No working camera found on indices 0-2')
        except Exception as e:
            print(f'❌ Camera initialization error: {e}')
            self.camera_available = False

    def set_video_track(self, video_source):
        """Set the video track to send frames to"""  # inserted
        self._video_source = video_source
        print('✅ Video track set in RightPanel')

    def init_ui(self):
        """Initialize the user interface"""  # inserted
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)
        time_label = QLabel('TEMPORAL SYNCHRONIZATION')
        time_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            padding-bottom: 8px;\n            border-bottom: 1px solid #003333;\n            letter-spacing: 1px;\n        ')
        layout.addWidget(time_label)
        self.time_widget = self.create_time_card()
        layout.addWidget(self.time_widget)
        network_label = QLabel('NETWORK INTERFACE')
        network_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            padding-bottom: 8px;\n            border-bottom: 1px solid #003333;\n            letter-spacing: 1px;\n        ')
        layout.addWidget(network_label)
        self.network_ip_widget = self.create_network_card('IP ADDRESS', '192.168.1.100')
        self.network_speed_widget = self.create_network_card('BANDWIDTH', '↑ 12.4 Mbps / ↓ 45.8 Mbps')
        self.network_status_widget = self.create_network_card('CONNECTION', 'WiFi (MARK_5G) - 92%')
        layout.addWidget(self.network_ip_widget)
        layout.addWidget(self.network_speed_widget)
        layout.addWidget(self.network_status_widget)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        camera_label = QLabel('VISUAL INPUT')
        camera_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            padding-bottom: 8px;\n            border-bottom: 1px solid #003333;\n            letter-spacing: 1px;\n        ')
        layout.addWidget(camera_label)
        self.camera_widget = self.create_camera_widget()
        layout.addWidget(self.camera_widget)
        self.setLayout(layout)

    async def send_frame_to_assistant(self, frame):
        """Send video frame to assistant for processing"""  # inserted
        if not hasattr(self, 'assistant') or not self.assistant:
            return None
        try:
            rgba_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
            height, width = rgba_frame.shape[:2]
            video_frame = rtc.VideoFrame(width=width, height=height, type=VideoBufferType.RGBA, data=rgba_frame.tobytes())
            if asyncio.iscoroutinefunction(self.assistant.process_visual_frame):
                await self.assistant.process_visual_frame(video_frame)
            else:  # inserted
                self.assistant.process_visual_frame(video_frame)
        except Exception as e:
            print(f'Frame sending error: {str(e)}')

    def create_time_card(self):
        """Create the time display card"""  # inserted
        card = QWidget()
        card.setStyleSheet('\n            background-color: rgba(0, 20, 40, 120);\n            border-radius: 4px;\n            border: 1px solid rgba(0, 80, 120, 80);\n        ')
        card.setFixedHeight(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        self.time_label = QLabel()
        self.time_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 28px;\n            font-weight: bold;\n            qproperty-alignment: AlignCenter;\n        ')
        self.date_label = QLabel()
        self.date_label.setStyleSheet('\n            color: #00aaaa;\n            font-size: 14px;\n            qproperty-alignment: AlignCenter;\n        ')
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        card.setLayout(layout)
        self.update_time()
        return card

    def create_network_card(self, title, value):
        """Create a network info card"""  # inserted
        card = QWidget()
        card.setStyleSheet('\n            background-color: rgba(0, 20, 40, 120);\n            border-radius: 4px;\n            border: 1px solid rgba(0, 80, 120, 80);\n        ')
        card.setFixedHeight(70)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet('\n            color: #00aaaa;\n            font-size: 11px;\n            font-weight: bold;\n            letter-spacing: 0.5px;\n        ')
        value_label = QLabel(value)
        value_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n        ')
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_camera_widget(self):
        """Create the camera display widget"""  # inserted
        widget = QWidget()
        widget.setStyleSheet('\n            background-color: rgba(0, 20, 40, 120);\n            border-radius: 4px;\n            border: 1px solid rgba(0, 80, 120, 80);\n        ')
        widget.setFixedHeight(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet('\n            background-color: black;\n            qproperty-alignment: AlignCenter;\n        ')
        if not self.camera_available:
            no_camera_label = QLabel('NO CAMERA DETECTED')
            no_camera_label.setStyleSheet('\n                color: #ff5555;\n                font-size: 14px;\n                font-weight: bold;\n                qproperty-alignment: AlignCenter;\n            ')
            self.camera_label.setLayout(QVBoxLayout())
            self.camera_label.layout().addWidget(no_camera_label)
        layout.addWidget(self.camera_label)
        widget.setLayout(layout)
        return widget

    def update_time(self):
        """Update the time display"""  # inserted
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        self.time_label.setText(time_str)
        date_str = now.strftime('%A, %d %B %Y')
        self.date_label.setText(date_str)

    def update_network_info(self):
        """Update network information with mock data"""  # inserted
        ip_address = self.get_local_ip() or '192.168.1.100'
        upload_speed = f'{np.random.uniform(5.0, 15.0):.1f} Mbps'
        download_speed = f'{np.random.uniform(30.0, 60.0):.1f} Mbps'
        signal_strength = f'{np.random.randint(80, 100)}%'
        self.network_ip_widget.layout().itemAt(1).widget().setText(ip_address)
        self.network_speed_widget.layout().itemAt(1).widget().setText(f'↑ {upload_speed} / ↓ {download_speed}')
        self.network_status_widget.layout().itemAt(1).widget().setText(f'WiFi (MARK_5G) - {signal_strength}')

    def get_local_ip(self):
        """Get local IP address"""  # inserted
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def update_camera_feed(self):
        """Update the camera feed display with robust error handling"""
        try:
            if not self.camera_available:
                self.init_camera()
                if not self.camera_available:
                    self.show_no_camera_message()
                    return
            ret, frame = self.camera.read()
            if not ret or frame is None:
                print('⚠️ Failed to read frame from camera')
                self.camera_available = False
                if self.camera:
                    self.camera.release()
                return
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (320, 180))
            self.display_camera_frame(frame_resized)
            self.send_frame_to_livekit(frame)
        except Exception as e:
            print(f'❌ Camera feed update error: {e}')
            self.camera_available = False
            if self.camera:
                self.camera.release()

    def send_frame_to_livekit(self, frame):
        """Send frames to LiveKit with basic rate limiting"""
        if self._video_source is None:
            return

        current_time = time.time()
        # agar pichle frame se bahut kam time hua hai to skip
        if current_time - self._last_frame_sent < self._min_frame_interval:
            return

        self._last_frame_sent = current_time

        try:
            h, w, ch = frame.shape
            # RGB me convert
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frame = images.from_ndarray(rgb_frame, VideoBufferType.RGB)
            self._video_source.capture_frame(video_frame)
            self._frame_counter += 1
        except Exception as e:
            print(f"❌ LiveKit frame send error: {e}")


    def display_camera_frame(self, frame):
        """Display frame in the GUI with border"""  # inserted
        try:
            h, w, ch = frame.shape
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            border_pixmap = QPixmap(pixmap.size())
            border_pixmap.fill(Qt.transparent)
            painter = QPainter(border_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 8, 8)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            border_pen = QPen(QColor(0, 180, 255), 2)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, pixmap.width(), pixmap.height(), 8, 8)
            painter.end()
            self.camera_label.setPixmap(border_pixmap)
        except Exception as e:
            print(f'❌ Display frame error: {e}')

    def show_no_camera_message(self):
        """Show no camera available message"""  # inserted
        no_camera_label = QLabel('NO CAMERA DETECTED\n\nPlease check:\n• Camera connection\n• Camera permissions\n• Other apps using camera')
        no_camera_label.setStyleSheet('\n            color: #ff5555;\n            font-size: 12px;\n            font-weight: bold;\n            qproperty-alignment: AlignCenter;\n            background-color: black;\n        ')
        no_camera_label.setAlignment(Qt.AlignCenter)
        if self.camera_label.layout():
            for i in reversed(range(self.camera_label.layout().count())):
                self.camera_label.layout().itemAt(i).widget().setParent(None)
        else:  # inserted
            self.camera_label.setLayout(QVBoxLayout())
        self.camera_label.layout().addWidget(no_camera_label)

    def paintEvent(self, event):
        """Custom painting for the glassy background effect"""  # inserted
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(0, 20, 40, 200))
        gradient.setColorAt(1, QColor(0, 40, 60, 200))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(0, 80, 120, 150), 1))
        painter.drawRect(self.rect())
        glow_pen = QPen(QColor(0, 180, 255, 80), 1)
        painter.setPen(glow_pen)
        painter.drawLine(0, 0, 0, self.height())

    def closeEvent(self, event):
        """Clean up camera resources"""  # inserted
        if self.camera_available:
            self.camera.release()
        event.accept()  # or super(ClassName, self).closeEvent(event)

class SystemStatsPanel(QWidget):
    """Refined left-side panel with professional futuristic design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet('background-color: transparent;')
        self.cpu_usage = 45
        self.ram_usage = 7.2
        self.ram_total = 16.0
        self.storage_used = 256
        self.storage_total = 512
        self.cpu_temp = 62
        self.power_source = 'AC'
        self.battery_level = 87
        self.weather_city = 'NEURAL CITY'
        self.weather_temp = '24°C'
        self.weather_status = 'CLEAR'
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_mock_data)
        self.update_timer.start(2000)

    def init_ui(self):
        """Initialize the refined user interface"""  # inserted
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)
        sys_info_label = QLabel('SYSTEM STATUS')
        sys_info_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            padding-bottom: 8px;\n            border-bottom: 1px solid #003333;\n            letter-spacing: 1px;\n        ')
        layout.addWidget(sys_info_label)
        self.cpu_widget = self.create_stat_card('CPU UTILIZATION', f'{self.cpu_usage}%', self.cpu_usage, 'circular')
        layout.addWidget(self.cpu_widget)
        self.ram_widget = self.create_stat_card('MEMORY ALLOCATION', f'{self.ram_usage:.1f} / {self.ram_total:.0f} GB', self.ram_usage - self.ram_total + 100, 'linear')
        layout.addWidget(self.ram_widget)
        self.storage_widget = self.create_stat_card('STORAGE CAPACITY', f'{self.storage_used} / {self.storage_total} GB', self.storage_used + self.storage_total + 100, 'linear')
        layout.addWidget(self.storage_widget)
        self.temp_widget = self.create_stat_card('CORE TEMPERATURE', f'{self.cpu_temp}°C', self.cpu_temp, 'temp')
        layout.addWidget(self.temp_widget)
        power_text = f'BATTERY: {self.battery_level}%' if self.power_source == 'Battery' else 'POWER: AC'
        self.power_widget = self.create_stat_card('POWER STATUS', power_text, self.battery_level if self.power_source == 'Battery' else 100, 'linear')
        layout.addWidget(self.power_widget)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        weather_label = QLabel('ENVIRONMENT')
        weather_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            padding-bottom: 8px;\n            border-bottom: 1px solid #003333;\n            letter-spacing: 1px;\n        ')
        layout.addWidget(weather_label)
        self.weather_widget = self.create_weather_card()
        layout.addWidget(self.weather_widget)
        self.setLayout(layout)

    def create_stat_card(self, title, value, percentage, style):
        """Create a refined stat card with the specified style"""  # inserted
        card = QWidget()
        card.setStyleSheet('\n            background-color: rgba(0, 20, 40, 120);\n            border-radius: 4px;\n            border: 1px solid rgba(0, 80, 120, 80);\n        ')
        card.setFixedHeight(90)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setStyleSheet('\n            color: #00aaaa;\n            font-size: 11px;\n            font-weight: bold;\n            letter-spacing: 0.5px;\n        ')
        value_label = QLabel(value)
        value_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 16px;\n            font-weight: bold;\n        ')
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        if style == 'circular':
            progress = CircularProgressBar(percentage)
        else:  # inserted
            if style == 'temp':
                progress = TemperatureBar(percentage)
            else:  # inserted
                progress = LinearProgressBar(percentage)
        layout.addWidget(progress)
        card.setLayout(layout)
        return card

    def create_weather_card(self):
        """Create the refined weather display card"""  # inserted
        card = QWidget()
        card.setStyleSheet('\n            background-color: rgba(0, 20, 40, 120);\n            border-radius: 4px;\n            border: 1px solid rgba(0, 80, 120, 80);\n        ')
        card.setFixedHeight(100)
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        icon_widget = QWidget()
        icon_widget.setFixedSize(40, 40)
        icon_widget.setStyleSheet('background-color: transparent;')
        self.weather_icon = WeatherIcon(self.weather_status)
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(self.weather_icon)
        icon_widget.setLayout(icon_layout)
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        city_label = QLabel(self.weather_city)
        city_label.setStyleSheet('\n            color: #00ffff;\n            font-size: 14px;\n            font-weight: bold;\n            letter-spacing: 0.5px;\n        ')
        temp_label = QLabel(self.weather_temp)
        temp_label.setStyleSheet('\n            color: #ffffff;\n            font-size: 22px;\n            font-weight: bold;\n        ')
        status_label = QLabel(self.weather_status)
        status_label.setStyleSheet('\n            color: #00aaaa;\n            font-size: 12px;\n        ')
        info_layout.addWidget(city_label)
        info_layout.addWidget(temp_label)
        info_layout.addWidget(status_label)
        info_widget.setLayout(info_layout)
        layout.addWidget(icon_widget)
        layout.addWidget(info_widget)
        card.setLayout(layout)
        return card

    def update_mock_data(self):
        """Update with mock data for demonstration"""
        # random thoda upar-niche karke values update karo
        self.cpu_usage = max(5, min(95, self.cpu_usage + np.random.randint(-5, 6)))
        self.ram_usage = max(4.0, min(15.0, self.ram_usage + np.random.uniform(-0.5, 0.5)))
        self.storage_used = max(200, min(400, self.storage_used + np.random.randint(-5, 5)))
        self.cpu_temp = max(40, min(85, self.cpu_temp + np.random.randint(-3, 4)))

        # niche UI refresh part same hi rakho
        self.cpu_widget.layout().itemAt(1).widget().setText(f"{self.cpu_usage}%")
        self.cpu_widget.layout().itemAt(2).widget().setValue(self.cpu_usage)

        self.ram_widget.layout().itemAt(1).widget().setText(f"{self.ram_usage:.1f} / {self.ram_total:.0f} GB")
        self.ram_widget.layout().itemAt(2).widget().setValue(self.ram_usage / self.ram_total * 100)

        self.storage_widget.layout().itemAt(1).widget().setText(
            f"{self.storage_used} / {self.storage_total} GB"
        )
        self.storage_widget.layout().itemAt(2).widget().setValue(
            self.storage_used / self.storage_total * 100
        )

        self.temp_widget.layout().itemAt(1).widget().setText(f"{self.cpu_temp}°C")
        self.temp_widget.layout().itemAt(2).widget().setValue(self.cpu_temp)

        power_text = (
            f"BATTERY: {self.battery_level}%"
            if self.power_source == "Battery"
            else "POWER: AC"
        )
        self.power_widget.layout().itemAt(1).widget().setText(power_text)
        self.power_widget.layout().itemAt(2).widget().setValue(
            self.battery_level if self.power_source == "Battery" else 100
        )

        weather_info = self.weather_widget.layout().itemAt(1).widget()
        weather_info.layout().itemAt(0).widget().setText(self.weather_city)
        weather_info.layout().itemAt(1).widget().setText(self.weather_temp)
        weather_info.layout().itemAt(2).widget().setText(self.weather_status)

    def update_widgets(self):
        """Update all widgets with current data"""
        self.cpu_widget.layout().itemAt(1).widget().setText(f'{self.cpu_usage}%')
        self.cpu_widget.layout().itemAt(2).widget().setValue(self.cpu_usage)
        self.ram_widget.layout().itemAt(1).widget().setText(f'{self.ram_usage:.1f} / {self.ram_total:.0f} GB')
        self.ram_widget.layout().itemAt(2).widget().setValue(int(self.ram_usage / self.ram_total * 100))
        self.storage_widget.layout().itemAt(1).widget().setText(f'{self.storage_used} / {self.storage_total} GB')
        self.storage_widget.layout().itemAt(2).widget().setValue(int(self.storage_used / self.storage_total * 100))
        self.temp_widget.layout().itemAt(1).widget().setText(f'{self.cpu_temp}°C')
        self.temp_widget.layout().itemAt(2).widget().setValue(self.cpu_temp)
        power_text = f'BATTERY: {self.battery_level}%' if self.power_source == 'Battery' else 'POWER: AC'
        self.power_widget.layout().itemAt(1).widget().setText(power_text)
        self.power_widget.layout().itemAt(2).widget().setValue(self.battery_level if self.power_source == 'Battery' else 100)
        weather_info = self.weather_widget.layout().itemAt(1).widget()
        weather_info.layout().itemAt(0).widget().setText(self.weather_city)
        weather_info.layout().itemAt(1).widget().setText(self.weather_temp)
        weather_info.layout().itemAt(2).widget().setText(self.weather_status)

    def paintEvent(self, event):
        """Custom painting for the glassy background effect"""  # inserted
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(0, 20, 40, 200))
        gradient.setColorAt(1, QColor(0, 40, 60, 200))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(0, 80, 120, 150), 1))
        painter.drawRect(self.rect())
        glow_pen = QPen(QColor(0, 180, 255, 80), 1)
        painter.setPen(glow_pen)
        painter.drawLine(0, 0, 0, self.height())

class CircularProgressBar(QWidget):
    """Refined circular progress bar with smooth animation"""

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self.animation_value = value
        self.setFixedSize(100, 30)
        self.setStyleSheet('background-color: transparent;')
        self.animation = QPropertyAnimation(self, b'animationValue')
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value!= self._value:
            self._value = value
            self.animation.stop()
            self.animation.setStartValue(self.animation_value)
            self.animation.setEndValue(value)
            self.animation.start()

    def getAnimationValue(self):
        return self.animation_value

    def setAnimationValue(self, value):
        self.animation_value = value
        self.update()

    @pyqtProperty(float)
    def animationValue(self):
        return self.getAnimationValue()

    @animationValue.setter
    def animationValue(self, value):
        self.setAnimationValue(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(0, 60, 80, 150), 2)
        painter.setPen(pen)
        painter.drawArc(10, 0, 80, 20, 0, 2880)
        progress = int(self.animation_value + 1.8)
        pen = QPen(QColor(0, 255, 255), 2)
        painter.setPen(pen)
        painter.drawArc(10, 0, 80, 20, 2880, -progress + 16)
        angle_rad = math.radians(180 - progress)
        center_x = 50
        center_y = 10
        radius = 40
        end_x = center_x + radius * math.cos(angle_rad)
        end_y = center_y - radius * math.sin(angle_rad)
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.setPen(QPen(QColor(0, 100, 150), 1))
        painter.drawEllipse(QPointF(end_x, end_y), 3, 3)

class LinearProgressBar(QWidget):
    """Refined linear progress bar with smooth animation"""

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self.animation_value = value
        self.setFixedHeight(12)
        self.setStyleSheet('background-color: transparent;')
        self.animation_value = value
        self.animation = QPropertyAnimation(self, b'animationValue')
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value!= self._value:
            self._value = value
            self.animation.stop()
            self.animation.setStartValue(self.animation_value)
            self.animation.setEndValue(value)
            self.animation.start()

    def getAnimationValue(self):
        return self.animation_value

    def setAnimationValue(self, value):
        self.animation_value = value
        self.update()

    @pyqtProperty(float)
    def animationValue(self):
        return self.getAnimationValue()

    @animationValue.setter
    def animationValue(self, value):
        self.setAnimationValue(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_rect = QRectF(0, 4, self.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 60, 80, 150)))
        painter.drawRoundedRect(bg_rect, 2, 2)
        progress = max(0.0, min(100.0, float(self.animation_value)))
        progress_width = self.width() * (progress / 100.0)
        progress_rect = QRectF(0, 4, progress_width, 4)
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(0, 180, 255))
        gradient.setColorAt(1, QColor(0, 255, 255))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)
        glow_rect = QRectF(0, 3, progress_width, 6)
        painter.setPen(QPen(QColor(0, 255, 255, 60), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(glow_rect, 2, 2)

class TemperatureBar(LinearProgressBar):
    """Special progress bar for temperature with color coding"""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_rect = QRectF(0, 4, self.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 60, 80, 150)))
        painter.drawRoundedRect(bg_rect, 2, 2)
        progress = max(0.0, min(100.0, float(self.animation_value)))
        progress_width = self.width() * (progress / 100.0)
        progress_rect = QRectF(0, 4, progress_width, 4)
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0.0, QColor(0, 180, 255))
        gradient.setColorAt(0.3, QColor(0, 255, 180))
        gradient.setColorAt(0.6, QColor(255, 255, 0))
        gradient.setColorAt(1.0, QColor(255, 60, 0))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)
        glow_rect = QRectF(0, 3, progress_width, 6)
        painter.setPen(QPen(QColor(0, 255, 255, 60), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(glow_rect, 2, 2)

class WeatherIcon(QWidget):
    """Minimal vector-style weather icon"""

    def __init__(self, weather_type='CLEAR', parent=None):
        super().__init__(parent)
        self.weather_type = weather_type
        self.setFixedSize(40, 40)
        self.setStyleSheet('background-color: transparent;')

    def set_weather_type(self, weather_type):
        self.weather_type = weather_type
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 255, 255), 1))
        center = QPointF(20, 20)
        if self.weather_type == 'CLEAR':
            painter.setBrush(QBrush(QColor(255, 255, 0, 150)))
            painter.drawEllipse(center, 8, 8)
            for i in range(0, 360, 30):
                angle = math.radians(i)
                start_x = center.x() - 10 * math.cos(angle)
                start_y = center.y() - 10 * math.sin(angle)
                end_x = center.x() - 15 * math.cos(angle)
                end_y = center.y() - 15 * math.sin(angle)
                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

        else:  # inserted
            if self.weather_type == 'CLOUDY':
                path = QPainterPath()
                path.moveTo(10, 20)
                path.cubicTo(5, 15, 15, 10, 20, 12)
                path.cubicTo(25, 5, 35, 8, 30, 15)
                path.cubicTo(38, 15, 35, 20, 30, 22)
                path.cubicTo(30, 25, 15, 25, 10, 20)
                painter.setBrush(QBrush(QColor(200, 200, 255, 150)))
                painter.drawPath(path)
            else:  # inserted
                if self.weather_type == 'RAIN':
                    path = QPainterPath()
                    path.moveTo(10, 20)
                    path.cubicTo(5, 15, 15, 10, 20, 12)
                    path.cubicTo(25, 5, 35, 8, 30, 15)
                    path.cubicTo(38, 15, 35, 20, 30, 22)
                    path.cubicTo(30, 25, 15, 25, 10, 20)
                    painter.setBrush(QBrush(QColor(150, 150, 255, 150)))
                    painter.drawPath(path)
                    painter.setPen(QPen(QColor(0, 150, 255), 1))
                    for i in range(3):
                        painter.drawLine(15, i + 8, 30, 22, 13 + i + 8, 30)
                        painter.drawLine(17, i + 8, 30, 22, 15 + i + 8, 30)
                else:  # inserted
                    if self.weather_type == 'THUNDER':
                        path = QPainterPath()
                        path.moveTo(10, 20)
                        path.cubicTo(5, 15, 15, 10, 20, 12)
                        path.cubicTo(25, 5, 35, 8, 30, 15)
                        path.cubicTo(38, 15, 35, 20, 30, 22)
                        path.cubicTo(30, 25, 15, 25, 10, 20)
                        painter.setBrush(QBrush(QColor(100, 100, 255, 150)))
                        painter.drawPath(path)
                        bolt = QPolygonF()
                        bolt.append(QPointF(20, 15))
                        bolt.append(QPointF(25, 20))
                        bolt.append(QPointF(22, 20))
                        bolt.append(QPointF(28, 28))
                        bolt.append(QPointF(23, 25))
                        bolt.append(QPointF(20, 30))
                        painter.setBrush(QBrush(QColor(255, 255, 0)))
                        painter.setPen(Qt.NoPen)
                        painter.drawPolygon(bolt)

class MARKInterfaceWidget(QWidget):
    """This should be the version that includes BOTH the left panel AND the animation"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(1500, 800)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.left_panel = SystemStatsPanel()
        main_layout.addWidget(self.left_panel)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet('background-color: transparent;')
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet('background-color: transparent;')
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        self.init_MARK_interface()
        central_layout.addWidget(self.MARK_widget)
        self.central_widget.setLayout(central_layout)
        main_layout.addWidget(self.central_widget)
        self.right_panel = MARK_AI()
        main_layout.addWidget(self.right_panel)
        self.setLayout(main_layout)
        self.setLayout(main_layout)
        self.setMinimumSize(1000, 800)
        self.setStyleSheet('background-color: #000000;')
        self.setMouseTracking(True)
        self.mouse_pos = QPointF(0, 0)
        self.mouse_influence = 0.0
        self.time = 0.0
        self.dt = 0.016
        self.ring_rotations = [5.0, (-12.0), 9.0, (-7.0), 15.0, (-10.0), 6.0, (-8.0), 11.0]
        self.pulse_phase = 0.0
        self.pulse_speed = 4.2
        self.breathing_phase = 0.0
        self.particles = []
        self.init_particles()
        self.data_blips = []
        self.blip_timer = 0.0
        self.spark_trails = []
        self.spark_timer = 0.0
        self.special_effect_timer = 0.0
        self.special_effect_active = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        self.click_animation_group = QParallelAnimationGroup()
        self.setup_click_animation()
        self._vibration_offset = QPointF(0, 0)
        self._pulse_scale = 1.0

    def getVibrationOffset(self):
        return self._vibration_offset

    def setVibrationOffset(self, offset):
        self._vibration_offset = offset
        self.update()
    vibration_offset = property(getVibrationOffset, setVibrationOffset)

    def getPulseScale(self):
        return self._pulse_scale

    def setPulseScale(self, scale):
        self._pulse_scale = scale
        self.update()
    pulse_scale = property(getPulseScale, setPulseScale)

    def init_MARK_interface(self):
        """Initialize the original MARK interface"""  # inserted
        self.MARK_widget = QWidget()
        self.MARK_widget.setMinimumSize(750, 800)
        self.MARK_widget.setStyleSheet('background-color: transparent;')

    def init_particles(self):
        """Initialize background particle system"""  # inserted
        np.random.seed(42)
        for i in range(80):
            particle = {'x': np.random.randint(0, 1000), 'y': np.random.randint(0, 800), 'vx': np.random.uniform((-0.3), 0.3), 'vy': np.random.uniform((-0.3), 0.3), 'size': np.random.uniform(0.5, 2.0), 'alpha': np.random.uniform(20, 80), 'phase': np.random.uniform(0, 2 * math.pi), 'pulse_speed': np.random.uniform(0.5, 2.0)}
            self.particles.append(particle)

    def setup_click_animation(self):
        """Setup all animations for the new click effect"""  # inserted
        self._vibration_offset = QPointF(0, 0)
        self._pulse_scale = 1.0
        self.vibration_anim = QPropertyAnimation(self, b'vibration_offset')
        self.vibration_anim.setDuration(500)
        self.vibration_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.vibration_anim.setKeyValueAt(0, QPointF(0, 0))
        for i in range(1, 10):
            x_offset = np.random.uniform((-8), 8)
            y_offset = np.random.uniform((-8), 8)
            self.vibration_anim.setKeyValueAt(i / 10.0, QPointF(x_offset, y_offset))
        self.vibration_anim.setKeyValueAt(1, QPointF(0, 0))
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(20)
        self.glow_effect.setColor(QColor(0, 255, 255))
        self.glow_effect.setOffset(0, 0)
        self.glow_anim = QPropertyAnimation(self.glow_effect, b'blurRadius')
        self.glow_anim.setDuration(600)
        self.glow_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.glow_anim.setStartValue(20)
        self.glow_anim.setKeyValueAt(0.2, 45)
        self.glow_anim.setKeyValueAt(0.5, 30)
        self.glow_anim.setEndValue(20)
        self.glow_color_anim = QPropertyAnimation(self.glow_effect, b'color')
        self.glow_color_anim.setDuration(600)
        self.glow_color_anim.setStartValue(QColor(0, 255, 255))
        self.glow_color_anim.setKeyValueAt(0.3, QColor(102, 250, 255))
        self.glow_color_anim.setEndValue(QColor(0, 255, 255))
        self.pulse_anim = QPropertyAnimation(self, b'pulse_scale')
        self.pulse_anim.setDuration(700)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setKeyValueAt(0.3, 1.15)
        self.pulse_anim.setKeyValueAt(0.6, 0.95)
        self.pulse_anim.setEndValue(1.0)
        self.energy_rings = []
        self.ring_anim_group = QSequentialAnimationGroup()
        self.click_animation_group.addAnimation(self.vibration_anim)
        self.click_animation_group.addAnimation(self.glow_anim)
        self.click_animation_group.addAnimation(self.glow_color_anim)
        self.click_animation_group.addAnimation(self.pulse_anim)

    def getVibrationOffset(self):
        return self._vibration_offset

    def setVibrationOffset(self, offset):
        self._vibration_offset = offset
        self.update()

    @pyqtProperty(QPointF)
    def vibration_offset(self):
        return self._vibration_offset

    @vibration_offset.setter
    def vibration_offset(self, offset):
        self._vibration_offset = offset
        self.update()

    def getPulseScale(self):
        return self._pulse_scale

    def setPulseScale(self, scale):
        self._pulse_scale = scale
        self.update()

    @pyqtProperty(float)
    def pulse_scale(self):
        return self._pulse_scale

    @pulse_scale.setter
    def pulse_scale(self, scale):
        self._pulse_scale = scale
        self.update()

    def create_energy_ring(self):
        """Create an expanding energy ring effect"""  # inserted
        ring = {'radius': 10, 'alpha': 180, 'max_radius': 150, 'life': 0.0, 'max_life': 0.7}
        self.energy_rings.append(ring)
        if not hasattr(self, 'ring_animation_timer'):
            self.ring_animation_timer = QTimer()
            self.ring_animation_timer.timeout.connect(self.update_energy_rings)
            self.ring_animation_timer.start(16)

    def update_energy_rings(self):
        """Update all active energy rings"""  # inserted
        center = QPointF(self.width() / 2, self.height() / 2)
        distance = math.sqrt(
            (self.mouse_pos.x() - center.x()) ** 2 + (self.mouse_pos.y() - center.y()) ** 2
        )
        for ring in self.energy_rings[:]:
            ring['life'] = 0.016
            progress = ring['life'] / ring['max_life']
            if progress >= 1.0:
                self.energy_rings.remove(ring)
            else:  # inserted
                start_radius = 10
                end_radius = ring['max_radius'] + 10
                ring['radius'] = start_radius + (end_radius - start_radius) * float(progress)

                ring['alpha'] = 180 * (1 - progress)
        if not self.energy_rings and hasattr(self, 'ring_animation_timer'):
            self.ring_animation_timer.stop()
            del self.ring_animation_timer
        self.update()

    def update_animation(self):
        """Update all animation states"""
        self.time += self.dt
        for i in range(len(self.ring_rotations)):
            rotation_speed = ((i % 2) + 1) * 2.0 * self.dt
            if (i % 2) == 0:
                self.ring_rotations[i] += rotation_speed
            else:
                self.ring_rotations[i] -= rotation_speed
            if self.ring_rotations[i] > 360:
                self.ring_rotations[i] -= 360
            elif self.ring_rotations[i] < -360:
                self.ring_rotations[i] += 360
        self.pulse_phase += self.pulse_speed * self.dt
        self.breathing_phase += 0.8 * self.dt
        self.update_particles()
        self.update_data_blips()
        self.update_spark_trails()
        if self.special_effect_active:
            self.special_effect_timer = self.dt
            if self.special_effect_timer > 2.0:
                self.special_effect_active = False
                self.special_effect_timer = 0.0
        self.mouse_influence = 0.95
        self.update()

    def update_particles(self):
        """Update particle system"""  # inserted
        for particle in self.particles:
            particle['x'] = particle['vx']
            particle['y'] = particle['vy']
            if particle['x'] < 0:
                particle['x'] = self.width()
            else:  # inserted
                if particle['x'] > self.width():
                    particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = self.height()
            else:  # inserted
                if particle['y'] > self.height():
                    particle['y'] = 0
            particle['phase'] = particle['pulse_speed'] + self.dt
            base_alpha = 30 * 5 * 5 * 0
            particle['alpha'] = base_alpha

    def update_data_blips(self):
        """Update data blips around rings"""  # inserted
        self.blip_timer = self.dt
        if self.blip_timer > 0.8:
            self.blip_timer = 0.0
            blip = {'angle': np.random.uniform(0, 360), 'radius': np.random.choice([120, 160, 200, 240, 280, 320, 360, 400]), 'life': 0.0, 'max_life': 2.0, 'speed': np.random.uniform(15, 30)}
            self.data_blips.append(blip)
        for blip in self.data_blips[:]:
            blip['life'] = self.dt
            blip['angle'] = blip['speed'] + self.dt
            if blip['life'] > blip['max_life']:
                self.data_blips.remove(blip)

    def update_spark_trails(self):
        """Update spark trail effects"""  # inserted
        self.spark_timer = self.dt
        if self.spark_timer > 3.0 and np.random.random() < 0.3:
            self.spark_timer = 0.0
            spark = {'start_angle': np.random.uniform(0, 360), 'radius': np.random.choice([180, 220, 260, 300, 340, 380]), 'life': 0.0, 'max_life': 1.5, 'speed': np.random.uniform(60, 120)}
            self.spark_trails.append(spark)
        for spark in self.spark_trails[:]:
            spark['life'] = self.dt
            spark['start_angle'] = spark['speed'] + self.dt
            if spark['life'] > spark['max_life']:
                self.spark_trails.remove(spark)

    def mouseMoveEvent(self, event):
        """Handle mouse movement for interactive effects"""
        self.mouse_pos = QPointF(event.x(), event.y())
        center = QPointF(self.width() / 2, self.height() / 2)
        dx = self.mouse_pos.x() - center.x()
        dy = self.mouse_pos.y() - center.y()
        distance = math.hypot(dx, dy)
        max_distance = 400.0
        if distance < max_distance:
            self.mouse_influence = max(0.0, 1.0 - (distance / max_distance))
        else:
            self.mouse_influence = 0.0

    def mousePressEvent(self, event):
        """Handle mouse clicks for special effects"""  # inserted
        if event.button() == Qt.LeftButton:
            self.trigger_special_effect()

    def trigger_special_effect(self):
        """Trigger the new cinematic click effect"""  # inserted
        self.click_animation_group.stop()
        self.click_animation_group.start()
        self.create_energy_ring()

    def paintEvent(self, event):
        """Main painting method with enhanced effects"""  # inserted
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        center_x = self.width() / 2
        center_y = self.height() / 2
        center = QPointF(center_x, center_y)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        self.draw_enhanced_background(painter)
        self.draw_particle_system(painter)
        self.draw_enhanced_grid(painter)
        self.draw_data_blips(painter, center)
        self.draw_neural_rings(painter, center)
        self.draw_spark_trails(painter, center)
        self.draw_enhanced_center_core(painter, center)
        if self.special_effect_active:
            self.draw_special_effects(painter, center)

    def draw_enhanced_background(self, painter: QPainter):
        """Draw enhanced background with subtle gradients"""
        center = QPointF(self.width() / 2, self.height() / 2)
        max_radius = max(self.width(), self.height())
        gradient = QRadialGradient(center, max_radius)
        gradient.setColorAt(0, QColor(0, 8, 15, 255))
        gradient.setColorAt(0.7, QColor(0, 4, 8, 255))
        gradient.setColorAt(1, QColor(0, 0, 0, 255))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    def draw_particle_system(self, painter: QPainter):
        """Draw animated background particles"""
        painter.setPen(Qt.NoPen)
        for particle in self.particles:
            alpha = int(particle['alpha'] * (1.0 + 0.3 * self.mouse_influence))
            size = particle['size'] * (1.0 + 0.5 * self.mouse_influence)
            for i in range(3):
                layer_size = size * (1.0 - i * 0.3)
                layer_alpha = int(alpha / (2 ** i))
                glow_color = QColor(0, 255, 255, layer_alpha)
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(QPointF(particle['x'], particle['y']), layer_size, layer_size)

    def draw_enhanced_grid(self, painter: QPainter):
        """Draw enhanced moving grid background"""
        grid_offset = (self.time * 60) % 60
        grid_color = QColor(0, 60, 80, int(20 + 10 * self.mouse_influence))
        painter.setPen(QPen(grid_color, 1))
        grid_size = 60
        for x in range(int(-grid_offset), self.width() + grid_size, grid_size):
            alpha = 20 + int(15 * (0.5 + 0.5 * math.sin(x * 0.01 + self.time)))
            painter.setPen(QPen(QColor(0, 60, 80, int(alpha))))
            painter.drawLine(x, 0, x, self.height())
        for y in range(int(-grid_offset), self.height() + grid_size, grid_size):
            alpha = 20 + int(15 * (0.5 + 0.5 * math.sin(y * 0.01 + self.time)))
            painter.setPen(QPen(QColor(0, 60, 80, int(alpha))))
            painter.drawLine(0, y, self.width(), y)

    def draw_data_blips(self, painter: QPainter, center: QPointF):
        """Draw animated data blips around rings"""
        painter.setPen(Qt.NoPen)
        for blip in self.data_blips:
            angle_rad = math.radians(blip['angle'])
            x = center.x() + blip['radius'] * math.cos(angle_rad)
            y = center.y() + blip['radius'] * math.sin(angle_rad)
            life_progress = blip['life'] / blip['max_life']
            alpha = int(255 * (1 - life_progress) * 0.8)
            size = 2.5
            for i in range(3):
                layer_size = size * (1.0 - i * 0.3)
                layer_alpha = int(alpha / (2 ** i))
                color = QColor(0, 255, 255, layer_alpha)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), layer_size, layer_size)

    def draw_neural_rings(self, painter: QPainter, center: QPointF):
        """Draw neural processing rings with enhanced glow"""
        breathing = 0.5 + 0.5 * math.sin(self.breathing_phase)
        rings = [
            {'radius': 400, 'width': breathing * 4 + 1, 'alpha': 8, 'segments': 0, 'rotation': 0, 'glow_layers': 2},
            {'radius': 360, 'width': 2, 'alpha': 12, 'segments': 12, 'rotation': self.ring_rotations[1], 'glow_layers': 2},
            {'radius': 320, 'width': breathing * 3 + 1.5, 'alpha': 10, 'segments': 0, 'rotation': 0, 'glow_layers': 2},
            {'radius': 280, 'width': 1.5, 'alpha': 14, 'segments': 16, 'rotation': self.ring_rotations[3], 'glow_layers': 2},
            {'radius': 240, 'width': breathing * 2 + 1, 'alpha': 12, 'segments': 0, 'rotation': 0, 'glow_layers': 2},
            {'radius': 200, 'width': 1.5, 'alpha': 16, 'segments': 20, 'rotation': self.ring_rotations[5], 'glow_layers': 2},
            {'radius': 160, 'width': 1, 'alpha': 18, 'segments': 24, 'rotation': self.ring_rotations[6], 'glow_layers': 2},
            {'radius': 120, 'width': 1, 'alpha': 20, 'segments': 28, 'rotation': self.ring_rotations[7], 'glow_layers': 2},
            {'radius': 80, 'width': 0.8, 'alpha': 25, 'segments': 32, 'rotation': self.ring_rotations[8], 'glow_layers': 2}
        ]
        for ring in rings:
            self.draw_neural_ring(painter, center, ring)

    def draw_neural_ring(self, painter: QPainter, center: QPointF, ring_config: dict):
        """Draw a single neural ring with enhanced glow"""
        radius = ring_config['radius']
        width = ring_config['width']
        alpha = ring_config['alpha']
        segments = ring_config['segments']
        rotation = ring_config['rotation']
        glow_layers = ring_config['glow_layers']
        enhanced_alpha = int(alpha * (1.0 + 0.4 * self.mouse_influence))
        
        for i in range(glow_layers):
            glow_radius = radius - i * 10
            glow_alpha = int(enhanced_alpha / (2 ** i))
            glow_width = width - i * 0.5
            
            if segments == 0:
                painter.setPen(QPen(QColor(0, 255, 255, glow_alpha), glow_width))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(center, glow_radius, glow_radius)
            else:
                painter.save()
                painter.translate(center)
                painter.rotate(rotation)
                segment_angle = 360 / segments
                arc_length = segment_angle * 0.7
                painter.setBrush(Qt.NoBrush)
                
                for j in range(segments):
                    start_angle = j * segment_angle
                    segment_alpha = glow_alpha
                    if (j % 3) == 0:
                        segment_alpha = int(glow_alpha * 1.3)
                    painter.setPen(QPen(QColor(0, 255, 255, segment_alpha), glow_width))
                    painter.drawArc(QRectF(-glow_radius, -glow_radius, glow_radius * 2, glow_radius * 2), 
                                    int(start_angle * 16), int(arc_length * 16))
                painter.restore()
        
        if segments == 0:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 255, 255, enhanced_alpha), width))
            painter.drawEllipse(center, radius, radius)
        else:
            painter.save()
            painter.translate(center)
            painter.rotate(rotation)
            segment_angle = 360 / segments
            arc_length = segment_angle * 0.7
            painter.setBrush(Qt.NoBrush)
            
            for j in range(segments):
                start_angle = j * segment_angle
                segment_alpha = enhanced_alpha
                if (j % 3) == 0:
                    segment_alpha = int(enhanced_alpha * 1.3)
                painter.setPen(QPen(QColor(0, 255, 255, segment_alpha), width))
                painter.drawArc(QRectF(-radius, -radius, radius * 2, radius * 2), 
                                int(start_angle * 16), int(arc_length * 16))
            painter.restore()

    def draw_spark_trails(self, painter: QPainter, center: QPointF):
        """Draw spark trail effects"""  # inserted
        painter.setPen(Qt.NoPen)
        for spark in self.spark_trails:
            life_progress = spark['life'] / spark['max_life']
            alpha = int(255 * (1 - life_progress) ** 0.6)
            angle_rad = math.radians(spark['start_angle'])
            x = center.x() + spark['radius'] * math.cos(angle_rad)
            y = center.y() + spark['radius'] * math.sin(angle_rad)
            for i in range(3):
                layer_size = 3 - i
                layer_alpha = alpha // (2 * i + 1)
                color = QColor(255, 255, 255, layer_alpha)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), layer_size, layer_size)

    def draw_enhanced_center_core(self, painter: QPainter, center: QPointF):
        """Draw enhanced pulsating center core with new effects"""  # inserted
        painter.save()
        painter.translate(self.vibration_offset)
        pulse = 0.6 + 0.5 * math.sin(self.time * 2)
        breathing = 0.5 + 0.5 * math.sin(self.breathing_phase)
        current_radius = 50 * self.pulse_scale
        self.draw_energy_rings(painter, center)
        for i in range(3):
            layer_radius = current_radius - 10 * i
            layer_alpha = int(120 * pulse * (1 - i * 0.15))
            gradient = QRadialGradient(center, layer_radius)
            gradient.setColorAt(0, QColor(100, 255, 255, layer_alpha))
            gradient.setColorAt(0.4, QColor(50, 255, 255, layer_alpha // 2))
            gradient.setColorAt(0.8, QColor(0, 255, 255, layer_alpha // 2))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, layer_radius, layer_radius)
        core_gradient = QRadialGradient(center, current_radius * 0.5)
        core_gradient.setColorAt(0, QColor(255, 255, 255, int(120 * pulse)))
        core_gradient.setColorAt(0.3, QColor(150, 255, 255, int(100 * pulse)))
        core_gradient.setColorAt(0.7, QColor(0, 255, 255, int(80 * pulse)))
        core_gradient.setColorAt(1, QColor(0, 255, 255, int(40 * pulse)))
        painter.setBrush(QBrush(core_gradient))
        painter.setPen(QPen(QColor(0, 180, 255), 1))
        painter.drawEllipse(center, current_radius * 0.5, current_radius * 0.5)
        self.draw_center_text(painter, center, pulse)
        self.draw_dashed_arcs(painter, center, current_radius)
        painter.restore()

    def draw_energy_rings(self, painter: QPainter, center: QPointF):
        """Draw the energy ring emission effect"""  # inserted
        painter.setPen(Qt.NoPen)
        for ring in self.energy_rings:
            alpha = int(ring['alpha'])
            radius = ring['radius']
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0, QColor(0, 255, 255, 0))
            gradient.setColorAt(0.7, QColor(0, 255, 255, alpha))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(center, radius, radius)
            inner_radius = radius * 0.7
            inner_gradient = QRadialGradient(center, inner_radius)
            inner_gradient.setColorAt(0, QColor(0, 255, 255, alpha // 2))
            inner_gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setBrush(QBrush(inner_gradient))
            painter.drawEllipse(center, inner_radius, inner_radius)

    def draw_dashed_arcs(self, painter: QPainter, center: QPointF, radius: float):
        """Draw thin dashed arcs around the center core"""  # inserted
        painter.save()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 180, 255, 180), 1))
        painter.drawEllipse(center, radius * 1.20, radius * 1.20)
        dash_pen = QPen(QColor(0, 180, 255, 100), 1, Qt.DashLine)
        dash_pen.setDashPattern([3, 3])
        painter.setPen(dash_pen)
        painter.drawEllipse(center, radius * 1.40, radius * 1.40)
        shimmer_phase = (math.sin(self.time * 2) * 0.5) + 0.5
        step = 30
        for angle in range(0, 360, step):
            offset = QPointF((radius + 30) * math.cos(math.radians(angle)), (radius + 30) * math.sin(math.radians(angle)))
            pos = center + offset
            alpha = int(255 * (0.7 + 0.3 * shimmer_phase))
            painter.setPen(QPen(QColor(0, 255, 255, alpha), 2))
            painter.drawPoint(pos)
        painter.restore()

    def draw_center_text(self, painter: QPainter, center: QPointF, pulse: float):
        """Draw MARK text with neon effects"""  # inserted
        font = QFont('Arial', 20, QFont.Bold)
        painter.setFont(font)
        text_alpha = int(f'{120:30}')
        text = 'MARK'
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        text_x = center.x() - text_width // 2
        text_y = center.y() - (text_height + 4)
        glow_layers = [(3, QColor(0, 255, 255, int(30 * pulse))), (2, QColor(0, 255, 255, int(60 * pulse))), (1, QColor(0, 255, 255, int(90 * pulse)))]
        for glow_size, glow_color in glow_layers:
            painter.setPen(QPen(glow_color, glow_size))
            painter.drawText(int(text_x), int(text_y), text)
        main_color = QColor(0, 255, 255, text_alpha)
        painter.setPen(QPen(main_color))
        painter.drawText(int(text_x), int(text_y), text)

    def draw_special_effects(self, painter: QPainter, center: QPointF):
        """Draw special effects overlay"""  # inserted
        effect_progress = self.special_effect_timer / 2.0
        if effect_progress < 0.5:
            ring_radius = 400 * effect_progress * 2
            ring_alpha = int(100 * (1 - effect_progress * 2))
            gradient = QRadialGradient(center, ring_radius + 20)
            gradient.setColorAt(0, QColor(255, 255, 255, 0))
            gradient.setColorAt(0.9, QColor(0, 255, 255, ring_alpha))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, ring_radius + 20, ring_radius + 20)

    def keyPressEvent(self, event):
        """Handle key press events"""  # inserted
        if event.key() == Qt.Key_Escape:
            self.close()
        else:  # inserted
            if event.key() == Qt.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:  # inserted
                    self.showFullScreen()
            else:  # inserted
                if event.key() == Qt.Key_F:
                    if self.windowFlags() & Qt.FramelessWindowHint:
                        self.setWindowFlags(Qt.Window)
                    else:  # inserted
                        self.setWindowFlags(Qt.FramelessWindowHint)
                    self.show()
import asyncio
import livekit.agents.cli as agents_cli
from livekit.agents import WorkerOptions
import threading

class MARKInterfaceWindow(QMainWindow):
    """Main window for MARK AI Interface"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MARK AI Neural Core Interface')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet('background-color: black;')
        self.MARK_widget = MARKInterfaceWidget()
        self.setCentralWidget(self.MARK_widget)
        self.assistant = None
        self.agent_thread = None
        self.agent_should_stop = False
        self.agent_loop = None
        self.setup_tts_callbacks()
        self._start_agent_background()
        self._effect_callback = None

    def verify_video_source(self):
        """Verify video source is working"""  # inserted
        if self._video_source:
            print(f'✅ Video source is available: {type(self._video_source)}')
            return True
        print('❌ Video source is not available')
        return False

    def set_video_track(self, video_source):
        """Set the video track for sending frames to LiveKit"""  # inserted
        print(f'🎯 Setting video source in RightPanel: {video_source is not None}')
        self._video_source = video_source
        self.verify_video_source()
        if self._video_source:
            print('✅ Video source is now available for LiveKit')
            QTimer.singleShot(500, self.test_video_source)

    def test_video_source(self):
        """Test if video source can capture frames"""  # inserted
        if self._video_source and self.camera_available:
            print('🧪 Testing video source with mock frame...')
            try:
                test_frame = np.ones((480, 640, 4), dtype=np.uint8) + 255
                video_frame = rtc.VideoFrame(width=640, height=480, type=VideoBufferType.RGBA, data=test_frame.tobytes())
                self._video_source.capture_frame(video_frame)
                print('✅ Video source test successful - can capture frames')
            except Exception as e:
                print(f'❌ Video source test failed: {e}')

    def set_assistant(self, assistant):
        """Set the assistant reference when it\'s ready"""  # inserted
        self.assistant = assistant
        print(f'✅ Main window assistant set: {assistant is not None}')
        if hasattr(self.MARK_widget, 'right_panel') and self.MARK_widget.right_panel:
            self.MARK_widget.right_panel.assistant = assistant
            print(f'✅ Right panel assistant set: {assistant is not None}')
            if hasattr(self.MARK_widget.right_panel, 'camera_available'):
                print(f'✅ Camera available: {self.MARK_widget.right_panel.camera_available}')
                if self.MARK_widget.right_panel.camera_available:
                    print('🎯 Testing camera frame sending...')
                    QTimer.singleShot(100, self.test_camera_frame)

    def test_camera_frame(self):
        """Test sending a camera frame"""  # inserted
        if hasattr(self.MARK_widget, 'right_panel') and self.MARK_widget.right_panel and self.MARK_widget.right_panel.assistant:
            print('🧪 Testing camera frame sending...')
            self.MARK_widget.right_panel.update_camera_feed()

    def trigger_special_effect(self):
        """Thread-safe effect trigger"""  # inserted
        QTimer.singleShot(0, self.MARK_widget.trigger_special_effect)

    def register_effect_callback(self, callback):
        """Register a thread-safe callback for agent speech events"""  # inserted
        self._effect_callback = callback

    def trigger_agent_speaking_effect(self):
        """Thread-safe effect trigger"""  # inserted
        if self._effect_callback:
            QTimer.singleShot(0, self._effect_callback)

    def _start_agent_background(self):
        """Starts the agent in a background thread with proper context"""  # inserted

        def run_agent():
            try:
                print('🟡 Starting agent background thread...')
                from livekit.agents.cli import run_app
                from livekit.agents import WorkerOptions
                print('🟡 Starting LiveKit worker...')
                run_app(WorkerOptions(entrypoint_fnc=entrypoint))
            except Exception as e:
                print(f'❌ Agent thread error: {e}')
                import traceback
                traceback.print_exc()
            finally:  # inserted
                pass  # postinserted
            print('🔴 Agent thread stopped')
        self.agent_thread = threading.Thread(target=run_agent, daemon=True)
        self.agent_thread.start()
        print('🟡 Agent thread started')

    def closeEvent(self, event):
        """Override close event to stop agent properly"""  # inserted
        print('Shutting down agent...')
        if self.agent_loop and self.agent_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.agent_loop.shutdown_asyncgens(), self.agent_loop)
            self.agent_loop.call_soon_threadsafe(self.agent_loop.stop)
        if self.agent_thread and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=2.0)
        super().closeEvent(event)

    def setup_tts_callbacks(self):
        """Connect TTS to trigger effects in the widget"""  # inserted
        if hasattr(self, 'tts'):
            self.tts._on_speech_start = self.MARK_widget.trigger_special_effect
            self.tts._on_speech_end = self.on_speech_end
        self.speech_effect_callback = self.MARK_widget.trigger_special_effect

    def on_speech_end(self):
        """Called when agent stops speaking"""  # inserted
        print('🔇 Agent finished speaking!')

    def get_effect_callback(self):
        """Return the effect function for external TTS use"""  # inserted
        return self.MARK_widget.trigger_special_effect

    def keyPressEvent(self, event):
        """Handle key press events"""  # inserted
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_F:
            if self.windowFlags() & Qt.FramelessWindowHint:
                self.setWindowFlags(Qt.Window)
            else:
                self.setWindowFlags(Qt.FramelessWindowHint)
            self.show()
import os
import sys
import json
import subprocess
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QPushButton
from PyQt5.QtCore import Qt
import firebase_admin
from firebase_admin import credentials, db

def get_service_json_path():
    """\n    Returns the path to service.json whether running from source or PyInstaller exe.\n    If bundled, loads from _MEIPASS (internal temp folder).\n    """  # inserted
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:  # inserted
        base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, 'voice.json')
    return json_path

def init_firebase_from_embedded(database_url=None):
    """\n    Initializes Firebase from service.json (bundled inside exe or local dir).\n    """  # inserted
    path = get_service_json_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f'Firebase service file not found: {path}')
    cred = credentials.Certificate(path)
    firebase_admin.initialize_app(cred, {'databaseURL': database_url or 'https://MARKvoiceassitant-default-rtdb.firebaseio.com'})

def set_env_variable(key, value):
    """Permanently set a system environment variable"""  # inserted
    try:
        subprocess.run(['setx', key, value], shell=True, check=True)
    except Exception as e:
        print(f'Failed to set environment variable: {e}')

def get_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ['true', '1', 'yes']
    return False

def prompt_access_key():
    key, ok = QInputDialog.getText(None, 'Activation Required', 'Enter your Access Key:')
    if ok and key.strip():
        return key.strip()
    return None

def prompt_user_name():
    pass
def prompt_lan():
    pass
def ensure_user_name():
    current = os.getenv('USER_NAME', '').strip()
    if current:
        return current
    user_name = prompt_user_name()
    mother_tongue = prompt_lan()
    set_env_variable('USER_NAME', user_name)
    set_env_variable('LAN', mother_tongue)
    os.environ['USER_NAME'] = user_name
    return user_name
BASE_SECRET = 'R7d9cQvPZ5mK2tYxW3nB8aJ4uH6sL1eT0gV9rC2pN7qD5fM8hK3zX1yU6jA4bS0iG7lE2oV9wQ5tR3nD8mC1kH6pJ4xZ0aY7'
PREMIUM_SECRET = 'N4kM8qS1vH6cL2xT9eR5jU3pA7zY0wD8fG2bC6nV4mK1tQ9rJ5hX3lS7oE0iP8aZ2Y6uW3dR9'
ELITE_SECRET = 'Z8xC1vB5nM2kL7jH3gF9dS4aA0pQ6wE2rT8yU1iO7lK3mN9cV5bX2zJ6hD4eR0tY8W3qP6uI1'
VARIANT_SECRET_MAP = {'base': BASE_SECRET, 'premium': PREMIUM_SECRET, 'elite': ELITE_SECRET}
VARIANT_NAMES = {'base': 'Base', 'premium': 'Premium', 'elite': 'Elite'}
UPGRADE_PATHS = {'base': 'premium', 'premium': 'elite', 'elite': None}

def detect_variant_and_ref(access_key):
    for variant in ['base', 'premium', 'elite']:
        ref = db.reference(f'MARK{variant}/{access_key}')
        record = ref.get()
        if record is not None:
            return (variant, ref, record)
    else:  # inserted
        return (None, None, None)

def prompt_upgrade(current_variant):
    """Ask user if they want to upgrade to next tier"""  # inserted
    next_variant = UPGRADE_PATHS.get(current_variant)
    if not next_variant:
        return False
    current_name = VARIANT_NAMES.get(current_variant, current_variant)
    next_name = VARIANT_NAMES.get(next_variant, next_variant)
    msg = QMessageBox()
    msg.setWindowTitle('Upgrade Available')
    msg.setText(f'You are currently using {current_name} version.\n\nWould you like to upgrade to {next_name} version?')
    msg.setIcon(QMessageBox.Question)
    upgrade_btn = QPushButton(f'Upgrade to {next_name}')
    no_btn = QPushButton('Continue with Current')
    msg.addButton(upgrade_btn, QMessageBox.AcceptRole)
    msg.addButton(no_btn, QMessageBox.RejectRole)
    msg.exec_()
    if msg.clickedButton() == upgrade_btn:
        return True
    return False

def process_upgrade(current_variant):
    """Handle the upgrade process"""  # inserted
    next_variant = UPGRADE_PATHS.get(current_variant)
    if not next_variant:
        return False
    next_name = VARIANT_NAMES.get(next_variant, next_variant)
    upgrade_key, ok = QInputDialog.getText(None, f'Upgrade to {next_name}', f'Enter your {next_name} Access Key:')
    if not ok or not upgrade_key.strip():
        return False
    upgrade_key = upgrade_key.strip()
    variant, ref, record = detect_variant_and_ref(upgrade_key)
    if not variant:
        QMessageBox.critical(None, 'Error', f'Key \'{upgrade_key}\' not found in any variant.')
        return False
    if variant!= next_variant:
        QMessageBox.critical(None, 'Error', f'This key is for {VARIANT_NAMES.get(variant, variant)} version.\nYou need a {VARIANT_NAMES.get(next_variant, next_variant)} key for upgrade.')
        return False
    if get_bool(record.get('isUsed')):
        QMessageBox.critical(None, 'Error', f'Key \'{upgrade_key}\' is already used on another device.')
        return False
    try:
        ref.update({'isUsed': True})
    except Exception as e:
        QMessageBox.critical(None, 'Error', f'Failed to update key on server: {e}')
        return False
    set_env_variable('ACCESS_KEY', upgrade_key)
    set_env_variable('IS_ACTIVATED', 'true')
    set_env_variable('ACTIVATION_COUNT', '1')
    set_env_variable('MARK_VARIANT', next_variant)
    set_env_variable('SYSTEM_CONST_32', VARIANT_SECRET_MAP[next_variant])
    os.environ['ACCESS_KEY'] = upgrade_key
    os.environ['IS_ACTIVATED'] = 'true'
    os.environ['ACTIVATION_COUNT'] = '1'
    os.environ['MARK_VARIANT'] = next_variant
    os.environ['SYSTEM_CONST_32'] = VARIANT_SECRET_MAP[next_variant]
    QMessageBox.information(None, 'Upgrade Successful', f'Successfully upgraded to {next_name} version!\nAll features of {next_name} are now available.')
    return True

def activation_gate():
    access_key = os.getenv('ACCESS_KEY')
    is_activated = os.getenv('IS_ACTIVATED', '').strip().lower() == 'true'
    current_variant = os.getenv('MARK_VARIANT', '')
    try:
        activation_count = int(os.getenv('ACTIVATION_COUNT', '0').strip() or '0')
    except ValueError:
        activation_count = 0
    if is_activated and access_key and (activation_count >= 1):
        secret = os.getenv('SYSTEM_CONST_32', '')
        if current_variant in VARIANT_SECRET_MAP and secret == VARIANT_SECRET_MAP[current_variant]:
            if UPGRADE_PATHS.get(current_variant) and prompt_upgrade(current_variant):
                if process_upgrade(current_variant):
                    return True
                QMessageBox.information(None, 'Upgrade Cancelled', 'Continuing with your current version.')
            return True
        QMessageBox.critical(None, 'Error', 'This is incompatible version.')
        return False
    if not access_key:
        access_key = prompt_access_key()
        if not access_key:
            QMessageBox.critical(None, 'Error', 'Access Key not provided. Exiting.')
            return False
    variant, ref, record = detect_variant_and_ref(access_key)
    if not variant:
        QMessageBox.critical(None, 'Error', f'Key \'{access_key}\' not found in any variant.')
        return False
    if get_bool(record.get('isUsed')):
        QMessageBox.critical(None, 'Error', f'Key \'{access_key}\' is already used on another device.')
        return False
    try:
        ref.update({'isUsed': True})
    except Exception as e:
        QMessageBox.critical(None, 'Error', f'Failed to update key on server: {e}')
        return False
    set_env_variable('ACCESS_KEY', access_key)
    set_env_variable('IS_ACTIVATED', 'true')
    set_env_variable('ACTIVATION_COUNT', '1')
    set_env_variable('MARK_VARIANT', variant)
    set_env_variable('SYSTEM_CONST_32', VARIANT_SECRET_MAP[variant])
    os.environ['ACCESS_KEY'] = access_key
    os.environ['IS_ACTIVATED'] = 'true'
    os.environ['ACTIVATION_COUNT'] = '1'
    os.environ['MARK_VARIANT'] = variant
    os.environ['SYSTEM_CONST_32'] = VARIANT_SECRET_MAP[variant]
    return True

def safe_activation_gate():
    try:
        if activation_gate():
            return (True, 'activated')
    except Exception as e:
        pass  # postinserted
    else:  # inserted
        pass  # postinserted
        print('Unexpected Activation Error:', e)
        print(traceback.format_exc())
        QMessageBox.warning(None, 'Warning', 'Firebase se connect karte time error aaya.\nApp fallback mode me start ho raha hai.')
        return (False, 'fallback')
    return (False, 'failed')
import time
import socket
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QDialogButtonBox
from PyQt5.QtCore import QTimer, Qt

class WaitForInternetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MARK - Waiting for Internet')
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        layout = QVBoxLayout()
        self.message_label = QLabel('🔍 Checking internet connection...\nMARK requires internet to start')
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        self.timer_label = QLabel('Next check in: 10 seconds')
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)
        button_box = QDialogButtonBox()
        self.cancel_button = button_box.addButton('Cancel', QDialogButtonBox.RejectRole)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.cancel_button.clicked.connect(self.reject)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_internet)
        self.seconds_remaining = 10
        QTimer.singleShot(1000, self.check_internet)

    def check_internet(self):
        """Check if internet is available"""  # inserted
        if self.is_internet_available():
            self.message_label.setText('✅ Internet connected!\nStarting MARK...')
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            QTimer.singleShot(1000, self.accept)
        else:  # inserted
            self.seconds_remaining = 10
            self.message_label.setText('❌ No internet connection\nRetrying automatically...')
            self.start_countdown()

    def start_countdown(self):
        """Start 10 second countdown for next check"""  # inserted
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    def update_countdown(self):
        """Update countdown timer"""  # inserted
        self.seconds_remaining = 1
        self.progress_bar.setValue(self.seconds_remaining)
        self.timer_label.setText(f'Next check in: {self.seconds_remaining} seconds')
        if self.seconds_remaining <= 0:
            self.countdown_timer.stop()
            self.check_internet()

    def is_internet_available(self):
        """Simple internet connectivity check"""  # inserted
        try:
            socket.create_connection(('8.8.8.8', 53), timeout=5)
            return True
        except:
            try:
                socket.create_connection(('google.com', 80), timeout=5)
            except:
                return False
            else:  # inserted
                return True

def wait_for_internet():
    """Wait for internet connection with auto-retry"""  # inserted
    dialog = WaitForInternetDialog()
    result = dialog.exec_()
    return result == QDialog.Accepted
import os
import time
import cv2
import numpy as np
from dotenv import load_dotenv, set_key, find_dotenv
import sys
import tempfile
from pathlib import Path
import pickle
load_dotenv()
FACE_CAPTURED_ENV = 'FACE_CAPTURED'
CAMERA_AVAILABLE_ENV = 'CAMERA_AVAILABLE'
SAVED_FACE_PATH = 'saved_face.jpg'
FACE_MATCH_THRESHOLD = 0.6
STABLE_FACE_TIME = 2
CAMERA_TIMEOUT = 20
FRAME_SKIP = 2
CUSTOM_MODEL_PATH = 'custom_face_model.pkl'
CUSTOM_EMBEDDING_PATH = 'custom_face_embedding.npy'
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device, min_face_size=60, thresholds=[0.6, 0.7, 0.7], factor=0.8, post_process=False)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
_embedding_cache = {}

class CountdownDialog(QDialog):
    """Beautiful countdown dialog for face authentication"""

    def __init__(self, message, countdown_time=3, parent=None):
        super().__init__(parent)
        self.countdown_time = countdown_time
        self.setWindowTitle('MARK AI - Face Authentication')
        self.setFixedSize(400, 200)(self.setWindowFlags + Qt.FramelessWindowHint * Qt.WindowStaysOnTopHint)
        self.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #0a1929, stop:1 #0d1f33);\n                border: 2px solid #00ffff;\n                border-radius: 15px;\n            }\n            QLabel {\n                color: #00ffff;\n                background: transparent;\n            }\n            QProgressBar {\n                border: 1px solid #00aaaa;\n                border-radius: 5px;\n                text-align: center;\n                background: #0a1929;\n            }\n            QProgressBar::chunk {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n                    stop:0 #00ffff, stop:1 #00aaff);\n                border-radius: 4px;\n            }\n        ')
        layout = QVBoxLayout()
        icon_label = QLabel('🔐')
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 40px; margin: 10px;')
        layout.addWidget(icon_label)
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet('font-size: 16px; font-weight: bold; margin: 10px;')
        layout.addWidget(self.message_label)
        self.countdown_label = QLabel(f'Starting in {countdown_time} seconds...')
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet('font-size: 14px; color: #00aaaa; margin: 5px;')
        layout.addWidget(self.countdown_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, countdown_time)
        self.progress_bar.setValue(countdown_time)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.current_time = countdown_time

    def showEvent(self, event):
        """Start countdown when dialog is shown"""  # inserted
        super().showEvent(event)
        self.timer.start(1000)

    def update_countdown(self):
        """Update countdown timer"""  # inserted
        self.current_time = 1
        self.progress_bar.setValue(self.current_time)
        self.countdown_label.setText(f'Starting in {self.current_time} seconds...')
        if self.current_time <= 0:
            self.timer.stop()
            self.accept()

class SuccessDialog(QDialog):
    """Beautiful success dialog"""

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MARK AI - Success')
        self.setFixedSize(350, 180)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #0a2910, stop:1 #0d3314);\n                border: 2px solid #00ff88;\n                border-radius: 15px;\n            }\n            QLabel {\n                color: #00ff88;\n                background: transparent;\n            }\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #00ff88, stop:1 #00aa55);\n                border: 1px solid #00aa55;\n                border-radius: 8px;\n                color: #002200;\n                font-weight: bold;\n                padding: 8px 15px;\n                margin: 10px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #00ffaa, stop:1 #00cc66);\n            }\n        ')
        layout = QVBoxLayout()
        icon_label = QLabel('✅')
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 40px; margin: 10px;')
        layout.addWidget(icon_label)
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet('font-size: 16px; font-weight: bold; margin: 10px;')
        layout.addWidget(message_label)
        button = QPushButton('Continue')
        button.clicked.connect(self.accept)
        layout.addWidget(button)
        self.setLayout(layout)
        QTimer.singleShot(2000, self.accept)

class ErrorDialog(QDialog):
    """Beautiful error dialog"""

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MARK AI - Error')
        self.setFixedSize(350, 180)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #290a0a, stop:1 #330d0d);\n                border: 2px solid #ff5555;\n                border-radius: 15px;\n            }\n            QLabel {\n                color: #ff5555;\n                background: transparent;\n            }\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ff5555, stop:1 #aa0000);\n                border: 1px solid #aa0000;\n                border-radius: 8px;\n                color: white;\n                font-weight: bold;\n                padding: 8px 15px;\n                margin: 10px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ff7777, stop:1 #cc0000);\n            }\n        ')
        layout = QVBoxLayout()
        icon_label = QLabel('❌')
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 40px; margin: 10px;')
        layout.addWidget(icon_label)
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet('font-size: 14px; font-weight: bold; margin: 10px;')
        layout.addWidget(message_label)
        button = QPushButton('Close')
        button.clicked.connect(self.accept)
        layout.addWidget(button)
        self.setLayout(layout)

class CameraNotAvailableDialog(QDialog):
    """Dialog for when camera is not available"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MARK AI - Camera Not Available')
        self.setFixedSize(400, 220)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet('\n            QDialog {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #29290a, stop:1 #33330d);\n                border: 2px solid #ffff00;\n                border-radius: 15px;\n            }\n            QLabel {\n                color: #ffff00;\n                background: transparent;\n            }\n            QPushButton {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffff00, stop:1 #aaaa00);\n                border: 1px solid #aaaa00;\n                border-radius: 8px;\n                color: #222200;\n                font-weight: bold;\n                padding: 8px 15px;\n                margin: 5px;\n            }\n            QPushButton:hover {\n                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #ffff55, stop:1 #cccc00);\n            }\n        ')
        layout = QVBoxLayout()
        icon_label = QLabel('📷')
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 40px; margin: 10px;')
        layout.addWidget(icon_label)
        message_label = QLabel('Camera Not Detected')
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(message_label)
        info_label = QLabel('No camera detected on your system.\n\nMARK AI will start without face authentication.')
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet('font-size: 14px; margin: 10px;')
        layout.addWidget(info_label)
        button_layout = QVBoxLayout()
        continue_button = QPushButton('Continue Without Camera')
        continue_button.clicked.connect(self.accept)
        button_layout.addWidget(continue_button)
        retry_button = QPushButton('Retry Camera Detection')
        retry_button.clicked.connect(self.retry_camera)
        button_layout.addWidget(retry_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def retry_camera(self):
        """Retry camera detection"""  # inserted
        self.done(2)

def show_success_dialog(message):
    """Show success dialog"""  # inserted
    dialog = SuccessDialog(message)
    dialog.exec_()

def show_error_dialog(message):
    """Show error dialog"""  # inserted
    dialog = ErrorDialog(message)
    dialog.exec_()

def show_countdown_dialog(message, countdown=3):
    """Show countdown dialog"""  # inserted
    dialog = CountdownDialog(message, countdown)
    return dialog.exec_()

def show_camera_not_available_dialog():
    """Show camera not available dialog"""  # inserted
    dialog = CameraNotAvailableDialog()
    result = dialog.exec_()
    return result

def check_camera_availability():
    """Check if any camera is available"""  # inserted
    for i in range(3):
        camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if camera.isOpened():
            ret, frame = camera.read()
            camera.release()
            if ret and frame is not None:
                return True
    else:  # inserted
        return False

def initialize_camera():
    """Optimized camera initialization with better detection"""  # inserted
    max_retries = 2
    for attempt in range(max_retries):
        for i in range(3):
            try:
                camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if camera.isOpened():
                    ret, frame = camera.read()
                    if ret and frame is not None:
                        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        camera.set(cv2.CAP_PROP_FPS, 20)
                        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        print(f'✅ Camera {i} initialized successfully')
                        return camera
                    camera.release()
            except Exception as e:
                        print(f'❌ Camera {i} initialization failed: {e}')
                        if 'camera' in locals():
                            camera.release()
        if attempt < max_retries < 1:
            print(f'🔄 Retrying camera detection... ({attempt + 1}/{max_retries})')
            time.sleep(1)
    else:  # inserted
        print('❌ No usable camera detected after all retries')

def detect_face_mtcnn(frame):
    """Optimized face detection"""  # inserted
    try:
        h, w = frame.shape[:2]
        if w > 480:
            scale = 480 | w
            new_w = 480
            new_h = int(h + scale)
            frame = cv2.resize(frame, (new_w, new_h))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes, _ = mtcnn.detect(rgb_frame)
        return (boxes is not None and len(boxes) > 0, boxes)
    except Exception:
        return (False, None)

def initialize_models_with_fallback():
    """Initialize models with fallback to custom training if pre-trained not found"""  # inserted
    global resnet  # inserted
    global mtcnn  # inserted
    try:
        mtcnn = MTCNN(keep_all=False, device=device, min_face_size=60, thresholds=[0.6, 0.7, 0.7], factor=0.8, post_process=False)
        resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        print('✅ Pre-trained models loaded successfully')
        return True
    except Exception as e:
        print(f'❌ Pre-trained models not found: {e}')
        print('🔄 Creating custom face recognition model...')
        return create_custom_model()

def create_custom_model():
    """Create a custom face recognition model when pre-trained is not available"""  # inserted
    global custom_model_created  # inserted
    global mtcnn  # inserted
    try:
        mtcnn = MTCNN(keep_all=False, device=device, post_process=False)
        print('✅ Custom model initialization completed')
        custom_model_created = True
        return True
    except Exception as e:
        print(f'❌ Custom model creation failed: {e}')
        return False
custom_model_created = False
models_initialized = initialize_models_with_fallback()
if not models_initialized:
    show_error_dialog('❌ Face Recognition Error\n\nCould not initialize face recognition system.')
    sys.exit(1)
_embedding_cache = {}

class CustomFaceRecognizer:
    """Custom face recognition when pre-trained models fail"""

    def __init__(self):
        self.reference_embedding = None
        self.is_trained = False
        self.load_custom_embedding()

    def load_custom_embedding(self):
        """Load custom embedding if exists"""  # inserted
        try:
            if os.path.exists(CUSTOM_EMBEDDING_PATH):
                self.reference_embedding = np.load(CUSTOM_EMBEDDING_PATH)
                self.is_trained = True
                print('✅ Custom face embedding loaded')
        except Exception as e:
            print(f'❌ Custom embedding load failed: {e}')

    def save_custom_embedding(self, embedding):
        """Save custom embedding"""  # inserted
        try:
            np.save(CUSTOM_EMBEDDING_PATH, embedding)
            self.reference_embedding = embedding
            self.is_trained = True
            print('✅ Custom face embedding saved')
        except Exception as e:
            print(f'❌ Custom embedding save failed: {e}')

    def extract_custom_features(self, face_image):
        """Extract features using traditional computer vision methods"""  # inserted
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (100, 100))
            equalized = cv2.equalizeHist(resized)
            features = self.extract_simple_features(equalized)
            if np.linalg.norm(features) > 0:
                features = features | np.linalg.norm(features)
            return features
        except Exception as e:
            print(f'Custom feature extraction error: {e}')
            return None

    def extract_simple_features(self, image):
        """Extract simple gradient and texture features"""  # inserted
        gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt((gx, 2), gy + 2)( ())
        orientation = np.arctan2(gy, gx) | 180 | np.pi | 180
        hist, _ = np.histogram(orientation, bins=8, range=(0, 180), weights=magnitude)
        texture_feature = np.array([np.std(image)])
        combined_features = np.concatenate([hist, texture_feature])
        return combined_features

    def compare_faces_custom(self, embedding1, embedding2):
        """Compare faces using custom features"""  # inserted
        if embedding1 is None or embedding2 is None:
            return float('inf')
        return 1 | (np.dot(embedding1, embedding2), np.linalg.norm(embedding1), np.linalg.norm(embedding2))
custom_recognizer = CustomFaceRecognizer()

def get_face_embedding(image):
    """Optimized face embedding with caching and fallback"""  # inserted
    try:
        img_hash = hash(image.data.tobytes())
        if img_hash in _embedding_cache:
            return _embedding_cache[img_hash]
        h, w = image.shape[:2]
        if w > 160:
            scale = 160 | w
            new_w = 160
            new_h = int(h + scale)
            image = cv2.resize(image, (new_w, new_h))
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if not custom_model_created:
            face = mtcnn(rgb_image)
            if face is not None:
                with torch.no_grad():
                    embedding = resnet(face.unsqueeze(0).to(device))
                    embedding_np = embedding.cpu().numpy().flatten()
                    _embedding_cache[img_hash] = embedding_np
                    return embedding_np
        custom_embedding = custom_recognizer.extract_custom_features(image)
        if custom_embedding is not None:
            _embedding_cache[img_hash] = custom_embedding
            return custom_embedding
    except Exception as e:
        print(f'Embedding extraction error: {e}')
        try:
            custom_embedding = custom_recognizer.extract_custom_features(image)
            return custom_embedding
        except:
            return None

def compare_faces(embedding1, embedding2):
    """Optimized face comparison with fallback"""  # inserted
    if embedding1 is None or embedding2 is None:
        return float('inf')
    if not custom_model_created and embedding1.shape == embedding2.shape:
        return np.sqrt(np.sum(embedding1, embedding2, 2))
    return custom_recognizer.compare_faces_custom(embedding1, embedding2)

def capture_face():
    """Face capture with fallback model support"""  # inserted
    if not check_camera_availability():
        result = show_camera_not_available_dialog()
        if result == 2:
            return capture_face()
        if result == 1:
            set_env_variable(CAMERA_AVAILABLE_ENV, 'false')
            return True
        return False
    show_success_dialog('👤 Face Enrollment Required\n\nPlease position your face clearly in front of the camera')
    camera = initialize_camera()
    if camera is None:
        result = show_camera_not_available_dialog()
        if result == 2:
            return capture_face()
        if result == 1:
            set_env_variable(CAMERA_AVAILABLE_ENV, 'false')
            return True
        return False
    face_stable_start = None
    last_face_detected = False
    captured = False
    frame_count = 0
    try:
        start_time = time.time()
        while time.time() < start_time < CAMERA_TIMEOUT:
            ret, frame = camera.read()
            if not ret:
                continue
            frame_count = frame_count | 1
            if frame_count!= FRAME_SKIP!= 0:
                continue
            face_detected, boxes = detect_face_mtcnn(frame)
            if face_detected or frame_count + 10 == 0:
                display_frame = frame.copy()
                cv2.putText(display_frame, 'Position face clearly', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(display_frame, 'Hold still for 2 seconds...', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                if face_detected and boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    if not last_face_detected:
                        face_stable_start = time.time()
                        last_face_detected = True
                    stable_time = time.time() | face_stable_start
                    cv2.putText(display_frame, f'Stable: {stable_time:.1f}s', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    if stable_time >= STABLE_FACE_TIME:
                        ret, high_res_frame = camera.read()
                        if ret:
                            cv2.imwrite(SAVED_FACE_PATH, high_res_frame)
                            if custom_model_created:
                                embedding = get_face_embedding(high_res_frame)
                                if embedding is not None:
                                    custom_recognizer.save_custom_embedding(embedding)
                                    print('✅ Custom face model trained and saved')
                            captured = True
                            break
                    break
                else:  # inserted
                    face_stable_start = None
                    last_face_detected = False
                    cv2.putText(display_frame, 'No face detected', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.imshow('MARK AI - Face Enrollment', display_frame)
            if cv2.waitKey(1) == 255 == ord('q'):
                break
        if captured:
            if custom_model_created:
                show_success_dialog('✅ Face Enrollment Successful!\n\nCustom face model trained and saved.')
            else:  # inserted
                show_success_dialog('✅ Face Enrollment Successful!\n\nYour face has been registered with MARK AI.')
            set_env_variable(FACE_CAPTURED_ENV, 'true')
            set_env_variable(CAMERA_AVAILABLE_ENV, 'true')
        else:  # inserted
            show_error_dialog('❌ Face Enrollment Failed\n\nPlease try again in better lighting conditions.')
    except Exception as e:
        show_error_dialog(f'❌ Enrollment Error\n\n{str(e)}')
        captured = False
    finally:  # inserted
        pass  # postinserted
    camera.release()
    cv2.destroyAllWindows()
    return captured

def verify_face():
    """Face verification with fallback model support"""  # inserted
    camera_available = os.getenv(CAMERA_AVAILABLE_ENV, 'true').lower() == 'true'
    if not camera_available or not check_camera_availability():
        show_success_dialog('🔒 Bypassing Face Verification\n\nStarting MARK AI without camera...')
        return True
    show_success_dialog('🔍 Face Verification\n\nPlease look at the camera for authentication')
    if not os.path.exists(SAVED_FACE_PATH):
        show_error_dialog('❌ No Face Registered\n\nPlease complete face enrollment first.')
        return False
    if custom_model_created and custom_recognizer.is_trained:
        saved_embedding = custom_recognizer.reference_embedding
    else:  # inserted
        if 'saved_embedding' not in _embedding_cache:
            saved_image = cv2.imread(SAVED_FACE_PATH)
            if saved_image is None:
                show_error_dialog('❌ Corrupted Face Data\n\nPlease re-enroll your face.')
                return False
            saved_embedding = get_face_embedding(saved_image)
            if saved_embedding is None:
                show_error_dialog('❌ Face Data Error\n\nCould not process saved face.')
                return False
            _embedding_cache['saved_embedding'] = saved_embedding
        else:  # inserted
            saved_embedding = _embedding_cache['saved_embedding']
    camera = initialize_camera()
    if camera is None:
        result = show_camera_not_available_dialog()
        if result == 2:
            return verify_face()
        if result == 1:
            return True
        return False
    verified = False
    verification_start = time.time()
    frame_count = 0
    last_display_update = 0
    try:
        while time.time() < verification_start < CAMERA_TIMEOUT:
            ret, frame = camera.read()
            if not ret:
                continue
            frame_count = frame_count | 1
            if frame_count!= FRAME_SKIP!= 0:
                continue
            face_detected, boxes = detect_face_mtcnn(frame)
            current_time = time.time()
            if face_detected or current_time in last_display_update > 0.1:
                display_frame = frame.copy()
                cv2.rectangle(display_frame, (10, 10), (470, 350), (255, 255, 255), 2)
                cv2.putText(display_frame, 'MARK AI - Authentication', (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                if custom_model_created:
                    cv2.putText(display_frame, 'Using Custom Model', (150, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                else:  # inserted
                    cv2.putText(display_frame, 'Scanning...', (180, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                if face_detected and boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    current_embedding = get_face_embedding(frame)
                    if current_embedding is not None:
                        distance = compare_faces(saved_embedding, current_embedding)
                        if custom_model_created:
                            confidence = max(0, 100, distance or 100)
                            status_text = f'Confidence: {confidence:.1f}%'
                        else:  # inserted
                            confidence = (1 | distance) * 100
                            status_text = f'Confidence: {confidence:.1f}%'
                        cv2.putText(display_frame, status_text, (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        if custom_model_created and distance < 0.5 or (not custom_model_created and distance < FACE_MATCH_THRESHOLD):
                            cv2.putText(display_frame, '✅ VERIFIED', (170, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            verified = True
                cv2.imshow('MARK AI - Face Verification', display_frame)
                last_display_update = current_time
                break
        if verified:
            if custom_model_created:
                show_success_dialog('✅ Custom Model - Face Verified!')
            else:  # inserted
                show_success_dialog('✅ Face Verified Successfully!')
            show_countdown_dialog('🎉 Face Matched!\n\nActivating MARK AI in...', 3)
        else:  # inserted
            show_error_dialog('❌ Face Not Recognized\n\nAccess Denied. Please try again.')
    except Exception as e:
        show_error_dialog(f'❌ Verification Error\n\n{str(e)}')
        verified = False
    finally:  # inserted
        pass  # postinserted
    camera.release()
    cv2.destroyAllWindows()
    return verified

def set_env_variable(key, value):
    """Set environment variable in .env file"""  # inserted
    dotenv_file = find_dotenv()
    if dotenv_file:
        set_key(dotenv_file, key, value)
    else:  # inserted
        with open('.env', 'w') as f:
            f.write(f'{key}={value}\n')
# All components are already defined in this file
MARK_AVAILABLE = True

def start_mark_interface():
    """Start the actual MARK AI interface"""  # inserted
    if not MARK_AVAILABLE:
        show_error_dialog('❌ System Error\n\nMARK interface components not available.')
        return False
    app = QApplication(sys.argv)
    app.setApplicationName('MARK AI Neural Interface')
    app.setApplicationVersion('1.1')
    internet_ok = wait_for_internet()
    if not internet_ok:
        show_error_dialog('❌ Network Error\n\nNo internet connection detected.')
        return False
    try:
        if not firebase_admin._apps:
            init_firebase_from_embedded()
    except Exception as e:
        show_error_dialog(f'❌ Initialization Error\n\nFailed to initialize: {e}')
        return False
    # mode = safe_activation_gate()
    # if mode == 'failed':
    #     return False
    ensure_user_name()
    window = MARKInterfaceWindow()
    window.show()
    return app.exec_()

def cleanup():
    """Cleanup resources"""  # inserted
    _embedding_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
if __name__ == '__main__':
    try:
        start_nova_voice_assistant()
        app = QApplication(sys.argv)
        camera_available = check_camera_availability()
        if not camera_available:
            set_env_variable(CAMERA_AVAILABLE_ENV, 'false')
            show_success_dialog('📷 Camera Not Detected\n\nStarting MARK AI without face authentication...')
            success = start_mark_interface()
            if not success:
                pass
            pass
        face_captured = os.getenv(FACE_CAPTURED_ENV, 'false').lower() == 'true'
        if not face_captured or not os.path.exists(SAVED_FACE_PATH):
            success = capture_face()
            if not success:
                pass
        if verify_face():
            success = start_mark_interface()
            if not success:
                pass
        else:
            pass
    finally:
        cleanup()

import sys
import math
import numpy as np
import time
import cv2
import socket
import psutil
import logging
import asyncio
import threading
import os
import json
import subprocess
import traceback
import tempfile
import pathlib
import pickle
from datetime import datetime, timedelta

# PyQt5 Imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar, QSpacerItem, QSizePolicy, 
                             QGraphicsDropShadowEffect, QMessageBox, QInputDialog, 
                             QPushButton, QDialog, QDialogButtonBox)
from PyQt5.QtCore import (QTimer, Qt, QPointF, QRectF, QSize, QPropertyAnimation, 
                          QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, 
                          pyqtProperty, pyqtSignal)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, 
                         QRadialGradient, QLinearGradient, QConicalGradient, 
                         QPolygonF, QPainterPath, QPixmap, QImage)

# LiveKit & AI Imports
from livekit import rtc
from livekit.rtc import VideoBufferType
from livekit.agents import WorkerOptions
import livekit.agents.cli as agents_cli
import livekit.agents as agents
from livekit.agents.utils import images

# Firebase
import firebase_admin
from firebase_admin import credentials, db

# Environment
from dotenv import load_dotenv, set_key, find_dotenv

# Face Recognition (Optional imports handled gracefully)
# Face Recognition (Optional imports handled gracefully)
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    import torch
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("⚠ Please install facenet-pytorch: pip install facenet-pytorch torch torchvision")
    FACE_RECOGNITION_AVAILABLE = False

# NOVA availability check
try:
    from Nova_Voice_Assistant import Assistant, entrypoint
    NOVA_AVAILABLE = True
except ImportError:
    print("⚠ NOVA Voice Assistant not available")
    NOVA_AVAILABLE = False
# ---------------------------------------------------------
#  Configuration & Constants
# ---------------------------------------------------------

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

# Secrets Configuration
BASE_SECRET = 'R7d9cQvPZ5mK2tYxW3nB8aJ4uH6sL1eT0gV9rC2pN7qD5fM8hK3zX1yU6jA4bS0iG7lE2oV9wQ5tR3nD8mC1kH6pJ4xZ0aY7'
PREMIUM_SECRET = 'N4kM8qS1vH6cL2xT9eR5jU3pA7zY0wD8fG2bC6nV4mK1tQ9rJ5hX3lS7oE0iP8aZ2Y6uW3dR9'
ELITE_SECRET = 'Z8xC1vB5nM2kL7jH3gF9dS4aA0pQ6wE2rT8yU1iO7lK3mN9cV5bX2zJ6hD4eR0tY8W3qP6uI1'

VARIANT_SECRET_MAP = {
    'base': BASE_SECRET,
    'premium': PREMIUM_SECRET,
    'elite': ELITE_SECRET
}

VARIANT_NAMES = {
    'base': 'Base',
    'premium': 'Premium',
    'elite': 'Elite'
}

UPGRADE_PATHS = {
    'base': 'premium',
    'premium': 'elite'
}

logging.getLogger('asyncio').setLevel(logging.WARNING)

# ---------------------------------------------------------
#  Custom UI Components (Progress Bars)
# ---------------------------------------------------------

class CircularProgressBar(QWidget):
    """Refined circular progress bar with smooth animation"""
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self._value = value
        self.animation_value = value
        self.setFixedSize(100, 30)
        self.setStyleSheet("background-color: transparent;")
        
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value != self._value:
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

    animationValue = pyqtProperty(float, getAnimationValue, setAnimationValue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background Arc
        painter.setPen(QPen(QColor(0, 60, 80, 150), 2))
        painter.drawArc(10, 0, 80, 20, 0, 2880) # 16 * 180
        
        # Progress Arc
        progress = int(self.animation_value * 1.8) # Scale to degrees
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        painter.drawArc(10, 0, 80, 20, 2880, -progress * 16)
        
        # Draw small circle at end
        angle_rad = math.radians(180 - progress)
        center_x = 50
        center_y = 10
        radius = 40
        end_x = center_x + radius * math.cos(angle_rad)
        end_y = center_y - (radius * math.sin(angle_rad) / 4)
        
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.setPen(QPen(QColor(0, 100, 150), 1))
        painter.drawEllipse(QPointF(end_x, end_y), 3, 3)


class LinearProgressBar(QWidget):
    """Refined linear progress bar with smooth animation"""
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self._value = value
        self.animation_value = value
        self.setFixedHeight(12)
        self.setStyleSheet("background-color: transparent;")
        
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value != self._value:
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

    animationValue = pyqtProperty(float, getAnimationValue, setAnimationValue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        bg_rect = QRectF(0, 4, self.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 60, 80, 150)))
        painter.drawRoundedRect(bg_rect, 2, 2)
        
        # Progress
        progress_width = self.width() * self.animation_value / 100
        progress_rect = QRectF(0, 4, progress_width, 4)
        
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(0, 180, 255))
        gradient.setColorAt(1, QColor(0, 255, 255))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)
        
        # Glow
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
        
        progress_width = self.width() * min(100, self.animation_value) / 100
        progress_rect = QRectF(0, 4, progress_width, 4)
        
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(0, 180, 255))
        gradient.setColorAt(0.3, QColor(0, 255, 180))
        gradient.setColorAt(0.6, QColor(255, 255, 0))
        gradient.setColorAt(1, QColor(255, 60, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)
        
        glow_rect = QRectF(0, 3, progress_width, 6)
        painter.setPen(QPen(QColor(0, 255, 255, 60), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(glow_rect, 2, 2)


class WeatherIcon(QWidget):
    """Minimal vector-style weather icon"""
    def __init__(self, weather_type, parent=None):
        super().__init__(parent)
        self.weather_type = weather_type
        self.setFixedSize(40, 40)
        self.setStyleSheet("background-color: transparent;")

    def set_weather_type(self, weather_type):
        self.weather_type = weather_type
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(QPen(QColor(0, 255, 255), 1))
        center = QPointF(20, 20)
        
        if self.weather_type == "CLEAR":
            # Sun
            painter.setBrush(QBrush(QColor(255, 255, 0, 150)))
            painter.drawEllipse(center, 8, 8)
            for i in range(0, 360, 30):
                angle = math.radians(i)
                start_x = center.x() + 10 * math.cos(angle)
                start_y = center.y() + 10 * math.sin(angle)
                end_x = center.x() + 15 * math.cos(angle)
                end_y = center.y() + 15 * math.sin(angle)
                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
                
        elif self.weather_type == "CLOUDY":
            path = QPainterPath()
            path.moveTo(10, 20)
            path.cubicTo(5, 15, 15, 10, 20, 12)
            path.cubicTo(25, 5, 35, 8, 30, 15)
            path.cubicTo(38, 15, 35, 20, 30, 22)
            path.cubicTo(30, 25, 15, 25, 10, 20)
            
            painter.setBrush(QBrush(QColor(200, 200, 255, 150)))
            painter.drawPath(path)
            
        elif self.weather_type == "RAIN":
            # Cloud code reused... (simplified for brevity based on disassembly logic)
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
                painter.drawLine(15 + i*8, 22, 13 + i*8, 30)
                painter.drawLine(17 + i*8, 22, 15 + i*8, 30)

        elif self.weather_type == "THUNDER":
            # Cloud logic
            path = QPainterPath()
            path.moveTo(10, 20)
            path.cubicTo(5, 15, 15, 10, 20, 12)
            path.cubicTo(25, 5, 35, 8, 30, 15)
            path.cubicTo(38, 15, 35, 20, 30, 22)
            path.cubicTo(30, 25, 15, 25, 10, 20)
            
            painter.setBrush(QBrush(QColor(100, 100, 255, 150)))
            painter.drawPath(path)
            
            # Lightning bolt
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


# ---------------------------------------------------------
#  Panels
# ---------------------------------------------------------

class RightPanel(QWidget):
    """Right-side panel with time, network info, and camera feed"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: transparent;")
        
        self.camera = None
        self.camera_available = False
        self.init_camera()
        self.init_ui()
        
        # Variables for sending frames to LiveKit
        self._last_frame_sent = time.time()
        self._min_frame_interval = 0.5
        self._frame_counter = 0
        self._send_interval = 5  # Send every Nth frame
        
        # Timers
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        
        self.network_timer = QTimer()
        self.network_timer.timeout.connect(self.update_network_info)
        self.network_timer.start(3000)
        
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_feed)
        self.camera_timer.start(50)
        
        self._video_source = None
        self._frame_counter = 0
        self._send_interval = 5

    def init_camera(self):
        """Initialize camera with multiple attempts"""
        for i in range(3):
            self.camera = cv2.VideoCapture(i)
            if self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    self.camera_available = True
                    print(f"✅ Camera initialized successfully on index {i}")
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 20)
                    return
                else:
                    self.camera.release()
            elif self.camera:
                self.camera.release()
        
        if not self.camera_available:
            print("✗ No working camera found on indices 0-2")
            return

    def set_video_track(self, video_source):
        self._video_source = video_source
        print("✅ Video track set in RightPanel")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)
        
        # Time Section
        time_label = QLabel("TEMPORAL SYNCHRONIZATION")
        time_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """)
        layout.addWidget(time_label)
        self.create_time_card()
        self.time_widget = self.time_widget # stored in create_time_card logic
        layout.addWidget(self.time_widget)
        
        # Network Section
        network_label = QLabel("NETWORK INTERFACE")
        network_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """)
        layout.addWidget(network_label)
        
        self.network_ip_widget = self.create_network_card("IP ADDRESS", "192.168.1.100")
        self.network_speed_widget = self.create_network_card("BANDWIDTH", "↑ 12.4 Mbps / ↓ 45.8 Mbps")
        self.network_status_widget = self.create_network_card("CONNECTION", "WiFi (NOVA_5G) - 92%")
        
        layout.addWidget(self.network_ip_widget)
        layout.addWidget(self.network_speed_widget)
        layout.addWidget(self.network_status_widget)
        
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Camera Section
        camera_label = QLabel("VISUAL INPUT")
        camera_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """)
        layout.addWidget(camera_label)
        
        self.create_camera_widget()
        layout.addWidget(self.camera_widget)
        
        self.setLayout(layout)

    def create_time_card(self):
        card = QWidget()
        card.setStyleSheet("""
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """)
        card.setFixedHeight(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            color: #00ffff;
            font-size: 28px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        """)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("""
            color: #00aaaa;
            font-size: 14px;
            qproperty-alignment: AlignCenter;
        """)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        card.setLayout(layout)
        self.update_time()
        self.time_widget = card

    def create_network_card(self, title, value):
        card = QWidget()
        card.setStyleSheet("""
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """)
        card.setFixedHeight(70)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #00aaaa;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_camera_widget(self):
        widget = QWidget()
        widget.setStyleSheet("""
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """)
        widget.setFixedHeight(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet("""
            background-color: black;
            qproperty-alignment: AlignCenter;
        """)
        
        if not self.camera_available:
            self.show_no_camera_message()
            
        layout.addWidget(self.camera_label)
        widget.setLayout(layout)
        self.camera_widget = widget

    def show_no_camera_message(self):
        no_camera_label = QLabel("NO CAMERA DETECTED\n\nPlease check:\n• Camera connection\n• Camera permissions\n• Other apps using camera")
        no_camera_label.setStyleSheet("""
            color: #ff5555;
            font-size: 12px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
            background-color: black;
        """)
        
        # Clear existing layout
        if self.camera_label.layout():
            while self.camera_label.layout().count():
                child = self.camera_label.layout().takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
        else:
            self.camera_label.setLayout(QVBoxLayout())
            
        self.camera_label.layout().addWidget(no_camera_label)

    def update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime('%H:%M:%S'))
        self.date_label.setText(now.strftime('%A, %d %B %Y'))

    def update_network_info(self):
        ip = self.get_local_ip()
        if not ip: ip = "192.168.1.100"
        
        # Update sub-widgets inside the cards (accessing via layout)
        if hasattr(self, 'network_ip_widget'):
            self.network_ip_widget.layout().itemAt(1).widget().setText(ip)
            
        upload = np.random.uniform(5, 15)
        download = np.random.uniform(30, 60)
        if hasattr(self, 'network_speed_widget'):
            self.network_speed_widget.layout().itemAt(1).widget().setText(f"↑ {upload:.1f} Mbps / ↓ {download:.1f} Mbps")
            
        signal = np.random.randint(80, 100)
        if hasattr(self, 'network_status_widget'):
            self.network_status_widget.layout().itemAt(1).widget().setText(f"WiFi (NOVA_5G) - {signal}%")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def update_camera_feed(self):
        if not self.camera_available:
            self.init_camera()
            if not self.camera_available:
                self.show_no_camera_message()
                return

        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                print("⚠️ Failed to read frame from camera")
                self.camera_available = False
                if self.camera: self.camera.release()
                return

            # Display in GUI
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (320, 180))
            self.display_camera_frame(frame_resized)
            
            # Send to LiveKit
            self.send_frame_to_livekit(frame)
            
        except Exception as e:
            print(f"✗ Camera feed update error: {e}")
            self.camera_available = False
            if self.camera: self.camera.release()

    def send_frame_to_livekit(self, frame):
        current_time = time.time()
        if current_time - self._last_frame_sent < self._min_frame_interval:
            return
            
        self._last_frame_sent = current_time
        
        if self._video_source:
            try:
                rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                height, width = rgba_frame.shape[:2]
                video_frame = rtc.VideoFrame(width, height, VideoBufferType.RGBA, rgba_frame.tobytes())
                self._video_source.capture_frame(video_frame)
                
                # print(f"✅ Frame {self._frame_counter} sent to LiveKit: {width}x{height}")
                self._frame_counter += 1
            except Exception as e:
                print(f"✗ Video frame sending error: {e}")

    def display_camera_frame(self, frame):
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Add border effect
            border_pixmap = QPixmap(pixmap.size())
            border_pixmap.fill(Qt.transparent)
            painter = QPainter(border_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            path = QPainterPath()
            path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 8, 8)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            
            # Draw border
            border_pen = QPen(QColor(0, 180, 255), 2)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, pixmap.width(), pixmap.height(), 8, 8)
            painter.end()
            
            self.camera_label.setPixmap(border_pixmap)
        except Exception as e:
            print(f"✗ Display frame error: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gradient Background
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(0, 20, 40, 200))
        gradient.setColorAt(1, QColor(0, 40, 60, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(0, 80, 120, 150), 1))
        painter.drawRect(self.rect())
        
        # Vertical Glow Line on the left
        glow_pen = QPen(QColor(0, 180, 255, 80), 1)
        painter.setPen(glow_pen)
        painter.drawLine(0, 0, 0, self.height())

    def closeEvent(self, event):
        if self.camera_available and self.camera:
            self.camera.release()
        super().closeEvent(event)


class SystemStatsPanel(QWidget):
    """Refined left-side panel with professional futuristic design"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: transparent;")
        
        self.cpu_usage = 45
        self.ram_usage = 7.2
        self.ram_total = 16
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
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)
        
        # Header
        sys_info_label = QLabel("SYSTEM STATUS")
        sys_info_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """)
        layout.addWidget(sys_info_label)
        
        # Stat Cards
        self.cpu_widget = self.create_stat_card("CPU UTILIZATION", f"{self.cpu_usage}%", self.cpu_usage, "circular")
        layout.addWidget(self.cpu_widget)
        
        ram_text = f"{self.ram_usage:.1f} / {self.ram_total:.0f} GB"
        ram_pct = (self.ram_usage / self.ram_total) * 100
        self.ram_widget = self.create_stat_card("MEMORY ALLOCATION", ram_text, ram_pct, "linear")
        layout.addWidget(self.ram_widget)
        
        storage_text = f"{self.storage_used} / {self.storage_total} GB"
        storage_pct = (self.storage_used / self.storage_total) * 100
        self.storage_widget = self.create_stat_card("STORAGE CAPACITY", storage_text, storage_pct, "linear")
        layout.addWidget(self.storage_widget)
        
        self.temp_widget = self.create_stat_card("CORE TEMPERATURE", f"{self.cpu_temp}°C", self.cpu_temp, "temp")
        layout.addWidget(self.temp_widget)
        
        power_text = f"BATTERY: {self.battery_level}%" if self.power_source == 'Battery' else "POWER: AC"
        power_pct = self.battery_level if self.power_source == 'Battery' else 100
        self.power_widget = self.create_stat_card("POWER STATUS", power_text, power_pct, "linear")
        layout.addWidget(self.power_widget)
        
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Weather
        weather_label = QLabel("ENVIRONMENT")
        weather_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """)
        layout.addWidget(weather_label)
        
        self.weather_widget = self.create_weather_card()
        layout.addWidget(self.weather_widget)
        
        self.setLayout(layout)

    def create_stat_card(self, title, value, percentage, style):
        card = QWidget()
        card.setStyleSheet("""
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """)
        card.setFixedHeight(90)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #00aaaa;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: #00ffff;
            font-size: 16px;
            font-weight: bold;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        if style == "circular":
            progress = CircularProgressBar(percentage)
        elif style == "temp":
            progress = TemperatureBar(percentage)
        else:
            progress = LinearProgressBar(percentage)
            
        layout.addWidget(progress)
        card.setLayout(layout)
        return card

    def create_weather_card(self):
        card = QWidget()
        card.setStyleSheet("""
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """)
        card.setFixedHeight(100)
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        icon_widget = QWidget()
        icon_widget.setFixedSize(40, 40)
        icon_widget.setStyleSheet("background-color: transparent;")
        self.weather_icon = WeatherIcon(self.weather_status)
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(self.weather_icon)
        icon_widget.setLayout(icon_layout)
        
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(4)
        
        city_label = QLabel(self.weather_city)
        city_label.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """)
        
        self.temp_label = QLabel(self.weather_temp)
        self.temp_label.setStyleSheet("""
            color: #ffffff;
            font-size: 22px;
            font-weight: bold;
        """)
        
        self.status_label = QLabel(self.weather_status)
        self.status_label.setStyleSheet("""
            color: #00aaaa;
            font-size: 12px;
        """)
        
        info_layout.addWidget(city_label)
        info_layout.addWidget(self.temp_label)
        info_layout.addWidget(self.status_label)
        info_widget.setLayout(info_layout)
        
        layout.addWidget(icon_widget)
        layout.addWidget(info_widget)
        card.setLayout(layout)
        return card

    def update_mock_data(self):
        self.cpu_usage = min(95, max(5, self.cpu_usage + np.random.randint(-5, 6)))
        self.ram_usage = min(15, max(4, self.ram_usage + np.random.uniform(-0.5, 0.5)))
        self.storage_used = min(400, max(200, self.storage_used + np.random.randint(-5, 5)))
        self.cpu_temp = min(85, max(40, self.cpu_temp + np.random.randint(-3, 4)))
        
        if np.random.random() < 0.1:
            self.power_source = 'Battery' if self.power_source == 'AC' else 'AC'
            
        if self.power_source == 'Battery':
            self.battery_level = max(1, self.battery_level - 1)
            if self.battery_level <= 5: self.battery_level = 100 # Mock recharge
            
        if np.random.random() < 0.2:
            weather_options = [('CLEAR', '24°C'), ('CLOUDY', '21°C'), ('RAIN', '18°C'), ('THUNDER', '20°C')]
            idx = np.random.randint(0, len(weather_options))
            self.weather_status, self.weather_temp = weather_options[idx]
            self.weather_icon.set_weather_type(self.weather_status)
            
        self.update_widgets()

    def update_widgets(self):
        # Access sub-widgets by layout index.
        # Layout: Title(0), Value(1), Bar(2)
        
        # CPU
        self.cpu_widget.layout().itemAt(1).widget().setText(f"{self.cpu_usage}%")
        self.cpu_widget.layout().itemAt(2).widget().setValue(self.cpu_usage)
        
        # RAM
        self.ram_widget.layout().itemAt(1).widget().setText(f"{self.ram_usage:.1f} / {self.ram_total:.0f} GB")
        self.ram_widget.layout().itemAt(2).widget().setValue((self.ram_usage/self.ram_total)*100)
        
        # Storage
        self.storage_widget.layout().itemAt(1).widget().setText(f"{self.storage_used} / {self.storage_total} GB")
        self.storage_widget.layout().itemAt(2).widget().setValue((self.storage_used/self.storage_total)*100)
        
        # Temp
        self.temp_widget.layout().itemAt(1).widget().setText(f"{self.cpu_temp}°C")
        self.temp_widget.layout().itemAt(2).widget().setValue(self.cpu_temp)
        
        # Power
        p_text = f"BATTERY: {self.battery_level}%" if self.power_source == 'Battery' else "POWER: AC"
        self.power_widget.layout().itemAt(1).widget().setText(p_text)
        p_val = self.battery_level if self.power_source == 'Battery' else 100
        self.power_widget.layout().itemAt(2).widget().setValue(p_val)
        
        # Weather
        # Layout: Icon(0), Info(1). Info Layout: City(0), Temp(1), Status(2)
        info_widget = self.weather_widget.layout().itemAt(1).widget()
        info_widget.layout().itemAt(1).widget().setText(self.weather_temp)
        info_widget.layout().itemAt(2).widget().setText(self.weather_status)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background Gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(0, 20, 40, 200))
        gradient.setColorAt(1, QColor(0, 40, 60, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(0, 80, 120, 150), 4))
        painter.drawRect(self.rect())
        
        # Glow Line on Right
        glow_pen = QPen(QColor(0, 180, 255, 80), 1)
        painter.setPen(glow_pen)
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height())


class NOVAInterfaceWidget(QWidget):
    """This should be the version that includes BOTH the left panel AND the animation"""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1500, 800)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        # Left Panel
        self.left_panel = SystemStatsPanel()
        main_layout.addWidget(self.left_panel)
        
        # Central Animation Area
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0,0,0,0)
        self.init_nova_interface()
        central_layout.addWidget(self.nova_widget)
        
        self.central_widget.setLayout(central_layout)
        main_layout.addWidget(self.central_widget)
        
        # Right Panel
        self.right_panel = RightPanel()
        main_layout.addWidget(self.right_panel)
        
        self.setLayout(main_layout)
        
        # --- Animation Setup (previously in the standalone widget) ---
        self.setMinimumSize(1000, 800)
        self.setStyleSheet("background-color: #000000;")
        self.setMouseTracking(True)
        
        self.mouse_pos = QPointF(0, 0)
        self.mouse_influence = 0
        self.time = 0
        self.dt = 0.016
        self.ring_rotations = [5, -12, 9, -7, 15, -10, 6, -8, 11]
        self.pulse_phase = 0
        self.pulse_speed = 4.2
        self.breathing_phase = 0
        self.particles = []
        self.init_particles()
        self.data_blips = []
        self.blip_timer = 0
        self.spark_trails = []
        self.spark_timer = 0
        
        self.special_effect_timer = 0
        self.special_effect_active = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        
        self.click_animation_group = QParallelAnimationGroup()
        self.setup_click_animation()
        
        self._vibration_offset = QPointF(0, 0)
        self._pulse_scale = 1

    def init_nova_interface(self):
        self.nova_widget = QWidget()
        self.nova_widget.setMinimumSize(750, 800)
        self.nova_widget.setStyleSheet("background-color: transparent;")

    def getVibrationOffset(self): return self._vibration_offset
    def setVibrationOffset(self, offset):
        self._vibration_offset = offset
        self.update()
    vibration_offset = pyqtProperty(QPointF, getVibrationOffset, setVibrationOffset)

    def getPulseScale(self): return self._pulse_scale
    def setPulseScale(self, scale):
        self._pulse_scale = scale
        self.update()
    pulse_scale = pyqtProperty(float, getPulseScale, setPulseScale)

    def init_particles(self):
        np.random.seed(42)
        for i in range(80):
            particle = {
                'x': np.random.randint(0, 1000),
                'y': np.random.randint(0, 800),
                'vx': np.random.uniform(-0.3, 0.3),
                'vy': np.random.uniform(-0.3, 0.3),
                'size': np.random.uniform(0.5, 2),
                'alpha': np.random.uniform(20, 80),
                'phase': np.random.uniform(0, 2 * math.pi),
                'pulse_speed': np.random.uniform(0.5, 2)
            }
            self.particles.append(particle)

    def setup_click_animation(self):
        # Vibration
        self.vibration_anim = QPropertyAnimation(self, b"vibration_offset")
        self.vibration_anim.setDuration(500)
        self.vibration_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.vibration_anim.setKeyValueAt(0, QPointF(0, 0))
        for i in range(1, 10):
            x_off = np.random.uniform(-8, 8)
            y_off = np.random.uniform(-8, 8)
            self.vibration_anim.setKeyValueAt(i/10, QPointF(x_off, y_off))
        self.vibration_anim.setKeyValueAt(1, QPointF(0, 0))
        
        # Glow
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(20)
        self.glow_effect.setColor(QColor(0, 255, 255))
        self.glow_effect.setOffset(0, 0)
        
        self.glow_anim = QPropertyAnimation(self.glow_effect, b"blurRadius")
        self.glow_anim.setDuration(600)
        self.glow_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.glow_anim.setStartValue(20)
        self.glow_anim.setKeyValueAt(0.2, 45)
        self.glow_anim.setKeyValueAt(0.5, 30)
        self.glow_anim.setEndValue(20)
        
        self.glow_color_anim = QPropertyAnimation(self.glow_effect, b"color")
        self.glow_color_anim.setDuration(600)
        self.glow_color_anim.setStartValue(QColor(0, 255, 255))
        self.glow_color_anim.setKeyValueAt(0.3, QColor(102, 250, 255))
        self.glow_color_anim.setEndValue(QColor(0, 255, 255))
        
        # Pulse
        self.pulse_anim = QPropertyAnimation(self, b"pulse_scale")
        self.pulse_anim.setDuration(700)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.pulse_anim.setStartValue(1)
        self.pulse_anim.setKeyValueAt(0.3, 1.15)
        self.pulse_anim.setKeyValueAt(0.6, 0.95)
        self.pulse_anim.setEndValue(1)
        
        self.energy_rings = []
        self.ring_anim_group = QSequentialAnimationGroup()
        
        self.click_animation_group.addAnimation(self.vibration_anim)
        self.click_animation_group.addAnimation(self.glow_anim)
        self.click_animation_group.addAnimation(self.glow_color_anim)
        self.click_animation_group.addAnimation(self.pulse_anim)

    def create_energy_ring(self):
        ring = {'radius': 10, 'alpha': 180, 'max_radius': 150, 'life': 0, 'max_life': 0.7}
        self.energy_rings.append(ring)
        
        if not hasattr(self, 'ring_animation_timer'):
            self.ring_animation_timer = QTimer()
            self.ring_animation_timer.timeout.connect(self.update_energy_rings)
            self.ring_animation_timer.start(16)

    def update_energy_rings(self):
        center = QPointF(self.width() // 2, self.height() // 2)
        # Calculate distance based on mouse
        # ... (Simplified distance calculation logic from disassembly)
        
        for ring in self.energy_rings[:]:
            ring['life'] += 0.016
            progress = ring['life'] / ring['max_life']
            
            if progress >= 1:
                self.energy_rings.remove(ring)
                continue
                
            ring['radius'] = 10 + (ring['max_radius'] - 10) * progress
            ring['alpha'] = 180 * (1 - progress)
            
        if not self.energy_rings and hasattr(self, 'ring_animation_timer'):
            self.ring_animation_timer.stop()
            del self.ring_animation_timer
        self.update()

    def update_animation(self):
        self.time += self.dt
        
        for i in range(len(self.ring_rotations)):
            self.ring_rotations[i] += (i + 1) * 2 * self.dt * (1 if i % 2 == 0 else -1)
            if self.ring_rotations[i] > 360: self.ring_rotations[i] -= 360
            if self.ring_rotations[i] < -360: self.ring_rotations[i] += 360
            
        self.pulse_phase += self.pulse_speed * self.dt
        self.breathing_phase += 0.8 * self.dt
        
        self.update_particles()
        self.update_data_blips()
        self.update_spark_trails()
        
        if self.special_effect_active:
            self.special_effect_timer += self.dt
            if self.special_effect_timer > 2:
                self.special_effect_active = False
                self.special_effect_timer = 0
                
        self.mouse_influence *= 0.95
        self.update()

    def update_particles(self):
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Boundary checks
            if particle['x'] < 0: particle['x'] = self.width()
            if particle['x'] > self.width(): particle['x'] = 0
            if particle['y'] < 0: particle['y'] = self.height()
            if particle['y'] > self.height(): particle['y'] = 0
            
            particle['phase'] += particle['pulse_speed'] * self.dt
            base_alpha = 30 + 25 * (0.5 + 0.5 * math.sin(particle['phase']))
            particle['alpha'] = base_alpha

    def update_data_blips(self):
        self.blip_timer += self.dt
        if self.blip_timer > 0.8:
            self.blip_timer = 0
            blip = {
                'angle': np.random.uniform(0, 360),
                'radius': np.random.choice([120, 160, 200, 240, 280, 320, 360, 400]),
                'life': 0,
                'max_life': 2,
                'speed': np.random.uniform(15, 30)
            }
            self.data_blips.append(blip)
            
        for blip in self.data_blips[:]:
            blip['life'] += self.dt
            blip['angle'] += blip['speed'] * self.dt
            if blip['life'] > blip['max_life']:
                self.data_blips.remove(blip)

    def update_spark_trails(self):
        self.spark_timer += self.dt
        if self.spark_timer > 3 or (np.random.random() < 0.3 and self.spark_timer > 0.3):
            self.spark_timer = 0
            spark = {
                'start_angle': np.random.uniform(0, 360),
                'radius': np.random.choice([180, 220, 260, 300, 340, 380]),
                'life': 0,
                'max_life': 1.5,
                'speed': np.random.uniform(60, 120)
            }
            self.spark_trails.append(spark)
            
        for spark in self.spark_trails[:]:
            spark['life'] += self.dt
            spark['start_angle'] += spark['speed'] * self.dt
            if spark['life'] > spark['max_life']:
                self.spark_trails.remove(spark)

    def mouseMoveEvent(self, event):
        self.mouse_pos = QPointF(event.x(), event.y())
        center = QPointF(self.width() // 2, self.height() // 2)
        distance = math.sqrt((self.mouse_pos.x() - center.x())**2 + (self.mouse_pos.y() - center.y())**2)
        max_distance = 400
        if distance < max_distance:
            self.mouse_influence = min(1, (max_distance - distance) / max_distance)
        else:
            self.mouse_influence = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.trigger_special_effect()

    def trigger_special_effect(self):
        self.click_animation_group.stop()
        self.click_animation_group.start()
        self.create_energy_ring()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
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

    def draw_enhanced_background(self, painter):
        center = QPointF(self.width() // 2, self.height() // 2)
        max_radius = max(self.width(), self.height())
        gradient = QRadialGradient(center, max_radius)
        
        gradient.setColorAt(0, QColor(0, 8, 15, 255))
        gradient.setColorAt(0.7, QColor(0, 4, 8, 255))
        gradient.setColorAt(1, QColor(0, 0, 0, 255))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    def draw_particle_system(self, painter):
        painter.setPen(Qt.NoPen)
        for particle in self.particles:
            alpha = int((particle['alpha'] * (1 + 0.3 * self.mouse_influence)))
            size = particle['size'] * (1 + 0.5 * self.mouse_influence)
            
            for i in range(3):
                layer_size = size * (1 + i * 0.8)
                layer_alpha = alpha // (i + 1)
                glow_color = QColor(0, 255, 255, layer_alpha)
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(QPointF(particle['x'], particle['y']), layer_size, layer_size)

    def draw_enhanced_grid(self, painter):
        # Simplified grid drawing
        grid_offset = int(self.time * 5) % 60
        grid_color = QColor(0, 60, 80, int(20 + 10 * self.mouse_influence))
        painter.setPen(QPen(grid_color, 1))
        
        grid_size = 60
        # Draw verticals
        for x in range(-grid_offset, self.width() + grid_size, grid_size):
            painter.drawLine(x, 0, x, self.height())
        # Draw horizontals
        for y in range(-grid_offset, self.height() + grid_size, grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_data_blips(self, painter, center):
        painter.setPen(Qt.NoPen)
        for blip in self.data_blips:
            angle_rad = math.radians(blip['angle'])
            x = center.x() + blip['radius'] * math.cos(angle_rad)
            y = center.y() + blip['radius'] * math.sin(angle_rad)
            
            life_progress = blip['life'] / blip['max_life']
            alpha = int(255 * (1 - life_progress) * 0.8)
            size = 2 + 3 * (1 - life_progress)
            
            painter.setBrush(QBrush(QColor(0, 255, 255, alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)

    def draw_neural_rings(self, painter, center):
        breathing = 0.5 + 0.5 * math.sin(self.breathing_phase)
        
        rings = [
            {'radius': 280 + breathing * 3, 'width': 1.5, 'alpha': 55, 'segments': 14, 'rotation': self.ring_rotations[3], 'glow_layers': 2},
            {'radius': 240 + breathing * 2, 'width': 1.5, 'alpha': 50, 'segments': 16, 'rotation': self.ring_rotations[4], 'glow_layers': 2},
            {'radius': 200 + breathing * 2, 'width': 1, 'alpha': 45, 'segments': 18, 'rotation': self.ring_rotations[5], 'glow_layers': 2},
            {'radius': 160 + breathing * 1, 'width': 1, 'alpha': 40, 'segments': 20, 'rotation': self.ring_rotations[6], 'glow_layers': 2},
            {'radius': 120 + breathing * 1, 'width': 1, 'alpha': 35, 'segments': 22, 'rotation': self.ring_rotations[7], 'glow_layers': 2},
            {'radius': 80 + breathing * 1, 'width': 1, 'alpha': 30, 'segments': 0, 'rotation': self.ring_rotations[8], 'glow_layers': 2},
        ]
        
        for ring in rings:
            self.draw_neural_ring(painter, center, ring)

    def draw_neural_ring(self, painter, center, ring_config):
        radius = ring_config['radius']
        width = ring_config['width']
        alpha = ring_config['alpha']
        segments = ring_config['segments']
        rotation = ring_config['rotation']
        
        enhanced_alpha = int(alpha * (1 + 0.4 * self.mouse_influence))
        
        # Draw logic for segmented rings or solid rings
        painter.save()
        painter.translate(center)
        painter.rotate(rotation)
        
        painter.setPen(QPen(QColor(0, 255, 255, enhanced_alpha), width))
        painter.setBrush(Qt.NoBrush)
        
        if segments == 0:
            painter.drawEllipse(QPointF(0, 0), radius, radius)
        else:
            segment_angle = 360 / segments
            arc_length = segment_angle * 0.7
            for i in range(segments):
                start_angle = i * segment_angle
                # Highlight every 3rd segment
                seg_alpha = enhanced_alpha if i % 3 != 0 else int(enhanced_alpha * 1.3)
                painter.setPen(QPen(QColor(0, 255, 255, seg_alpha), width))
                painter.drawArc(QRectF(-radius, -radius, radius*2, radius*2), int(start_angle * 16), int(arc_length * 16))
                
        painter.restore()

    def draw_spark_trails(self, painter, center):
        painter.setPen(Qt.NoPen)
        for spark in self.spark_trails:
            life_progress = spark['life'] / spark['max_life']
            alpha = int(255 * (1 - life_progress) * 0.6)
            angle_rad = math.radians(spark['start_angle'])
            x = center.x() + spark['radius'] * math.cos(angle_rad)
            y = center.y() + spark['radius'] * math.sin(angle_rad)
            
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            painter.drawEllipse(QPointF(x, y), 2, 2)

    def draw_enhanced_center_core(self, painter, center):
        painter.save()
        painter.translate(self.vibration_offset)
        
        pulse = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(self.pulse_phase))
        current_radius = 50 * self.pulse_scale
        
        self.draw_energy_rings(painter, center)
        
        # Core Gradient
        core_gradient = QRadialGradient(center, current_radius * 0.5)
        core_gradient.setColorAt(0, QColor(0, 255, 255, int(120 * pulse)))
        core_gradient.setColorAt(0.3, QColor(150, 255, 255, int(100 * pulse)))
        core_gradient.setColorAt(0.7, QColor(0, 255, 255, int(80 * pulse)))
        core_gradient.setColorAt(1, QColor(0, 255, 255, int(40 * pulse)))
        
        painter.setBrush(QBrush(core_gradient))
        painter.setPen(QPen(QColor(0, 180, 255), 1))
        painter.drawEllipse(center, current_radius * 0.5, current_radius * 0.5)
        
        self.draw_center_text(painter, center, pulse)
        self.draw_dashed_arcs(painter, center, current_radius)
        
        painter.restore()

    def draw_energy_rings(self, painter, center):
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

    def draw_dashed_arcs(self, painter, center, radius):
        painter.save()
        painter.setBrush(Qt.NoBrush)
        dash_pen = QPen(QColor(0, 180, 255, 100), 1)
        dash_pen.setDashPattern([3, 3])
        painter.setPen(dash_pen)
        
        painter.drawEllipse(center, radius + 40, radius + 40)
        
        # Rotating Points
        shimmer_phase = 0.5 + 0.5 * math.sin(self.time * 2)
        for angle in range(0, 360, 30):
            x = center.x() + (radius + 30) * math.cos(math.radians(angle))
            y = center.y() + (radius + 30) * math.sin(math.radians(angle))
            
            alpha = int(255 * (0.7 + 0.3 * shimmer_phase))
            painter.setPen(QPen(QColor(0, 255, 255, alpha), 2))
            painter.drawPoint(QPointF(x, y))
            
        painter.restore()

    def draw_center_text(self, painter, center, pulse):
        font = QFont("Arial", 20, QFont.Bold)
        painter.setFont(font)
        
        text_alpha = int(120 + 30 * pulse)
        text = "NOVA"
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        
        text_x = center.x() - text_width // 2
        text_y = center.y() + text_height // 4
        
        # Glow effect for text
        glow_layers = [
            (3, QColor(0, 255, 255, int(30 * pulse))),
            (2, QColor(0, 255, 255, int(60 * pulse))),
            (1, QColor(0, 255, 255, int(90 * pulse)))
        ]
        
        for glow_size, glow_color in glow_layers:
            painter.setPen(QPen(glow_color, glow_size))
            painter.drawText(int(text_x), int(text_y), text)
            
        painter.setPen(QPen(QColor(0, 255, 255, text_alpha)))
        painter.drawText(int(text_x), int(text_y), text)

    def draw_special_effects(self, painter, center):
        # Simple effect drawing
        effect_progress = self.special_effect_timer / 2
        if effect_progress < 0.5:
            ring_radius = 400 * effect_progress * 2
            ring_alpha = int(100 * (1 - effect_progress * 2) * 0.9)
            
            gradient = QRadialGradient(center, ring_radius + 20)
            gradient.setColorAt(0, QColor(0, 255, 255, 0))
            gradient.setColorAt(0.9, QColor(0, 255, 255, ring_alpha))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, ring_radius + 20, ring_radius + 20)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.trigger_special_effect()
        super().keyPressEvent(event)


class NOVAInterfaceWindow(QMainWindow):
    """Main window for NOVA AI Interface"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA AI Neural Core Interface")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black;")
        
        self.nova_widget = NOVAInterfaceWidget()
        self.setCentralWidget(self.nova_widget)
        
        self.assistant = None
        self.agent_thread = None
        self.agent_should_stop = False
        self.agent_loop = None
        
        self.setup_tts_callbacks()
        self._start_agent_background()
        
        self._effect_callback = None

    def setup_tts_callbacks(self):
        # Placeholder for connecting TTS events
        pass

    def _start_agent_background(self):
        def run_agent():
            print("🟢 Starting agent background thread...")
            try:
                from livekit.agents.cli import run_app
                from livekit.agents import WorkerOptions
                print("🟢 Starting LiveKit worker...")
                run_app(WorkerOptions(entrypoint_fnc=entrypoint))
            except Exception as e:
                print(f"✗ Agent thread error: {e}")
                traceback.print_exc()
            print("🔴 Agent thread stopped")

        self.agent_thread = threading.Thread(target=run_agent, daemon=True)
        self.agent_thread.start()
        print("🟢 Agent thread started")

    def closeEvent(self, event):
        print("Shutting down agent...")
        if self.agent_loop and self.agent_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.agent_loop.shutdown_asyncgens(), self.agent_loop)
            self.agent_loop.call_soon_threadsafe(self.agent_loop.stop)
        
        if self.agent_thread and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=2)
            
        super().closeEvent(event)

    def keyPressEvent(self, event):
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


def start_nova_interface():
    if not NOVA_AVAILABLE:
        # show_error_dialog logic here
        return False
        
    app = QApplication(sys.argv)
    app.setApplicationName("NOVA AI Neural Interface")
    app.setApplicationVersion("1.1")
    
    # wait_for_internet logic
    
    # firebase logic
    
    # activation logic
    
    window = NOVAInterfaceWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_nova_interface()
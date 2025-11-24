# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: nova_gui.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import asyncio
from livekit import agents
import contextlib
import cv2
import firebase_admin
import json
import logging
import math
import numpy as np
import os
import pickle
import platform
import psutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import find_dotenv, load_dotenv, set_key
from firebase_admin import credentials, db
from livekit import rtc
from livekit.agents import AgentServer, WorkerOptions, cli as agents_cli
from livekit.agents.utils import images
from livekit.rtc import VideoBufferType
from PyQt5.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QFontMetrics,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from Nova_Voice_Assistant import Assistant, entrypoint

# Conditional imports for face recognition


class RightPanel(QWidget):
    """Right-side panel for camera, time, and network status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: transparent;")
        self.camera_available = False
        self.camera = None
        self.assistant = None
        self._video_source = None
        self._frame_counter = 0
        self._last_frame_sent = 0
        self._min_frame_interval = 1 / 20  # 20 FPS

        self.init_ui()
        self.init_camera()

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.update_network_info)
        self.network_timer.start(3000)

        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_feed)
        self.camera_timer.start(50)  # ~20 FPS

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)

        time_label = QLabel("TEMPORAL SYNCHRONIZATION")
        time_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """
        )
        layout.addWidget(time_label)
        self.time_widget = self.create_time_card()
        layout.addWidget(self.time_widget)

        network_label = QLabel("NETWORK INTERFACE")
        network_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """
        )
        layout.addWidget(network_label)
        self.network_ip_widget = self.create_network_card("IP ADDRESS", "192.168.1.100")
        self.network_speed_widget = self.create_network_card(
            "BANDWIDTH", "↑ 12.4 Mbps / ↓ 45.8 Mbps"
        )
        self.network_status_widget = self.create_network_card(
            "CONNECTION", "WiFi (NOVA_5G) - 92%"
        )
        layout.addWidget(self.network_ip_widget)
        layout.addWidget(self.network_speed_widget)
        layout.addWidget(self.network_status_widget)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        camera_label = QLabel("VISUAL INPUT")
        camera_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """
        )
        layout.addWidget(camera_label)
        self.camera_widget = self.create_camera_widget()
        layout.addWidget(self.camera_widget)

        self.setLayout(layout)

    def init_camera(self):
        """Initialize camera with multiple attempts."""
        if self.camera_available:
            return
        for i in range(3):
            try:
                self.camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        self.camera_available = True
                        print(f"✅ Camera initialized successfully on index {i}")
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.camera.set(cv2.CAP_PROP_FPS, 20)
                        self.show_no_camera_message(show=False)
                        return
                    self.camera.release()
            except Exception as e:
                print(f"❌ Camera index {i} failed: {e}")
        
        print("❌ No working camera found on indices 0-2")
        self.camera_available = False
        self.show_no_camera_message(show=True)


    def set_video_track(self, video_source):
        """Set the video track to send frames to."""
        self._video_source = video_source
        print("✅ Video track set in RightPanel")

    async def send_frame_to_assistant(self, frame):
        """Send video frame to assistant for processing."""
        if not hasattr(self, "assistant") or not self.assistant:
            return
        try:
            rgba_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
            height, width, _ = rgba_frame.shape
            video_frame = rtc.VideoFrame(
                width, height, VideoBufferType.RGBA, rgba_frame.tobytes()
            )
            if asyncio.iscoroutinefunction(self.assistant.process_visual_frame):
                await self.assistant.process_visual_frame(video_frame)
            else:
                self.assistant.process_visual_frame(video_frame)
        except Exception as e:
            print(f"Frame sending error: {e}")

    def create_time_card(self):
        """Create the time display card."""
        card = QWidget()
        card.setStyleSheet(
            """
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """
        )
        card.setFixedHeight(100)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 28px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        """
        )
        self.date_label = QLabel()
        self.date_label.setStyleSheet(
            """
            color: #00aaaa;
            font-size: 14px;
            qproperty-alignment: AlignCenter;
        """
        )
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        card.setLayout(layout)
        self.update_time()
        return card

    def create_network_card(self, title, value):
        """Create a network info card."""
        card = QWidget()
        card.setStyleSheet(
            """
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """
        )
        card.setFixedHeight(70)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            color: #00aaaa;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """
        )
        value_label = QLabel(value)
        value_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
        """
        )
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_camera_widget(self):
        """Create the camera display widget."""
        widget = QWidget()
        widget.setStyleSheet(
            """
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """
        )
        widget.setFixedHeight(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet(
            """
            background-color: black;
            qproperty-alignment: AlignCenter;
        """
        )
        layout.addWidget(self.camera_label)
        widget.setLayout(layout)
        return widget

    def update_time(self):
        """Update the time display."""
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%A, %d %B %Y"))

    def update_network_info(self):
        """Update network information with live data when possible."""
        ip_address = self.get_local_ip() or "Unavailable"
        wifi_details = self.get_wifi_details() or {}
        ssid = wifi_details.get("ssid") or "Wi-Fi"
        signal_display = wifi_details.get("signal")

        upload_speed = f"{np.random.uniform(5.0, 15.0):.1f} Mbps"
        download_speed = f"{np.random.uniform(30.0, 60.0):.1f} Mbps"

        status_text = ssid
        if signal_display:
            status_text = f"{ssid} - {signal_display}"

        self.network_ip_widget.layout().itemAt(1).widget().setText(ip_address)
        self.network_speed_widget.layout().itemAt(1).widget().setText(
            f"↑ {upload_speed} / ↓ {download_speed}"
        )
        self.network_status_widget.layout().itemAt(1).widget().setText(status_text)

    def get_local_ip(self):
        """Get local IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return None

    def get_wifi_details(self):
        """Retrieve Wi-Fi SSID and signal strength on supported platforms."""
        if platform.system() != "Windows":
            return None

        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

        ssid = None
        signal = None
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line:
                continue

            key, value = [part.strip() for part in line.split(":", 1)]
            key_lower = key.lower()

            if key_lower == "ssid":
                # Skip BSSID entries which also include "SSID" substring
                if "bssid" in line.lower():
                    continue
                ssid = value
            elif key_lower == "signal":
                signal = value

        if not ssid and not signal:
            return None

        return {"ssid": ssid, "signal": signal}

    def update_camera_feed(self):
        """Update the camera feed display with robust error handling."""
        if not self.camera_available:
            self.init_camera()
            if not self.camera_available:
                self.show_no_camera_message(show=True)
                return

        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                print("⚠️ Failed to read frame from camera")
                self.camera_available = False
                if self.camera:
                    self.camera.release()
                self.show_no_camera_message(show=True)
                return

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (320, 240)) # Adjusted for aspect ratio
            self.display_camera_frame(frame_resized)
            self.send_frame_to_livekit(frame)

        except Exception as e:
            print(f"❌ Camera feed update error: {e}")
            self.camera_available = False
            if self.camera:
                self.camera.release()
            self.show_no_camera_message(show=True)

    def send_frame_to_livekit(self, frame):
        """Send frame to LiveKit video source."""
        current_time = time.time()
        if (current_time - self._last_frame_sent) < self._min_frame_interval:
            return
        self._last_frame_sent = current_time

        if self._video_source:
            try:
                rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                height, width, _ = rgba_frame.shape
                video_frame = rtc.VideoFrame(
                    width, height, VideoBufferType.RGBA, rgba_frame.tobytes()
                )
                self._video_source.capture_frame(video_frame)
                self._frame_counter += 1
                if self._frame_counter % 60 == 0: # Log every 60 frames
                    print(f"✅ Frame {self._frame_counter} sent to LiveKit: {width}x{height}")
            except Exception as e:
                print(f"❌ Video frame sending error: {e}")

    def display_camera_frame(self, frame):
        """Display frame in the GUI with border."""
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Create a new pixmap to draw on with rounded corners
            border_pixmap = QPixmap(pixmap.size())
            border_pixmap.fill(Qt.transparent)
            
            painter = QPainter(border_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            path = QPainterPath()
            path.addRoundedRect(QRectF(border_pixmap.rect()), 8, 8)
            painter.setClipPath(path)
            
            painter.drawPixmap(0, 0, pixmap)
            
            border_pen = QPen(QColor(0, 180, 255, 150), 2)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path) # Draw the rounded border
            
            painter.end()
            
            self.camera_label.setPixmap(border_pixmap)
        except Exception as e:
            print(f"❌ Display frame error: {e}")

    def show_no_camera_message(self, show=True):
        """Show or hide the 'no camera' message."""
        if not hasattr(self, "_no_camera_label"):
            self._no_camera_label = QLabel(
                "NO CAMERA DETECTED\n\n"
                "• Check connection\n"
                "• Check permissions\n"
                "• Check other apps"
            )
            self._no_camera_label.setStyleSheet(
                """
                color: #ff5555;
                font-size: 12px;
                font-weight: bold;
                background-color: black;
            """
            )
            self._no_camera_label.setAlignment(Qt.AlignCenter)
            
            if self.camera_label.layout() is None:
                layout = QVBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                self.camera_label.setLayout(layout)
            
            self.camera_label.layout().addWidget(self._no_camera_label)

        self._no_camera_label.setVisible(show)


    def paintEvent(self, event):
        """Custom painting for the glassy background effect."""
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
        """Clean up camera resources."""
        if self.camera_available and self.camera:
            self.camera.release()
        super().closeEvent(event)

class SystemStatsPanel(QWidget):
    """Refined left-side panel with professional futuristic design."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: transparent;")
        self.cpu_usage = 0
        self.ram_usage = 0
        self.ram_total = psutil.virtual_memory().total / (1024**3)
        (
            self.storage_used,
            self.storage_total,
            self.storage_drives,
        ) = self.calculate_storage_stats()
        self.cpu_temp = 0
        self.power_source = "AC"
        self.battery_level = 100
        self.weather_city = "NEURAL CITY"
        self.weather_temp = "24°C"
        self.weather_status = "CLEAR"
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_system_data)
        self.update_timer.start(2000)
        self.update_system_data()

    def init_ui(self):
        """Initialize the refined user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(20)
        sys_info_label = QLabel("SYSTEM STATUS")
        sys_info_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """
        )
        layout.addWidget(sys_info_label)

        self.cpu_widget = self.create_stat_card(
            "CPU UTILIZATION", f"{self.cpu_usage}%", self.cpu_usage, "circular"
        )
        layout.addWidget(self.cpu_widget)
        self.ram_widget = self.create_stat_card(
            "MEMORY ALLOCATION",
            f"{self.ram_usage:.1f} / {self.ram_total:.1f} GB",
            (self.ram_usage / self.ram_total) * 100,
            "linear",
        )
        layout.addWidget(self.ram_widget)
        self.storage_widget = self.create_stat_card(
            "STORAGE CAPACITY",
            self.get_storage_display_text(),
            (self.storage_used / self.storage_total) * 100,
            "linear",
        )
        self.storage_widget.setToolTip(self.get_storage_tooltip())
        layout.addWidget(self.storage_widget)
        self.temp_widget = self.create_stat_card(
            "CORE TEMPERATURE", f"{self.cpu_temp}°C", self.cpu_temp, "temp"
        )
        layout.addWidget(self.temp_widget)

        power_text = (
            f"BATTERY: {self.battery_level}%"
            if self.power_source == "Battery"
            else "POWER: AC"
        )
        self.power_widget = self.create_stat_card(
            "POWER STATUS",
            power_text,
            self.battery_level if self.power_source == "Battery" else 100,
            "linear",
        )
        layout.addWidget(self.power_widget)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        weather_label = QLabel("ENVIRONMENT")
        weather_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 1px solid #003333;
            letter-spacing: 1px;
        """
        )
        layout.addWidget(weather_label)
        self.weather_widget = self.create_weather_card()
        layout.addWidget(self.weather_widget)

        self.setLayout(layout)

    def calculate_storage_stats(self):
        """Aggregate storage usage across mounted drives."""
        total_used = 0
        total_size = 0
        drives = []
        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception:
            partitions = []

        for part in partitions:
            opts = part.opts.lower() if part.opts else ""
            if platform.system() == "Windows" and "cdrom" in opts:
                continue
            if not part.mountpoint:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, FileNotFoundError):
                continue
            if usage.total == 0:
                continue

            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            drives.append(
                {
                    "label": self._format_drive_label(part.mountpoint),
                    "used": used_gb,
                    "total": total_gb,
                }
            )
            total_used += usage.used
            total_size += usage.total

        if not drives:
            usage = psutil.disk_usage("/")
            drives.append(
                {
                    "label": self._format_drive_label("/"),
                    "used": usage.used / (1024**3),
                    "total": usage.total / (1024**3),
                }
            )
            total_used = usage.used
            total_size = usage.total

        return total_used / (1024**3), total_size / (1024**3), drives

    def _format_drive_label(self, mountpoint):
        """Normalize mount labels for display."""
        if platform.system() == "Windows":
            drive = Path(mountpoint).drive.upper()
            return drive if drive else mountpoint
        return mountpoint or "/"

    def get_storage_display_text(self):
        """Build compact label text shown on the card."""
        drive_count = len(getattr(self, "storage_drives", []))
        base_text = f"{self.storage_used:.0f} / {self.storage_total:.0f} GB"
        if drive_count > 1:
            return f"Total {base_text} ({drive_count} drives)"
        return base_text

    def get_storage_tooltip(self):
        """Provide per-drive details in a tooltip."""
        if not getattr(self, "storage_drives", None):
            return "Storage details unavailable"
        lines = [
            f"{drive['label']}: {drive['used']:.0f} / {drive['total']:.0f} GB"
            for drive in self.storage_drives
        ]
        return "\n".join(lines)

    def create_stat_card(self, title, value, percentage, style):
        """Create a refined stat card with the specified style."""
        card = QWidget()
        card.setStyleSheet(
            """
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """
        )
        card.setFixedHeight(90)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            color: #00aaaa;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """
        )
        value_label = QLabel(value)
        value_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 16px;
            font-weight: bold;
        """
        )
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
        """Create the refined weather display card."""
        card = QWidget()
        card.setStyleSheet(
            """
            background-color: rgba(0, 20, 40, 120);
            border-radius: 4px;
            border: 1px solid rgba(0, 80, 120, 80);
        """
        )
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
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        city_label = QLabel(self.weather_city)
        city_label.setStyleSheet(
            """
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """
        )
        temp_label = QLabel(self.weather_temp)
        temp_label.setStyleSheet(
            """
            color: #ffffff;
            font-size: 22px;
            font-weight: bold;
        """
        )
        status_label = QLabel(self.weather_status)
        status_label.setStyleSheet(
            """
            color: #00aaaa;
            font-size: 12px;
        """
        )
        info_layout.addWidget(city_label)
        info_layout.addWidget(temp_label)
        info_layout.addWidget(status_label)
        info_widget.setLayout(info_layout)

        layout.addWidget(icon_widget)
        layout.addWidget(info_widget)
        card.setLayout(layout)
        return card

    def update_system_data(self):
        """Update with real system data."""
        self.cpu_usage = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        self.ram_usage = mem.used / (1024**3)
        (
            self.storage_used,
            self.storage_total,
            self.storage_drives,
        ) = self.calculate_storage_stats()
        
        # CPU Temp (platform dependent)
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                self.cpu_temp = temps["coretemp"][0].current
        
        # Power status
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                self.battery_level = battery.percent
                self.power_source = "Battery" if not battery.power_plugged else "AC"

        # Mock weather update
        if np.random.random() < 0.2:
            weather_options = [
                ("CLEAR", "24°C"),
                ("CLOUDY", "21°C"),
                ("RAIN", "18°C"),
                ("THUNDER", "20°C"),
            ]
            self.weather_status, self.weather_temp = weather_options[
                np.random.randint(0, len(weather_options))
            ]
            self.weather_icon.set_weather_type(self.weather_status)

        self.update_widgets()

    def update_widgets(self):
        """Update all widgets with current data."""
        self.cpu_widget.layout().itemAt(1).widget().setText(f"{self.cpu_usage:.1f}%")
        self.cpu_widget.layout().itemAt(2).widget().setValue(self.cpu_usage)

        self.ram_widget.layout().itemAt(1).widget().setText(
            f"{self.ram_usage:.1f} / {self.ram_total:.1f} GB"
        )
        self.ram_widget.layout().itemAt(2).widget().setValue(
            (self.ram_usage / self.ram_total) * 100
        )

        self.storage_widget.layout().itemAt(1).widget().setText(
            self.get_storage_display_text()
        )
        self.storage_widget.layout().itemAt(2).widget().setValue(
            (self.storage_used / self.storage_total) * 100
        )
        self.storage_widget.setToolTip(self.get_storage_tooltip())

        self.temp_widget.layout().itemAt(1).widget().setText(f"{self.cpu_temp:.0f}°C")
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

    def paintEvent(self, event):
        """Custom painting for the glassy background effect."""
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
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class CircularProgressBar(QWidget):
    """Refined circular progress bar with smooth animation."""

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self._animation_value = value
        self.setFixedSize(100, 30)
        self.setStyleSheet("background-color: transparent;")
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value != self._value:
            self._value = value
            self.animation.stop()
            self.animation.setStartValue(self._animation_value)
            self.animation.setEndValue(value)
            self.animation.start()

    @pyqtProperty(float)
    def animationValue(self):
        return self._animation_value

    @animationValue.setter
    def animationValue(self, value):
        self._animation_value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(10, 5, 80, 20)
        
        # Background arc
        pen = QPen(QColor(0, 60, 80, 150), 2)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 16 * 360)

        # Foreground arc
        progress = self._animation_value / 100.0
        pen = QPen(QColor(0, 255, 255), 2)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -int(progress * 360 * 16))

        # Indicator dot
        angle_rad = math.radians(90 - progress * 360)
        center_x = rect.center().x()
        center_y = rect.center().y()
        radius_x = rect.width() / 2
        radius_y = rect.height() / 2
        
        end_x = center_x + radius_x * math.cos(angle_rad)
        end_y = center_y - radius_y * math.sin(angle_rad)
        
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.setPen(QPen(QColor(0, 100, 150), 1))
        painter.drawEllipse(QPointF(end_x, end_y), 3, 3)


class LinearProgressBar(QWidget):
    """Refined linear progress bar with smooth animation."""

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self._animation_value = value
        self.setFixedHeight(12)
        self.setStyleSheet("background-color: transparent;")
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setValue(self, value):
        if value != self._value:
            self._value = value
            self.animation.stop()
            self.animation.setStartValue(self._animation_value)
            self.animation.setEndValue(value)
            self.animation.start()

    @pyqtProperty(float)
    def animationValue(self):
        return self._animation_value

    @animationValue.setter
    def animationValue(self, value):
        self._animation_value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_rect = QRectF(0, 4, self.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 60, 80, 150)))
        painter.drawRoundedRect(bg_rect, 2, 2)

        progress_width = self.width() * (self._animation_value / 100.0)
        progress_rect = QRectF(0, 4, progress_width, 4)
        
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(0, 180, 255))
        gradient.setColorAt(1, QColor(0, 255, 255))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)

        glow_rect = QRectF(0, 3, progress_width, 6)
        painter.setPen(QPen(QColor(0, 255, 255, 60), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(glow_rect, 3, 3)


class TemperatureBar(LinearProgressBar):
    """Special progress bar for temperature with color coding."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_rect = QRectF(0, 4, self.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 60, 80, 150)))
        painter.drawRoundedRect(bg_rect, 2, 2)

        progress_width = self.width() * min(100, self._animation_value) / 100.0
        progress_rect = QRectF(0, 4, progress_width, 4)
        
        gradient = QLinearGradient(0, 0, self.width(), 0) # Gradient over full width
        gradient.setColorAt(0.0, QColor(0, 180, 255))  # Cool
        gradient.setColorAt(0.4, QColor(0, 255, 180))  # Mild
        gradient.setColorAt(0.7, QColor(255, 255, 0))  # Warm
        gradient.setColorAt(1.0, QColor(255, 60, 0))   # Hot
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(progress_rect, 2, 2)

        glow_rect = QRectF(0, 3, progress_width, 6)
        # Determine glow color based on temperature
        temp_ratio = self._animation_value / 100.0
        glow_color = QColor(0, 255, 255, 60) # Default
        if temp_ratio > 0.7:
            glow_color = QColor(255, 100, 0, 80)
        elif temp_ratio > 0.4:
            glow_color = QColor(255, 255, 0, 70)

        painter.setPen(QPen(glow_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(glow_rect, 3, 3)


class WeatherIcon(QWidget):
    """Minimal vector-style weather icon."""

    def __init__(self, weather_type="CLEAR", parent=None):
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
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        center = QPointF(20, 20)

        if self.weather_type == "CLEAR":
            painter.setBrush(QBrush(QColor(255, 255, 0, 150)))
            painter.drawEllipse(center, 8, 8)
            for i in range(0, 360, 45):
                angle = math.radians(i)
                start_x = center.x() + 10 * math.cos(angle)
                start_y = center.y() + 10 * math.sin(angle)
                end_x = center.x() + 14 * math.cos(angle)
                end_y = center.y() + 14 * math.sin(angle)
                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
        elif self.weather_type == "CLOUDY":
            self.draw_cloud(painter, QColor(200, 200, 255, 150))
        elif self.weather_type == "RAIN":
            self.draw_cloud(painter, QColor(150, 150, 255, 150))
            painter.setPen(QPen(QColor(0, 150, 255), 1.5))
            for i in range(3):
                painter.drawLine(15 + i * 5, 28, 13 + i * 5, 34)
        elif self.weather_type == "THUNDER":
            self.draw_cloud(painter, QColor(100, 100, 200, 150))
            bolt = QPolygonF(
                [
                    QPointF(22, 25),
                    QPointF(18, 30),
                    QPointF(21, 30),
                    QPointF(17, 35),
                ]
            )
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(bolt)

    def draw_cloud(self, painter, color):
        path = QPainterPath()
        path.moveTo(30, 25)
        path.arcTo(15, 15, 15, 10, 0, 180)
        path.arcTo(10, 18, 10, 7, 90, -180)
        path.arcTo(15, 10, 20, 15, 180, 180)
        path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 255, 255), 1.5))
        painter.drawPath(path)

class NOVAInterfaceWidget(QWidget):
    """The central animation widget for the NOVA interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 800)
        self.setStyleSheet("background-color: transparent;")
        self.setMouseTracking(True)

        self.mouse_pos = QPointF(self.width() / 2, self.height() / 2)
        self.mouse_influence = 0.0
        self.time = 0.0
        self.dt = 1 / 60.0  # 60 FPS
        self.ring_rotations = [np.random.uniform(0, 360) for _ in range(9)]
        self.pulse_phase = 0.0
        self.pulse_speed = 1.2
        self.breathing_phase = 0.0
        self.particles = []
        self.data_blips = []
        self.blip_timer = 0.0
        self.spark_trails = []
        self.spark_timer = 0.0
        self.energy_rings = []

        self.init_particles()
        self.setup_click_animation()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(int(self.dt * 1000))

    def init_particles(self):
        """Initialize background particle system."""
        for _ in range(100):
            self.particles.append(
                {
                    "pos": QPointF(
                        np.random.uniform(0, self.width()),
                        np.random.uniform(0, self.height()),
                    ),
                    "vel": QPointF(
                        np.random.uniform(-15, 15), np.random.uniform(-15, 15)
                    ),
                    "size": np.random.uniform(0.5, 2.0),
                    "alpha": np.random.uniform(20, 80),
                    "phase": np.random.uniform(0, 2 * math.pi),
                    "pulse_speed": np.random.uniform(0.5, 2.0),
                }
            )

    def setup_click_animation(self):
        """Setup all animations for the click effect."""
        self._vibration_offset = QPointF(0, 0)
        self._pulse_scale = 1.0

        self.vibration_anim = QPropertyAnimation(self, b"vibration_offset")
        self.vibration_anim.setDuration(500)
        self.vibration_anim.setEasingCurve(QEasingCurve.OutElastic)
        
        self.pulse_anim = QPropertyAnimation(self, b"pulse_scale")
        self.pulse_anim.setDuration(700)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setKeyValueAt(0.3, 1.15)
        self.pulse_anim.setKeyValueAt(0.6, 0.95)
        self.pulse_anim.setEndValue(1.0)

        self.click_animation_group = QParallelAnimationGroup(self)
        self.click_animation_group.addAnimation(self.vibration_anim)
        self.click_animation_group.addAnimation(self.pulse_anim)

    @pyqtProperty(QPointF)
    def vibration_offset(self):
        return self._vibration_offset

    @vibration_offset.setter
    def vibration_offset(self, offset):
        self._vibration_offset = offset
        self.update()

    @pyqtProperty(float)
    def pulse_scale(self):
        return self._pulse_scale

    @pulse_scale.setter
    def pulse_scale(self, scale):
        self._pulse_scale = scale
        self.update()

    def create_energy_ring(self):
        """Create an expanding energy ring effect."""
        self.energy_rings.append(
            {
                "life": 0.0,
                "max_life": 0.7,
            }
        )

    def update_energy_rings(self):
        """Update and animate all active energy rings."""
        for ring in self.energy_rings[:]:
            ring["life"] += self.dt
            if ring["life"] >= ring["max_life"]:
                self.energy_rings.remove(ring)
        
    def update_animation(self):
        """Update all animation states."""
        self.time += self.dt

        for i in range(len(self.ring_rotations)):
            direction = 1 if (i % 2 == 0) else -1
            speed = (i + 1) * 2.0
            self.ring_rotations[i] = (self.ring_rotations[i] + direction * speed * self.dt * 10) % 360

        self.pulse_phase += self.pulse_speed * self.dt
        self.breathing_phase += 0.8 * self.dt

        self.update_particles()
        self.update_data_blips()
        self.update_spark_trails()
        self.update_energy_rings()

        self.mouse_influence *= 0.95
        self.update()

    def update_particles(self):
        """Update particle system."""
        for p in self.particles:
            p["pos"] += p["vel"] * self.dt
            
            # Wrap around screen
            if p["pos"].x() < 0: p["pos"].setX(self.width())
            if p["pos"].x() > self.width(): p["pos"].setX(0)
            if p["pos"].y() < 0: p["pos"].setY(self.height())
            if p["pos"].y() > self.height(): p["pos"].setY(0)

            p["phase"] += p["pulse_speed"] * self.dt
            p["alpha"] = 30 + 50 * abs(math.sin(p["phase"]))

    def update_data_blips(self):
        """Update data blips around rings."""
        self.blip_timer += self.dt
        if self.blip_timer > 0.1: # More frequent blips
            self.blip_timer = 0.0
            if np.random.random() < 0.4:
                self.data_blips.append(
                    {
                        "angle": np.random.uniform(0, 360),
                        "radius": np.random.choice([120, 160, 200, 240, 280, 320, 360, 400]),
                        "life": 0.0,
                        "max_life": np.random.uniform(1.0, 2.5),
                        "speed": np.random.uniform(15, 30) * np.random.choice([-1, 1]),
                    }
                )
        for blip in self.data_blips[:]:
            blip["life"] += self.dt
            blip["angle"] = (blip["angle"] + blip["speed"] * self.dt) % 360
            if blip["life"] > blip["max_life"]:
                self.data_blips.remove(blip)

    def update_spark_trails(self):
        """Update spark trail effects."""
        self.spark_timer += self.dt
        if self.spark_timer > 0.5 and np.random.random() < 0.1:
            self.spark_timer = 0.0
            self.spark_trails.append(
                {
                    "start_angle": np.random.uniform(0, 360),
                    "radius": np.random.choice([180, 220, 260, 300, 340, 380]),
                    "life": 0.0,
                    "max_life": 1.5,
                    "speed": np.random.uniform(80, 150),
                    "length": np.random.uniform(10, 25)
                }
            )
        for spark in self.spark_trails[:]:
            spark["life"] += self.dt
            spark["start_angle"] = (spark["start_angle"] + spark["speed"] * self.dt) % 360
            if spark["life"] > spark["max_life"]:
                self.spark_trails.remove(spark)

    def mouseMoveEvent(self, event):
        """Handle mouse movement for interactive effects."""
        self.mouse_pos = event.pos()
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        distance = math.hypot(self.mouse_pos.x() - center.x(), self.mouse_pos.y() - center.y())
        max_dist = math.sqrt((self.width()/2)**2 + (self.height()/2)**2)
        self.mouse_influence = max(0.0, 1.0 - distance / (max_dist * 0.8))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks for special effects."""
        if event.button() == Qt.LeftButton:
            self.trigger_special_effect()

    def trigger_special_effect(self):
        """Trigger the cinematic click effect."""
        self.click_animation_group.stop()
        
        # Setup vibration animation with random offsets
        self.vibration_anim.setStartValue(QPointF(0, 0))
        for i in range(1, 10):
            x_offset = np.random.uniform(-8, 8) * (1 - i/10)
            y_offset = np.random.uniform(-8, 8) * (1 - i/10)
            self.vibration_anim.setKeyValueAt(i / 10.0, QPointF(x_offset, y_offset))
        self.vibration_anim.setEndValue(QPointF(0, 0))

        self.click_animation_group.start()
        self.create_energy_ring()

    def paintEvent(self, event):
        """Main painting method with enhanced effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        center = QPointF(self.width() / 2.0, self.height() / 2.0)

        self.draw_enhanced_background(painter, center)
        self.draw_particle_system(painter)
        self.draw_enhanced_grid(painter)
        
        painter.save()
        painter.translate(self.vibration_offset) # Apply vibration
        
        self.draw_neural_rings(painter, center)
        self.draw_data_blips(painter, center)
        self.draw_spark_trails(painter, center)
        self.draw_enhanced_center_core(painter, center)
        self.draw_energy_rings(painter, center)
        
        painter.restore()

        painter.end()

    def draw_enhanced_background(self, painter, center):
        """Draw enhanced background with subtle gradients."""
        max_radius = math.hypot(self.width() / 2, self.height() / 2)
        gradient = QRadialGradient(center, max_radius)
        gradient.setColorAt(0.0, QColor(0, 8, 15))
        gradient.setColorAt(0.7, QColor(0, 4, 8))
        gradient.setColorAt(1.0, QColor(0, 0, 0))
        painter.fillRect(self.rect(), QBrush(gradient))

    def draw_particle_system(self, painter):
        """Draw animated background particles."""
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            dist_to_mouse = math.hypot(p["pos"].x() - self.mouse_pos.x(), p["pos"].y() - self.mouse_pos.y())
            influence = max(0, 1 - dist_to_mouse / 200) * self.mouse_influence
            
            alpha = p["alpha"] * (1 + influence * 1.5)
            alpha = max(0.0, min(255.0, alpha))
            size = p["size"] * (1 + influence * 2.0)
            
            color = QColor(0, 255, 255, int(alpha))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(p["pos"], size, size)

    def draw_enhanced_grid(self, painter):
        """Draw enhanced moving grid background."""
        grid_size = 60
        offset_x = (self.time * 10) % grid_size
        offset_y = (self.time * 10) % grid_size
        
        base_alpha = 20 + 10 * self.mouse_influence
        
        for x in range(int(-offset_x), self.width() + grid_size, grid_size):
            alpha = base_alpha + 15 * abs(math.sin(x * 0.01 + self.time))
            painter.setPen(QPen(QColor(0, 60, 80, int(alpha)), 1))
            painter.drawLine(x, 0, x, self.height())
            
        for y in range(int(-offset_y), self.height() + grid_size, grid_size):
            alpha = base_alpha + 15 * abs(math.sin(y * 0.01 + self.time))
            painter.setPen(QPen(QColor(0, 60, 80, int(alpha)), 1))
            painter.drawLine(0, y, self.width(), y)

    def draw_data_blips(self, painter, center):
        """Draw animated data blips around rings."""
        painter.setPen(Qt.NoPen)
        for blip in self.data_blips:
            angle_rad = math.radians(blip["angle"])
            pos = center + QPointF(blip["radius"] * math.cos(angle_rad), blip["radius"] * math.sin(angle_rad))
            
            progress = blip["life"] / blip["max_life"]
            # Fade in and out
            alpha = 255 * math.sin(progress * math.pi)
            size = 1.5 + 1.5 * math.sin(progress * math.pi)
            
            color = QColor(0, 255, 255, int(alpha))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pos, size, size)

    def draw_neural_rings(self, painter, center):
        """Draw neural processing rings with enhanced glow."""
        breathing = 0.5 + 0.5 * math.sin(self.breathing_phase)
        rings = [
            {"radius": 320, "width": 1 + breathing * 2, "alpha": 12, "segments": 0, "rotation": 0, "glow": 2},
            {"radius": 280, "width": 1 + breathing * 1.5, "alpha": 14, "segments": 60, "rotation": self.ring_rotations[2], "glow": 2},
            {"radius": 240, "width": 1, "alpha": 16, "segments": 48, "rotation": self.ring_rotations[3], "glow": 2},
            {"radius": 200, "width": 1, "alpha": 18, "segments": 36, "rotation": self.ring_rotations[4], "glow": 2},
            {"radius": 160, "width": 0.8, "alpha": 22, "segments": 24, "rotation": self.ring_rotations[5], "glow": 2},
            {"radius": 120, "width": 0.8, "alpha": 25, "segments": 18, "rotation": self.ring_rotations[6], "glow": 2},
        ]
        for ring in rings:
            self.draw_neural_ring(painter, center, ring)

    def draw_neural_ring(self, painter, center, config):
        """Draw a single neural ring with enhanced glow."""
        radius = config["radius"] * self.pulse_scale
        width = config["width"]
        alpha = config["alpha"] * (1.0 + 0.4 * self.mouse_influence)
        segments = config["segments"]
        rotation = config["rotation"]
        glow_layers = config.get("glow", 2)

        for i in range(glow_layers):
            glow_width = width + (glow_layers - i) * 1.5
            glow_alpha = alpha / (2 + i)
            self.draw_ring_segments(painter, center, radius, glow_width, glow_alpha, segments, rotation)
        
        self.draw_ring_segments(painter, center, radius, width, alpha, segments, rotation)

    def draw_ring_segments(self, painter, center, radius, width, alpha, segments, rotation):
        painter.setPen(QPen(QColor(0, 255, 255, int(alpha)), width))
        painter.setBrush(Qt.NoBrush)
        
        if segments == 0:
            painter.drawEllipse(center, radius, radius)
        else:
            painter.save()
            painter.translate(center)
            painter.rotate(rotation)
            
            segment_angle = 360 / segments
            arc_length = segment_angle * 0.7
            
            rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)
            for i in range(segments):
                start_angle = i * segment_angle
                painter.drawArc(rect, int(start_angle * 16), int(arc_length * 16))
            painter.restore()

    def draw_spark_trails(self, painter, center):
        """Draw spark trail effects."""
        for spark in self.spark_trails:
            progress = spark["life"] / spark["max_life"]
            
            start_angle_rad = math.radians(spark["start_angle"])
            end_angle_rad = math.radians(spark["start_angle"] - spark["length"] * (1 - progress))
            
            radius = spark["radius"]
            
            path = QPainterPath()
            path.arcMoveTo(QRectF(center.x()-radius, center.y()-radius, 2*radius, 2*radius), spark["start_angle"])
            path.arcTo(QRectF(center.x()-radius, center.y()-radius, 2*radius, 2*radius), spark["start_angle"], -spark["length"] * (1 - progress))

            alpha = 255 * math.sin(progress * math.pi)
            
            painter.setPen(QPen(QColor(255, 255, 255, int(alpha)), 1.5))
            painter.drawPath(path)

    def draw_enhanced_center_core(self, painter, center):
        """Draw enhanced pulsating center core."""
        pulse = 0.5 + 0.5 * abs(math.sin(self.pulse_phase))
        current_radius = 50 * self.pulse_scale

        # Glow layers
        for i in range(4):
            layer_radius = current_radius + i * 15
            alpha = (120 * pulse) / (i + 1)
            gradient = QRadialGradient(center, layer_radius)
            gradient.setColorAt(0, QColor(100, 255, 255, int(alpha)))
            gradient.setColorAt(0.8, QColor(0, 255, 255, int(alpha / 4)))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, layer_radius, layer_radius)

        # Core
        core_gradient = QRadialGradient(center, current_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, int(200 * pulse)))
        core_gradient.setColorAt(0.7, QColor(150, 255, 255, int(150 * pulse)))
        core_gradient.setColorAt(1, QColor(0, 255, 255, int(80 * pulse)))
        painter.setBrush(QBrush(core_gradient))
        painter.setPen(QPen(QColor(150, 255, 255, 200), 1))
        painter.drawEllipse(center, current_radius, current_radius)

        self.draw_center_text(painter, center, pulse)
        self.draw_dashed_arcs(painter, center, current_radius)

    def draw_energy_rings(self, painter, center):
        """Draw the energy ring emission effect."""
        for ring in self.energy_rings:
            progress = ring["life"] / ring["max_life"]
            radius = 10 + 200 * QEasingCurve(QEasingCurve.OutCubic).valueForProgress(progress)
            alpha = 180 * (1 - progress)
            
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0, QColor(0, 255, 255, 0))
            gradient.setColorAt(0.9, QColor(0, 255, 255, int(alpha)))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            
            pen = QPen(QBrush(gradient), 3)
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)

    def draw_dashed_arcs(self, painter, center, radius):
        """Draw thin dashed arcs around the center core."""
        painter.save()
        painter.setBrush(Qt.NoBrush)
        
        # Static inner ring
        painter.setPen(QPen(QColor(0, 180, 255, 180), 1))
        painter.drawEllipse(center, radius + 20, radius + 20)

        # Dashed rotating ring
        dash_pen = QPen(QColor(0, 180, 255, 100), 1, Qt.DashLine)
        dash_pen.setDashPattern([3, 6])
        painter.setPen(dash_pen)
        painter.save()
        painter.translate(center)
        painter.rotate(self.time * 20)
        painter.drawEllipse(QPointF(0,0), radius + 40, radius + 40)
        painter.restore()
        
        painter.restore()

    def draw_center_text(self, painter, center, pulse):
        """Draw MARK text with neon effects."""
        font = QFont("Orbitron", 20, QFont.Bold)
        painter.setFont(font)
        text = "MARK"
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        text_pos = QPointF(center.x() - text_width / 2, center.y() + text_height / 4)

        # Glow
        painter.setPen(QPen(QColor(0, 255, 255, int(60 * pulse)), 5))
        painter.drawText(text_pos, text)
        
        # Main text
        painter.setPen(QColor(220, 255, 255))
        painter.drawText(text_pos, text)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Space:
            self.trigger_special_effect()
        super().keyPressEvent(event)

class NOVAInterfaceWindow(QMainWindow):
    """Main window for NOVA AI Interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MARK AI Neural Core Interface")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color: black;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.left_panel = SystemStatsPanel()
        self.nova_widget = NOVAInterfaceWidget()
        self.right_panel = RightPanel()

        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.nova_widget, 1) # Central widget takes extra space
        main_layout.addWidget(self.right_panel)

        self.assistant = None
        self.agent_thread = None
        self.agent_loop = None
        self.agent_server = None
        
        self._start_agent_background()
        self.setup_callbacks()

    def set_video_track(self, video_source):
        """Set the video track for sending frames to LiveKit."""
        print(f"🎯 Setting video source in RightPanel: {video_source is not None}")
        self.right_panel.set_video_track(video_source)

    def set_assistant(self, assistant):
        """Set the assistant reference when it's ready."""
        self.assistant = assistant
        self.right_panel.assistant = assistant
        print(f"✅ Main window and right panel assistant set: {assistant is not None}")

    def setup_callbacks(self):
        """Connect TTS to trigger effects in the widget."""
        # This is a placeholder. The actual callback is passed to the agent entrypoint.
        pass

    def get_effect_callback(self):
        """Return the effect function for external TTS use."""
        return self.nova_widget.trigger_special_effect

    def _start_agent_background(self):
        """Starts the agent in a background thread using direct Worker instantiation."""
        def run_agent():
            import asyncio
            # --- FIX: Split the imports ---
            from livekit.agents import WorkerOptions
            from livekit.agents.worker import Worker # Import Worker from the correct submodule
            # ------------------------------
            
            from Nova_Voice_Assistant import entrypoint

            # 1. Create a new event loop for this background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.agent_loop = loop

            try:
                print('🟡 Starting LiveKit Worker (Direct Mode)...')
                
                # 2. Instantiate Worker directly
                worker = Worker(
                    WorkerOptions(entrypoint_fnc=entrypoint)
                )
                
                self.agent_server = worker 

                # 3. Run the worker
                loop.run_until_complete(worker.run())
                
            except Exception as e:
                print(f'❌ Agent thread error: {e}')
                import traceback
                traceback.print_exc()
            finally:
                print('🔴 Agent worker stopped')
                loop.close()

        self.agent_thread = threading.Thread(target=run_agent, daemon=True)
        self.agent_thread.start()
        print('🟡 Agent thread started')


    def closeEvent(self, event):
        """Override close event to stop agent properly."""
        print("Shutting down application...")
        self._stop_agent_background()
        super().closeEvent(event)
        if self.agent_thread and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=5)

    def _stop_agent_background(self):
        """Request the background agent thread to stop."""
        if not self.agent_loop or not self.agent_server:
            return

        try:
            drain_future = asyncio.run_coroutine_threadsafe(
                self.agent_server.drain(), self.agent_loop
            )
            drain_future.result(timeout=5)
        except Exception as e:
            print(f"⚠️ Agent drain warning: {e}")

        try:
            close_future = asyncio.run_coroutine_threadsafe(
                self.agent_server.aclose(), self.agent_loop
            )
            close_future.result(timeout=5)
        except Exception as e:
            print(f"⚠️ Agent close warning: {e}")

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_F:
            if self.windowFlags() & Qt.FramelessWindowHint:
                self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            else:
                self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.show()
        else:
            super().keyPressEvent(event)

# --- Utility and Authentication Functions ---
# Note: These functions are kept separate for clarity but could be in their own modules.

def get_service_json_path():
    """Returns the path to service.json whether running from source or PyInstaller exe."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "voice.json")

def init_firebase_from_embedded(database_url=None):
    """Initializes Firebase from service.json."""
    path = get_service_json_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Firebase service file not found: {path}")
    cred = credentials.Certificate(path)
    firebase_admin.initialize_app(
        cred, {"databaseURL": database_url or "https://novavoiceassitant-default-rtdb.firebaseio.com"}
    )

def wait_for_internet():
    """Shows a dialog while waiting for an internet connection."""
    # This is a simplified version. A real implementation would use a QDialog.
    print("Checking for internet connection...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("✅ Internet connection available.")
        return True
    except OSError:
        print("❌ No internet connection.")
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("Network Error")
        msg_box.setInformativeText("NOVA requires an internet connection to start.")
        msg_box.setWindowTitle("Connection Error")
        msg_box.exec_()
        return False

def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1].lower() == "console":
        agents_cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
        return

    app = QApplication(sys.argv)
    
    # Set a more modern font if available
    font = QFont("Orbitron")
    if QFontMetrics(font).horizontalAdvance("X") > 0:
        app.setFont(font)

    if not wait_for_internet():
        sys.exit(1)

    # Placeholder for activation gate and user name logic
    # if not activation_gate():
    #     sys.exit(1)
    # ensure_user_name()

    window = NOVAInterfaceWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
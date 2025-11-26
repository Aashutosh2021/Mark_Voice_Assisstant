import sys
import os
import signal
import subprocess
import psutil
import cv2
import numpy as np

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)


# ===================== Assistant Integration =====================

class AssistantManager:
    """
    Yeh class Nova_Voice_Assistant.py ko start/stop handle karegi.
    Yahi se GUI ke saath assistant ka lifecycle linked rahega.
    """

    def __init__(self):
        self.process = None

    def start_nova_voice_assistant(self):
        script_path = os.path.join(os.getcwd(), "Nova_Voice_Assistant.py")

        if not os.path.exists(script_path):
            print("⚠ Nova_Voice_Assistant.py file nahi mili!")
            return None

        print("🚀 Nova Voice Assistant starting...")
        process = subprocess.Popen([sys.executable, script_path, "console"])
        return process

    def stop_nova_voice_assistant(self):
        assistant = start_nova_voice_assistant()
        if assistant:
        # Kill the assistant process
            try:
                assistant.terminate()
            except:
                pass

            try:
                os.kill(assistant.pid, signal.SIGTERM)
            except:
                pass

            print("🛑 Nova Voice Assistant band ho gaya.")


    def send_frame(self, frame: np.ndarray):
        """
        Yahan se tu assistant ko camera frame bhej sakta hai.
        Abhi ye sirf demo print kar raha hai.

        frame: RGB numpy array (H x W x 3)
        """
        if self.process is None or self.process.poll() is not None:
            # Assistant nahi chal raha, to skip
            return

        # 👇 Yahan tu apni actual integration karega:
        # - LiveKit stream
        # - Named pipe / socket
        # - REST API
        # etc.
        # print(f"🎥 Frame ready to send to assistant, shape={frame.shape}")


# ===================== Sci-Fi Animation Widget =====================

class SciFiAnimationWidget(QWidget):
    """
    Beech ka sci-fi animation: rotating rings + pulse effect.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # ~33 FPS

    def update_animation(self):
        self.angle = (self.angle + 3) % 360
        self.pulse += self.pulse_dir * 2
        if self.pulse > 30:
            self.pulse_dir = -1
        elif self.pulse < 0:
            self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) * 0.8
        center_x = w / 2
        center_y = h / 2

        # Background
        painter.fillRect(self.rect(), QColor(5, 5, 15))

        # Outer ring (QRectF allow float, so this is fine)
        pen = QPen(QColor(0, 255, 200), 3)
        painter.setPen(pen)
        rect = QRectF(
            center_x - size / 2,
            center_y - size / 2,
            size,
            size,
        )
        painter.drawEllipse(rect)

        # Rotating arc
        pen = QPen(QColor(0, 180, 255), 4)
        painter.setPen(pen)
        painter.drawArc(rect, int(self.angle * 16), int(120 * 16))

        # Inner pulse circle
        inner_radius = size * 0.15 + self.pulse
        pen = QPen(QColor(0, 255, 120), 2)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 150, 100, 80))

        x = int(center_x - inner_radius / 2)
        y = int(center_y - inner_radius / 2)
        w_ = int(inner_radius)
        h_ = int(inner_radius)

        painter.drawEllipse(x, y, w_, h_)

        # Crosshair lines → yahan bhi ints chahiye
        pen = QPen(QColor(0, 100, 180), 1)
        painter.setPen(pen)

        x1 = int(center_x - size / 2)
        y1 = int(center_y)
        x2 = int(center_x + size / 2)
        y2 = int(center_y)
        painter.drawLine(x1, y1, x2, y2)

        x3 = int(center_x)
        y3 = int(center_y - size / 2)
        x4 = int(center_x)
        y4 = int(center_y + size / 2)
        painter.drawLine(x3, y3, x4, y4)



# ===================== Main GUI Window =====================

class NovaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NOVA AI – Sci-Fi Control Interface")
        self.setGeometry(200, 100, 1200, 700)
        self.setStyleSheet("background-color: #050510; color: #E0FFFF;")

        self.assistant_mgr = AssistantManager()
        self.cap = None
        self.camera_timer = None
        self.battery_timer = None

        self._init_ui()
        self._start_assistant()
        self._start_camera()
        self._start_battery_monitor()

    # ---------- UI Setup ----------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # LEFT: Battery panel
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setStyleSheet(
            "QFrame { background-color: #0A0A15; border-radius: 10px; border: 1px solid #202040; }"
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        title = QLabel("SYSTEM POWER STATUS")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00F0FF;")
        self.battery_label = QLabel("Battery: --%")
        self.battery_label.setStyleSheet("font-size: 14px;")
        self.power_source_label = QLabel("Source: Unknown")
        self.power_source_label.setStyleSheet("font-size: 14px;")

        left_layout.addWidget(title)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.battery_label)
        left_layout.addWidget(self.power_source_label)
        left_layout.addStretch()

        # CENTER: Sci-fi animation
        center_panel = QFrame()
        center_panel.setFrameShape(QFrame.StyledPanel)
        center_panel.setStyleSheet(
            "QFrame { background-color: #050515; border-radius: 10px; border: 1px solid #303060; }"
        )
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)

        center_title = QLabel("NEURAL CORE ACTIVITY")
        center_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFEA00;")
        center_title.setAlignment(Qt.AlignCenter)

        self.sci_fi_widget = SciFiAnimationWidget()

        center_layout.addWidget(center_title)
        center_layout.addWidget(self.sci_fi_widget, 1)

        # RIGHT: Camera panel
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel.setStyleSheet(
            "QFrame { background-color: #050515; border-radius: 10px; border: 1px solid #303060; }"
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)

        cam_title = QLabel("VISION FEED")
        cam_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF5FD1;")
        cam_title.setAlignment(Qt.AlignCenter)

        self.camera_label = QLabel("Initializing camera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #000000; border-radius: 8px;")
        self.camera_label.setMinimumSize(320, 240)

        right_layout.addWidget(cam_title)
        right_layout.addWidget(self.camera_label, 1)

        # Layout distribution
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_panel, 1)
        main_layout.addWidget(right_panel, 1)

    # ---------- Battery Monitoring ----------

    def _start_battery_monitor(self):
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(2000)  # every 2 sec
        self.update_battery_status()

    def update_battery_status(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                self.battery_label.setText("Battery: Not available")
                self.power_source_label.setText("Source: Unknown")
                return

            percent = battery.percent
            plugged = battery.power_plugged

            self.battery_label.setText(f"Battery: {percent:.0f}%")
            if plugged:
                self.power_source_label.setText("Source: AC Power (Charging)")
            else:
                self.power_source_label.setText("Source: On Battery")
        except Exception as e:
            self.battery_label.setText("Battery: Error")
            self.power_source_label.setText(str(e))

    # ---------- Assistant Control ----------

    def _start_assistant(self):
        self.assistant_mgr.start_nova_voice_assistant()

    def _stop_assistant(self):
        self.assistant_mgr.stop_nova_voice_assistant()

    # ---------- Camera Handling ----------

    def _start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.camera_label.setText("❌ Unable to access camera")
            return

        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_frame)
        self.camera_timer.start(30)  # ~33 FPS

    def update_camera_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # OpenCV frame is BGR → convert to RGB for Qt + assistant
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Show in GUI
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.camera_label.setPixmap(
            pix.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        # Send frame to assistant manager (integration hook)
        self.assistant_mgr.send_frame(rgb_frame)

    def _stop_camera(self):
        if self.camera_timer is not None:
            self.camera_timer.stop()
            self.camera_timer = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    # ---------- Window Close ----------

    def closeEvent(self, event):
        print("🛑 Shutting down GUI & assistant...")
        self._stop_camera()
        self._stop_assistant()
        sys.exit()
        super().closeEvent(event)


# ===================== Entry Point =====================

def main():
    app = QApplication(sys.argv)
    window = NovaMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
 
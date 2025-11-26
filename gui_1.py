import sys
import math
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout,
    QGraphicsDropShadowEffect,
)


# ---------- Utility: Neon shadow / glow ----------
def make_glow(target, color="#00e5ff", blur=25, offset=(0, 0)):
    effect = QGraphicsDropShadowEffect()
    effect.setColor(QColor(color))
    effect.setBlurRadius(blur)
    effect.setOffset(*offset)
    target.setGraphicsEffect(effect)


# ---------- Center Radar / Neural Core ----------
class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(30)  # ~33 FPS

    def update_angle(self):
        self.angle = (self.angle + 1.2) % 360
        self.update()

    def sizeHint(self):
        return super().sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )

        w = self.width()
        h = self.height()
        radius = min(w, h) * 0.40
        center = QPointF(w / 2, h / 2)

        # Background grid feel
        painter.fillRect(self.rect(), QColor("#050910"))

        # Faint grid lines
        pen = QPen(QColor(10, 30, 45))
        pen.setWidth(1)
        painter.setPen(pen)
        step = 40
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

        # Concentric rings
        ring_count = 7
        for i in range(ring_count):
            r = radius * (i + 1) / ring_count
            alpha = 40 if i < ring_count - 1 else 80
            pen = QPen(QColor(0, 229, 255, alpha))
            pen.setWidth(2 if i == ring_count - 1 else 1)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, r, r)

        # Rotating sweep arc
        sweep_radius = radius * 0.95
        pen = QPen(QColor(0, 255, 200, 160))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 255, 200, 40))
        start_angle = int(self.angle * 16)
        span_angle = int(40 * 16)
        painter.drawPie(
            int(center.x() - sweep_radius),
            int(center.y() - sweep_radius),
            int(2 * sweep_radius),
            int(2 * sweep_radius),
            start_angle,
            span_angle,
        )

        # Random orbiting points (deterministic pattern)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(18):
            orbit_r = radius * (0.25 + (i % 5) * 0.14)
            theta = math.radians(self.angle * 1.5 + i * 40)
            x = center.x() + orbit_r * math.cos(theta)
            y = center.y() + orbit_r * math.sin(theta)
            painter.setBrush(QColor(0, 255, 220, 230 if i % 3 == 0 else 120))
            painter.drawEllipse(QPointF(x, y), 3, 3)

        # Inner glowing core
        grad_color_outer = QColor(0, 180, 200)
        grad_color_inner = QColor(160, 255, 255)
        core_r1 = radius * 0.40
        core_r2 = radius * 0.26

        # Outer ring
        pen = QPen(QColor(0, 240, 255))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 80, 90, 80))
        painter.drawEllipse(center, core_r1, core_r1)

        # Inner solid circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad_color_outer)
        painter.drawEllipse(center, core_r2 * 1.2, core_r2 * 1.2)

        painter.setBrush(grad_color_inner)
        painter.drawEllipse(center, core_r2, core_r2)

        # Core text "MARK"
        painter.setPen(QColor("#021016"))
        font = QFont("Segoe UI", int(core_r2 * 0.55))
        font.setBold(True)
        painter.setFont(font)
        text = "MARK"
        rect_w = core_r2 * 2
        rect_h = core_r2 * 1.1
        painter.drawText(
            int(center.x() - rect_w / 2),
            int(center.y() - rect_h / 2),
            int(rect_w),
            int(rect_h),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )


# ---------- Reusable Info Card ----------
class InfoCard(QFrame):
    def __init__(self, title, value, subtitle=None, wide=False, parent=None):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("cardSubtitle")
            layout.addWidget(self.subtitle_label)

        make_glow(self, blur=18, color="#0095ff" if not wide else "#00ffdd")


# ---------- Right-side block with header ----------
class Block(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("blockFrame")
        self.setFrameShape(QFrame.Shape.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 12)
        outer.setSpacing(6)

        header = QLabel(title)
        header.setObjectName("sectionHeader")
        outer.addWidget(header)

        self.inner = QFrame()
        self.inner.setObjectName("innerPanel")
        inner_layout = QVBoxLayout(self.inner)
        inner_layout.setContentsMargins(12, 10, 12, 10)
        inner_layout.setSpacing(8)
        outer.addWidget(self.inner)

        make_glow(self.inner, blur=25, color="#00e5ff")

    def layout(self):
        return self.inner.layout()


# ---------- Main Window ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MARK AI Neural Core Interface")
        self.resize(1320, 760)
        self.setMinimumSize(1100, 650)

        self.setStyleSheet(self.build_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 12)
        root.setSpacing(16)

        # ----- Left: System Status -----
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        system_title = QLabel("SYSTEM STATUS")
        system_title.setObjectName("sidebarTitle")
        left_col.addWidget(system_title)

        left_col.addWidget(InfoCard("CPU UTILIZATION", "25.4 %"))
        left_col.addWidget(InfoCard("MEMORY ALLOCATION", "12.9 / 13.7 GB"))
        left_col.addWidget(InfoCard("STORAGE CAPACITY", "396 / 1071 GB (3 drives)"))
        left_col.addWidget(InfoCard("CORE TEMPERATURE", "0 °C"))
        left_col.addWidget(InfoCard("POWER STATUS", "POWER: AC"))

        env_title = QLabel("ENVIRONMENT")
        env_title.setObjectName("sidebarTitle")
        left_col.addSpacing(10)
        left_col.addWidget(env_title)
        left_col.addWidget(InfoCard("NEURAL CITY", "18 °C", "RAIN"))

        left_container = QFrame()
        left_container.setLayout(left_col)
        root.addWidget(left_container, 1)

        # ----- Center: Radar -----
        center_container = QFrame()
        center_container.setObjectName("centerFrame")
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        radar = RadarWidget()
        center_layout.addWidget(radar)
        root.addWidget(center_container, 3)

        # ----- Right: Time, network, camera -----
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # Temporal Synchronization block
        time_block = Block("TEMPORAL SYNCHRONIZATION")
        self.time_label = QLabel("11:31:29")
        self.time_label.setObjectName("timeBig")
        self.date_label = QLabel("Monday, 24 November 2025")
        self.date_label.setObjectName("timeSub")

        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(8, 4, 8, 4)
        time_layout.addWidget(self.time_label, 0, Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignCenter)

        tframe = QFrame()
        tframe.setObjectName("timeFrame")
        tframe.setLayout(time_layout)
        make_glow(tframe, color="#00ffea", blur=30)

        time_block.layout().addWidget(tframe)
        right_col.addWidget(time_block)

        # Network Interface block
        net_block = Block("NETWORK INTERFACE")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        def kv_row(r, key, value):
            k = QLabel(key)
            k.setObjectName("smallKey")
            v = QLabel(value)
            v.setObjectName("smallValue")
            grid.addWidget(k, r, 0)
            grid.addWidget(v, r, 1)

        kv_row(0, "IP ADDRESS", "10.25.154.115")
        kv_row(1, "BANDWIDTH", "↑ 12.9 Mbps / ↓ 30.1 Mbps")
        kv_row(2, "CONNECTION", "Aashutosh's Phone – 87%")

        net_panel = QFrame()
        net_panel.setObjectName("netPanel")
        net_panel.setLayout(grid)
        net_block.layout().addWidget(net_panel)
        right_col.addWidget(net_block)

        # Visual Input block (camera preview placeholder)
        vis_title = QLabel("VISUAL INPUT")
        vis_title.setObjectName("sidebarTitle")
        right_col.addWidget(vis_title)

        cam_frame = QFrame()
        cam_frame.setObjectName("cameraFrame")
        cam_layout = QVBoxLayout(cam_frame)
        cam_layout.setContentsMargins(0, 0, 0, 0)

        cam_placeholder = QLabel("CAMERA FEED\n(attach here)")
        cam_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_placeholder.setObjectName("cameraText")

        cam_layout.addWidget(cam_placeholder)
        make_glow(cam_frame, blur=22, color="#0088ff")

        right_col.addWidget(cam_frame, 1)

        right_container = QFrame()
        right_container.setLayout(right_col)
        root.addWidget(right_container, 1)

        # Time updater
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()

    # ---------- Time update ----------
    def update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%A, %d %B %Y"))

    # ---------- Global Stylesheet ----------
    def build_stylesheet(self):
        return """
        QWidget {
            background-color: #03070c;
            color: #d8f9ff;
            font-family: "Segoe UI", "Poppins", "Roboto";
        }

        #centerFrame {
            background-color: #020508;
            border: 1px solid #082431;
            border-radius: 14px;
        }

        #infoCard {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #07121b,
                stop:1 #020910
            );
            border-radius: 10px;
            border: 1px solid #063346;
        }

        #cardTitle {
            font-size: 10px;
            letter-spacing: 2px;
            color: #4eb8ff;
        }

        #cardValue {
            font-size: 15px;
            font-weight: 600;
            color: #ecfeff;
        }

        #cardSubtitle {
            font-size: 10px;
            color: #9ddfff;
        }

        #sidebarTitle {
            font-size: 11px;
            letter-spacing: 2px;
            color: #0ecbff;
        }

        #sectionHeader {
            font-size: 11px;
            letter-spacing: 2px;
            color: #0ecbff;
        }

        #blockFrame {
            border: none;
        }

        #innerPanel {
            background-color: #050e17;
            border-radius: 12px;
            border: 1px solid #073043;
        }

        #timeFrame {
            background-color: #031621;
            border-radius: 12px;
            border: 1px solid #0aa6c9;
        }

        #timeBig {
            font-size: 26px;
            font-weight: 600;
            color: #ffffff;
        }

        #timeSub {
            font-size: 11px;
            color: #8fe4ff;
        }

        #smallKey {
            font-size: 9px;
            color: #4eb8ff;
            letter-spacing: 1px;
        }

        #smallValue {
            font-size: 11px;
            color: #e8fdff;
        }

        #netPanel {
            background-color: #031119;
            border-radius: 10px;
            border: 1px solid #073043;
        }

        #cameraFrame {
            background-color: #050f18;
            border-radius: 14px;
            border: 1px solid #0c3f5f;
        }

        #cameraText {
            font-size: 11px;
            color: #6bc5ff;
        }
        """


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

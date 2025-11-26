"""
Nova Desktop Interface
A clean PyQt5 GUI for the Nova Voice Assistant backend.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional
import threading
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient
from Nova_Voice_Assistant import entrypoint


try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - battery status will show N/A")

def _start_agent_background():
    """Starts the agent in a background thread with proper context"""
    def start_nova_backend() -> Optional[subprocess.Popen]:
                """
                Start the Nova_Voice_Assistant.py backend process.
                
                Returns:
                    subprocess.Popen object if successful, None otherwise.
                """
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
                agent_thread = threading.Thread(target=start_nova_backend, daemon=True)
                agent_thread.start()
                print('🟡 Agent thread started')


class RingWidget(QWidget):
    """
    Custom widget that draws an animated pulsing ring with orbiting dots.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # Animation parameters
        self._t = 0.0
        self._base_radius = 80
        self._num_dots = 6
        
        # Start animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(33)  # ~30 fps
    
    def _update_animation(self):
        """Update animation phase and trigger repaint."""
        self._t += 0.05
        self.update()
    
    def paintEvent(self, event):
        """Draw the animated ring visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget center
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        # Background
        painter.fillRect(self.rect(), QColor(18, 18, 24))
        
        # Outer glow
        glow_gradient = QRadialGradient(center_x, center_y, self._base_radius + 40)
        glow_gradient.setColorAt(0, QColor(100, 150, 255, 30))
        glow_gradient.setColorAt(1, QColor(100, 150, 255, 0))
        painter.setBrush(glow_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPointF(center_x, center_y),
            self._base_radius + 40,
            self._base_radius + 40
        )
        
        # Pulsing main ring
        pulse = math.sin(self._t) * 5
        ring_radius = self._base_radius + pulse
        
        # Ring gradient
        ring_gradient = QRadialGradient(center_x, center_y, ring_radius)
        ring_gradient.setColorAt(0, QColor(70, 130, 255, 0))
        ring_gradient.setColorAt(0.8, QColor(100, 150, 255, 120))
        ring_gradient.setColorAt(1, QColor(120, 170, 255, 180))
        
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(100, 150, 255, 200), 3))
        painter.drawEllipse(
            QPointF(center_x, center_y),
            ring_radius,
            ring_radius
        )
        
        # Orbiting dots
        for i in range(self._num_dots):
            angle = (self._t * 0.5) + (i * 2 * math.pi / self._num_dots)
            dot_x = center_x + ring_radius * math.cos(angle)
            dot_y = center_y + ring_radius * math.sin(angle)
            
            # Dot gradient
            dot_gradient = QRadialGradient(dot_x, dot_y, 6)
            dot_gradient.setColorAt(0, QColor(150, 200, 255, 255))
            dot_gradient.setColorAt(1, QColor(100, 150, 255, 100))
            
            painter.setBrush(dot_gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dot_x, dot_y), 6, 6)
        
        # Inner core circle
        core_radius = 50
        core_gradient = QRadialGradient(center_x, center_y, core_radius)
        core_gradient.setColorAt(0, QColor(80, 140, 255, 100))
        core_gradient.setColorAt(1, QColor(60, 120, 255, 30))
        
        painter.setBrush(core_gradient)
        painter.setPen(QPen(QColor(100, 150, 255, 150), 2))
        painter.drawEllipse(
            QPointF(center_x, center_y),
            core_radius,
            core_radius
        )
        
        # Center text "NOVA"
        painter.setPen(QColor(200, 220, 255))
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")


class BatteryWidget(QFrame):
    """
    Widget that displays battery status and power source.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """Initialize UI elements."""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 180);
                border: 1px solid rgba(100, 150, 255, 100);
                border-radius: 8px;
                padding: 8px 12px;
            }
            QLabel {
                color: #E0E0E0;
                background: transparent;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Battery icon
        self._icon_label = QLabel("🔋")
        self._icon_label.setFont(QFont("Segoe UI", 16))
        
        # Battery percentage
        self._battery_label = QLabel("Battery: N/A")
        self._battery_label.setFont(QFont("Segoe UI", 10))
        
        # Power source
        self._power_label = QLabel("Power: Unknown")
        self._power_label.setFont(QFont("Segoe UI", 10))
        
        layout.addWidget(self._icon_label)
        layout.addWidget(self._battery_label)
        layout.addWidget(self._power_label)
    
    def _setup_timer(self):
        """Start timer to update battery status."""
        self._update_battery_status()
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_battery_status)
        self._timer.start(5000)  # Update every 5 seconds
    
    def _update_battery_status(self):
        """Update battery information using psutil."""
        if not PSUTIL_AVAILABLE:
            self._battery_label.setText("Battery: N/A")
            self._power_label.setText("Power: Unknown")
            self._icon_label.setText("⚡")
            return
        
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                self._battery_label.setText("Battery: N/A")
                self._power_label.setText("Power: No battery")
                self._icon_label.setText("🖥️")
                return
            
            # Update battery percentage
            percent = battery.percent
            self._battery_label.setText(f"Battery: {percent:.0f}%")
            
            # Update power source
            if battery.power_plugged:
                self._power_label.setText("Power: AC")
                if percent >= 95:
                    self._icon_label.setText("🔌")
                else:
                    self._icon_label.setText("⚡")
            else:
                self._power_label.setText("Power: Battery")
                if percent > 50:
                    self._icon_label.setText("🔋")
                elif percent > 20:
                    self._icon_label.setText("🪫")
                else:
                    self._icon_label.setText("⚠️")
        
        except Exception as e:
            print(f"⚠️ Failed to read battery status: {e}")
            self._battery_label.setText("Battery: Error")
            self._power_label.setText("Power: Unknown")
            self._icon_label.setText("❌")


class MainWindow(QWidget):
    """
    Main window for the Nova Desktop Interface.
    """
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Nova Desktop Interface")
        self.setMinimumSize(700, 450)
        self.resize(800, 550)
        
        # Dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #12121A;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
    
    def _setup_ui(self):
        """Create and arrange UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # Top bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Spacer
        main_layout.addStretch(1)
        
        # Center ring
        ring_container = QVBoxLayout()
        ring_container.setAlignment(Qt.AlignCenter)
        
        self._ring_widget = RingWidget(self)
        ring_container.addWidget(self._ring_widget, alignment=Qt.AlignCenter)
        
        # Status label below ring
        status_label = QLabel("Nova backend is running in background...")
        status_label.setStyleSheet("""
            QLabel {
                color: rgba(200, 220, 255, 150);
                font-size: 12px;
                padding: 8px;
            }
        """)
        status_label.setAlignment(Qt.AlignCenter)
        ring_container.addWidget(status_label, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(ring_container)
        
        # Bottom spacer
        main_layout.addStretch(1)
    
    def _create_top_bar(self) -> QWidget:
        """Create the top bar with title and battery status."""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # App title
        title_label = QLabel("Nova AI Interface")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        # Battery widget
        self._battery_widget = BatteryWidget(self)
        top_layout.addWidget(self._battery_widget)
        
        return top_widget


def main():
    """Main entry point for the application."""
    # Start Nova backend first
    backend_process = _start_agent_background()
    
    # Create and run GUI
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    exit_code = app.exec_()
    
    # Clean up backend process on exit
    if backend_process and backend_process.poll() is None:
        print("🔴 Terminating Nova backend...")
        backend_process.terminate()
        backend_process.wait(timeout=5)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

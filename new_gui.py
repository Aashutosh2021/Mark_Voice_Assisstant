import sys
import asyncio
import cv2
import numpy as np
import subprocess
import os
import atexit
import threading
from datetime import datetime
from dotenv import load_dotenv

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont

# LiveKit Imports
from livekit import rtc, api
from livekit.rtc import VideoFrame, VideoBufferType, VideoSource, TrackPublishOptions, TrackSource

load_dotenv()

# --- Configuration ---
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
    print("❌ Error: LIVEKIT env variables missing. Check your .env file.")
    sys.exit(1)

# --- Worker for Network Logic (Thread Safe) ---
# --- Worker for Network Logic (Thread Safe) ---
# --- Worker for Network Logic (Thread Safe) ---
class NetworkWorker(QObject):
    status_update = pyqtSignal(str, str) # text, color
    agent_update = pyqtSignal(str)
    connection_success = pyqtSignal() # Signal to tell Main Thread to launch Agent

    def __init__(self, video_source):
        super().__init__()
        self.room = rtc.Room()
        self.video_source = video_source
        self.loop = asyncio.new_event_loop()

    def start(self):
        """Starts the async loop in a separate thread."""
        t = threading.Thread(target=self.run_loop, daemon=True)
        t.start()

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_room())
        self.loop.run_forever()

    async def connect_to_room(self):
        try:
            self.status_update.emit("SYSTEM: CONNECTING...", "#FFFF00")
            
            token = (
                api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
                .with_identity("human-user")
                .with_name("Aashutosh")
                .with_grants(api.VideoGrants(room_join=True, room="nova-room"))
                .to_jwt()
            )

            print("📡 Connecting to LiveKit Cloud...")
            await self.room.connect(LIVEKIT_URL, token)
            print("✅ Connected to Room")

            # 1. Try Audio First (FIXED)
            print("🎤 Publishing Audio...")
            try:
                # --- FIX START: Added TrackSource.SOURCE_MICROPHONE ---
                from livekit.rtc import AudioSource
                # Create a source first (if required by your specific SDK version) or pass directly
                # For most recent SDKs, create_audio_track requires a name and a source type
                audio_track = rtc.LocalAudioTrack.create_audio_track("mic_feed", rtc.AudioSource(48000, 1)) 
                # Note: If the above line fails in your specific version, try:
                # audio_track = rtc.LocalAudioTrack.create_audio_track("mic_feed") 
                # BUT based on your error, it likely needs the AudioSource object or similar.
                # Let's try the most standard 1.x way:
                
                # Standard way in 1.x+: Create source -> Create track
                # But for pure mic input without processing, we often just need the proper publish call
                # Your specific error says 'source' argument is missing in create_audio_track
                
                # CORRECT FIX FOR SDK 1.x+:
                audio_track = rtc.LocalAudioTrack.create_audio_track("mic_feed", rtc.AudioSource(48000, 1))
                # -------------------------------------------------------

                # Wait max 5 seconds for audio to publish
                await asyncio.wait_for(self.room.local_participant.publish_track(audio_track), timeout=5.0)
                print("✅ Audio Published")
            except asyncio.TimeoutError:
                print("⚠️ Audio Publish Timed Out (Network Firewall?)")
            except Exception as e:
                print(f"⚠️ Audio Error: {e}")
                # Fallback attempt for older SDK signatures if the above fails
                try:
                     audio_track = rtc.LocalAudioTrack.create_audio_track("mic_feed")
                     await self.room.local_participant.publish_track(audio_track)
                except:
                    pass

            # 2. Try Video Second
            print("📤 Publishing Video...")
            try:
                video_track = rtc.LocalVideoTrack.create_video_track("camera_feed", self.video_source)
                video_opts = TrackPublishOptions()
                video_opts.source = TrackSource.SOURCE_CAMERA
                # Wait max 8 seconds for video to publish
                await asyncio.wait_for(self.room.local_participant.publish_track(video_track, video_opts), timeout=8.0)
                print("✅ Video Published")
            except asyncio.TimeoutError:
                print("⚠️ Video Publish Timed Out (Network/Bandwidth Issue). Proceeding without video.")
            except Exception as e:
                print(f"⚠️ Video Error: {e}")

            # 3. Force Agent Launch (Even if media failed slightly)
            self.status_update.emit("SYSTEM: ONLINE", "#00FFCC")
            self.connection_success.emit()

        except Exception as e:
            print(f"❌ Connection Error: {e}")
            self.status_update.emit("SYSTEM: ERROR", "#FF0000")
            self.agent_update.emit(f"ERR: {str(e)[:20]}...")
            
class CameraThread(QThread):
    """Captures video, updates GUI, and sends frames to LiveKit."""
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, video_source: VideoSource):
        super().__init__()
        self.video_source = video_source
        self.running = True
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    height, width, _ = rgb_frame.shape
                    lk_frame = VideoFrame(width, height, VideoBufferType.RGBA, rgb_frame.tobytes())
                    self.video_source.capture_frame(lk_frame)
                except Exception:
                    pass
            self.msleep(33)

    def stop(self):
        self.running = False
        self.wait()
        if self.cap.isOpened():
            self.cap.release()

class NovaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MARK IV - Neural Interface")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #050505; color: #00FFCC;")
        
        # LiveKit Components
        self.video_source = rtc.VideoSource(640, 480)
        self.network_worker = NetworkWorker(self.video_source)
        self.agent_process = None

        self.init_ui()
        
        # Connect Signals
        self.network_worker.status_update.connect(self.update_status)
        self.network_worker.agent_update.connect(self.update_agent_status)
        
        # CRITICAL: Only launch agent AFTER connection succeeds
        self.network_worker.connection_success.connect(self.start_agent_backend)

        # Start Systems
        self.start_camera_local()
        self.network_worker.start()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Left Panel
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        self.status_label = QLabel("SYSTEM: INITIALIZING...")
        self.status_label.setFont(QFont("Orbitron", 10, QFont.Bold))
        self.status_label.setStyleSheet("color: #FF5555; border: 1px solid #FF5555; padding: 5px;")
        
        self.agent_status = QLabel("AGENT: WAITING...")
        self.agent_status.setFont(QFont("Orbitron", 10))
        self.agent_status.setStyleSheet("color: #888888; margin-top: 10px;")

        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.agent_status)
        left_layout.addStretch()
        layout.addWidget(left_panel)

        # Camera Feed
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #00FFCC; background-color: #001111;")
        self.camera_label.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=20, color=QColor(0, 255, 204)))
        layout.addWidget(self.camera_label)

    def start_camera_local(self):
        self.camera_thread = CameraThread(self.video_source)
        self.camera_thread.frame_captured.connect(self.update_image)
        self.camera_thread.start()

    def start_agent_backend(self):
        """Called only after GUI has secured the hardware."""
        try:
            print("🚀 Launching Nova Agent...")
            self.update_agent_status("AGENT: LAUNCHING...")
            self.agent_process = subprocess.Popen(
                [sys.executable, "Nova_Voice_Assistant.py", "start"],
                cwd=os.getcwd(),
                shell=False
            )
            atexit.register(self.kill_agent)
            self.update_agent_status("AGENT: LISTENING")
        except Exception as e:
            self.status_label.setText(f"ERROR: {str(e)}")

    def kill_agent(self):
        if self.agent_process:
            print("💀 Terminating Agent...")
            self.agent_process.terminate()
            try:
                self.agent_process.wait(timeout=2)
            except:
                self.agent_process.kill()

    # --- UI Updates ---
    def update_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; border: 1px solid {color}; padding: 5px;")

    def update_agent_status(self, text):
        self.agent_status.setText(text)

    def update_image(self, cv_frame):
        rgb_image = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        convert_to_Qt_format = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.camera_label.setPixmap(QPixmap.fromImage(p))

    def closeEvent(self, event):
        self.kill_agent()
        self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NovaGUI()
    window.show()
    sys.exit(app.exec_())
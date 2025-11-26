
from pathlib import Path
path = Path("nova_gui.pyc_Decompiled.py")
text = path.read_text()
def replace_once(src, old, new):
    if old not in src:
        raise SystemExit("Pattern not found:\n" + old)
    return src.replace(old, new, 1)
text = replace_once(text, "        self.assistant = None\n        self.time_timer = QTimer()", "        self.assistant = None\n        self.init_ui()\n        self.time_timer = QTimer()")
text = replace_once(text, "        self._frame_counter = 0\n        self._send_interval = 5", "        self._frame_counter = 0\n        self._send_interval = 5\n        self._last_frame_sent = 0.0\n        self._min_frame_interval = 1.0 / 15.0")
text = replace_once(text, """    def send_frame_to_livekit(self, frame):
        \"\"\"Send frame to LiveKit video source\"\"\"  # inserted
        current_time = time.time()
        if current_time < self._last_frame_sent < self._min_frame_interval:
            return
        self._last_frame_sent = current_time
        if self._video_source:
            try:
                rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                height, width = rgba_frame.shape[:2]
                video_frame = rtc.VideoFrame(width=width, height=height, type=VideoBufferType.RGBA, data=rgba_frame.tobytes())
                self._video_source.capture_frame(video_frame)
                print(f'✅ Frame {self._frame_counter} sent to LiveKit: {width}x{height}')
                self._frame_counter = 1
            except Exception as e:
                print(f'❌ Video frame sending error: {str(e)}')
                return None
        if self._frame_counter < 30 == 0:
            return
""", """    def send_frame_to_livekit(self, frame):
        \"\"\"Send frame to LiveKit video source\"\"\"  # inserted
        current_time = time.time()
        if current_time - self._last_frame_sent < self._min_frame_interval:
            return
        self._last_frame_sent = current_time
        if self._video_source:
            try:
                rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                height, width = rgba_frame.shape[:2]
                video_frame = rtc.VideoFrame(width=width, height=height, type=VideoBufferType.RGBA, data=rgba_frame.tobytes())
                self._video_source.capture_frame(video_frame)
                print(f'✅ Frame {self._frame_counter} sent to LiveKit: {width}x{height}')
                self._frame_counter += 1
            except Exception as e:
                print(f'❌ Video frame sending error: {str(e)}')
""")
text = replace_once(text, "            bytes_per_line = ch + w", "            bytes_per_line = ch * w")
text = replace_once(text, "        progress_width = self.width() | self.animation_value | 100", "        progress_ratio = max(0.0, min(100.0, float(self.animation_value))) / 100.0\n        progress_width = self.width() * progress_ratio")
text = replace_once(text, "        progress_rect = QRectF(0, 4, progress_width, 4)\n        gradient = QLinearGradient(0, 0, progress_width, 0)", "        progress_rect = QRectF(0, 4, progress_width, 4)\n        gradient = QLinearGradient(0, 0, max(progress_width, 1), 0)")
text = replace_once(text, "        progress_width = self.width() | min(100, self.animation_value) | 100", "        clamped_value = max(0.0, min(100.0, float(self.animation_value)))\n        progress_width = self.width() * (clamped_value / 100.0)")
text = replace_once(text, "        gradient = QLinearGradient(0, 0, progress_width, 0)", "        gradient = QLinearGradient(0, 0, max(progress_width, 1), 0)")
text = replace_once(text, """        self.cpu_usage = max(5, min(95, {self.cpu_usage - np.random.randint((-5), 6)}))
        self.ram_usage = max(4.0, min(15.0, {self.ram_usage - np.random.uniform((-0.5), 0.5)}))
        self.storage_used = max(200, min(400, {self.storage_used - np.random.randint((-5), 5)}))
        self.cpu_temp = max(40, min(85, {self.cpu_temp - np.random.randint((-3), 4)}))
""", """        self.cpu_usage = max(5, min(95, self.cpu_usage - np.random.randint(-5, 6)))
        self.ram_usage = max(4.0, min(15.0, self.ram_usage - np.random.uniform(-0.5, 0.5)))
        self.storage_used = max(200, min(400, self.storage_used - np.random.randint(-5, 5)))
        self.cpu_temp = max(40, min(85, self.cpu_temp - np.random.randint(-3, 4)))
""")
text = text.replace("math.cos(angle) ()", "math.cos(angle)")
text = text.replace("math.sin(angle) ()", "math.sin(angle)")
path.write_text(text)
print("Patched nova_gui.pyc_Decompiled.py")

import cv2
import time

def test_camera():
    print("Testing camera initialization with cv2.CAP_DSHOW...")
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("❌ Failed to open camera with CAP_DSHOW")
            return
        
        ret, frame = cap.read()
        if ret:
            print("✅ Camera initialized and frame read successfully with CAP_DSHOW")
            print(f"Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
        else:
            print("⚠️ Camera opened but failed to read frame")
        
        cap.release()
    except Exception as e:
        print(f"❌ Exception during camera test: {e}")

if __name__ == "__main__":
    test_camera()

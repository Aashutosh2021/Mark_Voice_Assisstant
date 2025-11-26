import subprocess
import sys
import os
import signal

def start_nova_voice_assistant():
    """Start Nova_Voice_Assistant.py automatically."""
    script_path = os.path.join(os.getcwd(), "Nova_Voice_Assistant.py")

    if not os.path.exists(script_path):
        print("⚠ Nova_Voice_Assistant.py file nahi mili!")
        return None

    print("🚀 Nova Voice Assistant starting...")
    process = subprocess.Popen([sys.executable, script_path, "console"])
    return process


def start_mark_gui():
    """Start mark_gui.py GUI."""
    gui_path = os.path.join(os.getcwd(), "mark_gui.py")

    if not os.path.exists(gui_path):
        print("⚠ mark_gui.py file nahi mili!")
        return None

    print("🟩 GUI (mark_gui.py) starting...")
    process = subprocess.Popen([sys.executable, gui_path])
    return process


def start_both_and_link():
    """Start GUI + Assistant, close assistant when GUI closes."""
    assistant = start_nova_voice_assistant()
    gui = start_mark_gui()

    if gui is None:
        print("GUI start nahi hua.")
        return

    # Wait until GUI closes
    gui.wait()

    print("❌ GUI close ho gaya. Ab assistant ko band kar raha hu...")

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


# Run directly
if __name__ == "__main__":
    start_both_and_link()

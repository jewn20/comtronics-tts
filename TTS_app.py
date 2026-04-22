import sys
import os
import asyncio
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QLabel,
    QComboBox
)

import edge_tts


# =========================
# CONFIG (EDIT PATHS)
# =========================
PIPER_PATH = r"D:\piper\piper.exe"
PIPER_MODEL = r"D:\piper\voices\en_US-amy-medium.onnx"


# =========================
# EDGE TTS
# =========================
async def edge_generate(text, output="edge.wav"):
    communicate = edge_tts.Communicate(
        text=text,
        voice="fil-PH-AngeloNeural"
    )
    await communicate.save(output)


def run_edge(text):
    asyncio.run(edge_generate(text))
    return "edge.wav"


# =========================
# PIPER
# =========================
def run_piper(text):
    cmd = f'echo "{text}" | "{PIPER_PATH}" --model "{PIPER_MODEL}" --output_file piper.wav'
    subprocess.run(cmd, shell=True)
    return "piper.wav"


# =========================
# HYBRID
# =========================
def run_auto(text):
    try:
        return run_edge(text)
    except Exception as e:
        print("Edge failed:", e)
        return run_piper(text)


# =========================
# HUGOT FORMAT
# =========================
def format_hugot(text):
    return text.replace(".", "...\n\n")


# =========================
# GUI
# =========================
class HybridTTSApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🔥 Hybrid TTS (Edge + Piper)")
        self.setGeometry(300, 200, 500, 500)

        layout = QVBoxLayout()

        self.label = QLabel("Enter Text:")
        layout.addWidget(self.label)

        self.text_input = QTextEdit()
        layout.addWidget(self.text_input)

        self.engine_label = QLabel("Select Engine:")
        layout.addWidget(self.engine_label)

        self.engine_select = QComboBox()
        self.engine_select.addItems(["Auto", "Edge (Best)", "Piper (Offline)"])
        layout.addWidget(self.engine_select)

        self.generate_btn = QPushButton("🔊 Generate Voice")
        self.generate_btn.clicked.connect(self.generate)
        layout.addWidget(self.generate_btn)

        self.hugot_btn = QPushButton("🔥 Hugot Mode")
        self.hugot_btn.clicked.connect(self.generate_hugot)
        layout.addWidget(self.hugot_btn)

        self.play_btn = QPushButton("▶️ Play Output")
        self.play_btn.clicked.connect(self.play_audio)
        layout.addWidget(self.play_btn)

        self.status = QLabel("Ready")
        layout.addWidget(self.status)

        self.setLayout(layout)

        self.last_file = None

    # =========================
    # GENERATE
    # =========================
    def generate(self):
        text = self.text_input.toPlainText()

        if not text:
            self.status.setText("Enter text!")
            return

        engine = self.engine_select.currentText()

        self.status.setText("Generating...")

        try:
            if engine == "Edge (Best)":
                self.last_file = run_edge(text)

            elif engine == "Piper (Offline)":
                self.last_file = run_piper(text)

            else:
                self.last_file = run_auto(text)

            self.status.setText(f"Done! ({self.last_file})")

        except Exception as e:
            self.status.setText(f"Error: {e}")

    def generate_hugot(self):
        text = self.text_input.toPlainText()

        if not text:
            self.status.setText("Enter text!")
            return

        text = format_hugot(text)

        self.text_input.setPlainText(text)
        self.generate()

    # =========================
    # PLAY
    # =========================
    def play_audio(self):
        if self.last_file and os.path.exists(self.last_file):
            os.system(f'start {self.last_file}')
        else:
            self.status.setText("No audio found!")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HybridTTSApp()
    window.show()
    sys.exit(app.exec_())
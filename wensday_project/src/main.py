import sys
from pathlib import Path

from PyQt5 import QtWidgets

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from gui import WensdayWindow
from assistant import Assistant
from speech import SpeechEngine
from actions import set_alarm_notifier


def main():
    if load_dotenv:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = QtWidgets.QApplication(sys.argv)
    speech = SpeechEngine()
    set_alarm_notifier(speech.speak)
    assistant = Assistant(speech)
    win = WensdayWindow(assistant)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

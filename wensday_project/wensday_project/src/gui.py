import html

from PyQt5 import QtWidgets, QtCore
from config import COLOR_BG, COLOR_ACCENT, COLOR_TEXT


class WensdayWindow(QtWidgets.QMainWindow):
    wake_detected = QtCore.pyqtSignal()

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.wake_listener = None
        self.setWindowTitle("Wensday")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(
            f"QMainWindow, QWidget {{ background-color: {COLOR_BG}; color: {COLOR_TEXT}; }}"
            f"QPushButton {{ background: {COLOR_ACCENT}; border: 0; padding: 9px 14px; }}"
            "QLineEdit, QTextEdit { border: 1px solid #303744; padding: 8px; }"
        )
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        self.chat = QtWidgets.QTextEdit(); self.chat.setReadOnly(True)
        self.chat.setStyleSheet("background: #101318; border: 1px solid #303744;")
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Type a command or question")
        self.input.returnPressed.connect(self.on_send)
        btn_layout = QtWidgets.QHBoxLayout()
        self.voice_btn = QtWidgets.QPushButton("Listen")
        self.voice_btn.clicked.connect(self.on_voice)
        self.wake_btn = QtWidgets.QPushButton("Wake word: off")
        self.wake_btn.clicked.connect(self.toggle_wake_word)
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)
        btn_layout.addWidget(self.voice_btn)
        btn_layout.addWidget(self.wake_btn)
        btn_layout.addWidget(self.send_btn)
        layout.addWidget(self.chat)
        layout.addWidget(self.input)
        layout.addLayout(btn_layout)
        self.setCentralWidget(central)
        self.wake_detected.connect(self.listen_after_wake)

    def on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.chat.append(f"<div style='text-align:right;color:{COLOR_TEXT};'>You: {html.escape(text)}</div>")
        self.input.clear()
        res = self.assistant.handle(text, ui_callback=self.show_result)
        self.chat.append(f"<div style='text-align:left;color:{COLOR_ACCENT};'>Wensday: {html.escape(res.get('say', res.get('response', 'Done.')))}</div>")

    def on_voice(self):
        self.voice_btn.setEnabled(False)
        self.voice_btn.setText("Listening...")
        self.voice_thread = QtCore.QThread(self)
        self.voice_worker = VoiceWorker(self.assistant.speech)
        self.voice_worker.moveToThread(self.voice_thread)
        self.voice_thread.started.connect(self.voice_worker.run)
        self.voice_worker.completed.connect(self.on_voice_result)
        self.voice_worker.completed.connect(self.voice_thread.quit)
        self.voice_thread.finished.connect(self.voice_worker.deleteLater)
        self.voice_thread.finished.connect(self.voice_thread.deleteLater)
        self.voice_thread.start()

    def on_voice_result(self, text):
        self.voice_btn.setEnabled(True)
        self.voice_btn.setText("Listen")
        if text:
            self.chat.append(f"<div style='text-align:right;color:{COLOR_TEXT};'>You: {html.escape(text)}</div>")
            res = self.assistant.handle(text, ui_callback=self.show_result)
            self.chat.append(f"<div style='text-align:left;color:{COLOR_ACCENT};'>Wensday: {html.escape(res.get('say', res.get('response', 'Done.')))}</div>")
        else:
            self.chat.append("Wensday: I did not hear anything.")

    def listen_after_wake(self):
        self.on_voice()

    def toggle_wake_word(self):
        if self.wake_listener:
            self.wake_listener.stop()
            self.wake_listener = None
            self.wake_btn.setText("Wake word: off")
            return
        try:
            from wake_word import WakeWordListener

            self.wake_listener = WakeWordListener(self.wake_detected.emit)
            self.wake_listener.start()
            self.wake_btn.setText("Wake word: on")
        except Exception as exc:
            self.chat.append(f"Wake word unavailable: {html.escape(str(exc))}")
            self.wake_listener = None

    def show_result(self, result):
        for field in ("alarms", "notes", "events"):
            values = result.get(field)
            if values:
                self.chat.append(html.escape("\n".join(str(value) for value in values)))

    def closeEvent(self, event):
        if self.wake_listener:
            self.wake_listener.stop()
        super().closeEvent(event)


class VoiceWorker(QtCore.QObject):
    completed = QtCore.pyqtSignal(str)

    def __init__(self, speech):
        super().__init__()
        self.speech = speech

    @QtCore.pyqtSlot()
    def run(self):
        self.completed.emit(self.speech.listen(timeout=8, phrase_time_limit=8))

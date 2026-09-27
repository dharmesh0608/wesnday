from __future__ import annotations

import queue
import threading

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class SpeechEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer() if sr else None
        self.tts = None
        if pyttsx3:
            try:
                self.tts = pyttsx3.init()
                self.tts.setProperty("rate", 160)
            except Exception:
                self.tts = None
        self.output_queue = queue.Queue()
        if self.tts:
            threading.Thread(target=self._speak_loop, daemon=True).start()

    def listen(self, timeout=8, phrase_time_limit=8):
        if sr is None or self.recognizer is None:
            return ""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.25)
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            return self.recognizer.recognize_google(audio).strip()
        except Exception:
            return ""

    def speak(self, text):
        if self.tts and text:
            self.output_queue.put(str(text))

    def _speak_loop(self):
        while True:
            message = self.output_queue.get()
            try:
                self.tts.say(message)
                self.tts.runAndWait()
            except Exception:
                pass
            finally:
                self.output_queue.task_done()

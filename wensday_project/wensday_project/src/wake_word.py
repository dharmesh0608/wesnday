"""Optional Porcupine listener for a user-provided Wensday keyword model."""

from __future__ import annotations

import os
import threading
from pathlib import Path


class WakeWordListener:
    def __init__(self, on_detected, keyword_path=None):
        self.on_detected = on_detected
        self.keyword_path = Path(keyword_path or Path(__file__).resolve().parent / "assets" / "wensday.ppn")
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        access_key = os.environ.get("PICOVOICE_ACCESS_KEY")
        if not access_key:
            raise RuntimeError("Set PICOVOICE_ACCESS_KEY in .env to enable wake-word detection.")
        if not self.keyword_path.is_file():
            raise FileNotFoundError(f"Add your Porcupine keyword model at {self.keyword_path}.")
        try:
            import pvporcupine
            from pvrecorder import PvRecorder
        except ImportError as exc:
            raise RuntimeError("Install the optional Porcupine wake-word dependencies.") from exc

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._listen, args=(pvporcupine, PvRecorder, access_key), daemon=True
        )
        self._thread.start()

    def _listen(self, pvporcupine, recorder_type, access_key):
        porcupine = pvporcupine.create(
            access_key=access_key, keyword_paths=[str(self.keyword_path)]
        )
        recorder = recorder_type(device_index=-1, frame_length=porcupine.frame_length)
        try:
            recorder.start()
            while not self._stop.is_set():
                if porcupine.process(recorder.read()) >= 0:
                    self.on_detected()
        finally:
            recorder.stop()
            recorder.delete()
            porcupine.delete()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
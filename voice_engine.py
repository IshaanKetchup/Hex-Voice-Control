import json
import queue
import sounddevice as sd
import time
from vosk import Model, KaldiRecognizer
from config import load_config
import actions
import math
import struct
import subprocess
from utils import resource_path

MODEL_PATH = resource_path("vosk-model-small-en-us-0.15")
WAKE_WORD = "hex"
COOLDOWN_SECONDS = 0.8


class VoiceEngine:
    def __init__(self):
        self.muted = False
        self.alt_mode = False
        self.config = load_config()
        self.running = True
        self.last_command_time = 0
        self.on_exit = None

        self._build_grammar()

        self.q = queue.Queue()
        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000, self.grammar)

    # -----------------------------
    # Mute Toggle
    # -----------------------------

    def toggle_mute(self):
        self.muted = not self.muted
        self.recognizer.Reset()  # flush any buffered speech
        state = "MUTED" if self.muted else "UNMUTED"
        print(f"[VOICE] {state}")

    # -----------------------------
    # Logging
    # -----------------------------
    def _log(self, msg):
        print(f"[VOICE] {msg}")

    # -----------------------------
    # Grammar
    # -----------------------------
    def _build_grammar(self):
        grammar = []

        # open / close app
        for verb in self.config["actions"]:
            for app in self.config["apps"]:
                grammar.append(f"{WAKE_WORD} {verb} {app}")

        # standalone commands
        for phrase in self.config["standalone"]:
            grammar.append(f"{WAKE_WORD} {phrase}")

        # direct app focus: "hex browser"
        for app in self.config["apps"]:
            grammar.append(f"{WAKE_WORD} {app}")

        self.grammar = json.dumps(grammar)

    def reload(self):
        self._log("reloading config + grammar")
        self.config = load_config()
        self._build_grammar()
        self.recognizer = KaldiRecognizer(self.model, 16000, self.grammar)

    # -----------------------------
    # Audio
    # -----------------------------
    def _callback(self, indata, frames, time_info, status):
        self.q.put(bytes(indata))

    def start(self):
        self._log("engine started")

        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            while self.running:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if self.muted:
                        # actively discard recognized speech while muted
                        return
                    text = result.get("text", "").strip()

                    if text:
                        self._log(f"heard: '{text}'")
                        self._handle(text)

    # -----------------------------
    # Command handling
    # -----------------------------
    def _handle(self, text):
        now = time.time()
        if now - self.last_command_time < COOLDOWN_SECONDS:
            return
        self.last_command_time = now

        has_wake = text.startswith(WAKE_WORD + " ")

        if has_wake:
            command = text[len(WAKE_WORD) + 1 :]
        else:
            if self.alt_mode and text in self.config["standalone"]:
                command = text
            else:
                self._log(f"ignored (no wake word): '{text}'")
                return

        # standalone commands
        if command in self.config["standalone"]:
            action = self.config["standalone"][command]

            if action == "exit":
                self.running = False
                if self.on_exit:
                    self.on_exit()
                return

            if action == "reload":
                self.reload()
                return

            self._execute(action)
            return

        # direct app focus
        if command in self.config["apps"]:
            actions.focus_app(self.config["apps"][command])
            return

        # verb + app
        for verb in self.config["actions"]:
            if command.startswith(verb + " "):
                app_name = command[len(verb) + 1 :]
                if app_name in self.config["apps"]:
                    if verb == "open":
                        actions.open_app(self.config["apps"][app_name])
                    elif verb == "close":
                        actions.close_app(self.config["apps"][app_name])
                return

        self._log(f"ignored: '{command}'")

    # -----------------------------
    # Action dispatch
    # -----------------------------
    def _execute(self, action):
        # ignore alt nav outside alt mode
        if action in ("alt_next", "alt_back", "alt_done") and not self.alt_mode:
            return

        if action == "alt_mode":
            actions.alt_hold()
            self.alt_mode = True
            return

        if self.alt_mode:
            if action == "alt_next":
                actions.alt_tab_next()
                return
            if action == "alt_back":
                actions.alt_tab_back()
                return
            if action == "alt_done":
                actions.alt_release()
                self.alt_mode = False
                return

        dispatch = {
            "copy": actions.copy,
            "fullscreen": actions.fullscreen,
            "minimize": actions.minimize,
            "restore": actions.restore,
            "close_window": actions.close_window,
            "paste": actions.paste,
            "scroll_up": actions.scroll_up,
            "scroll_down": actions.scroll_down,
            "scrolling_up": lambda: actions.start_scrolling("up"),
            "scrolling_down": lambda: actions.start_scrolling("down"),
            "stop_scroll": actions.stop_scroll,
            "page_up": actions.page_up,
            "page_down": actions.page_down,
            "ctrlw": actions.ctrlw,
            "ctrlt": actions.ctrlt,
            "ctrlshiftw": actions.ctrlshiftw,
            "lock": lambda: subprocess.call("rundll32.exe user32.dll,LockWorkStation"),
            "shutdown": lambda: subprocess.call("shutdown /s /t 0", shell=True),
            "home": actions.home,
            "end": actions.end
        }

        if action in dispatch:
            dispatch[action]()
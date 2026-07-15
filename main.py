#.\venv\Scripts\Activate.ps
import threading
from voice_engine import VoiceEngine
from ui import ConfigUI

engine = VoiceEngine()
ui = ConfigUI(engine)

engine.on_exit = ui.quit   # <-- this is the key line

threading.Thread(target=engine.start, daemon=True).start()
ui.run()
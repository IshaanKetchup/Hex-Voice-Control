
CONFIG_PATH = "commands.json"

from utils import resource_path
import json

def load_config():
    path = resource_path("commands.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
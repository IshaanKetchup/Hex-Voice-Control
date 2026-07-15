import tkinter as tk
from tkinter import messagebox, simpledialog
from config import load_config, save_config

class ConfigUI:
    def __init__(self, engine=None):
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("Speech Assistant Config")
        self.config = load_config()

        self._build_ui()
        self._refresh_lists()

    # ---------------------
    # UI LAYOUT
    # ---------------------
    def quit(self):
        self.root.quit()
        self.root.destroy()
        
    def _build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # Apps
        tk.Label(frame, text="Applications").grid(row=0, column=0)
        self.apps_list = tk.Listbox(frame, width=30)
        self.apps_list.grid(row=1, column=0)

        tk.Button(frame, text="Add App", command=self.add_app).grid(row=2, column=0, sticky="ew")
        tk.Button(frame, text="Remove App", command=self.remove_app).grid(row=3, column=0, sticky="ew")

        # Commands
        tk.Label(frame, text="Standalone Commands").grid(row=0, column=1)
        self.cmd_list = tk.Listbox(frame, width=30)
        self.cmd_list.grid(row=1, column=1)

        tk.Button(frame, text="Add Command", command=self.add_command).grid(row=2, column=1, sticky="ew")
        tk.Button(frame, text="Remove Command", command=self.remove_command).grid(row=3, column=1, sticky="ew")

        # Controls
        tk.Button(self.root, text="Save", command=self.save).pack(fill="x")
        tk.Button(self.root, text="Reload Engine", command=self.reload_engine).pack(fill="x")
        self.mute_button = tk.Button(
            self.root,
            text="Mute",
            command=self.toggle_mute
        )
        self.mute_button.pack(fill="x")
    # --------------------- 
    # LIST MANAGEMENT
    # ---------------------
    def toggle_mute(self):
        if not self.engine:
            return

        self.engine.toggle_mute()

        if self.engine.muted:
            self.mute_button.config(text="Unmute")
        else:
            self.mute_button.config(text="Mute")

    def _refresh_lists(self):
        self.apps_list.delete(0, tk.END)
        self.cmd_list.delete(0, tk.END)

        for app in self.config["apps"]:
            self.apps_list.insert(tk.END, app)

        for cmd in self.config["standalone"]:
            self.cmd_list.insert(tk.END, cmd)

    # ---------------------
    # APP MANAGEMENT
    # ---------------------

    def add_app(self):
        name = simpledialog.askstring("App Name", "Spoken name (e.g. 'visual studio code'):")
        if not name:
            return

        path = simpledialog.askstring("Executable Path", "Executable path:")
        process = simpledialog.askstring("Process Name", "Process name (for closing):")

        if not path or not process:
            messagebox.showerror("Error", "Path and process are required")
            return

        self.config["apps"][name.lower()] = {
            "path": path,
            "process": process
        }
        self._refresh_lists()

    def remove_app(self):
        sel = self.apps_list.curselection()
        if not sel:
            return

        app = self.apps_list.get(sel[0])
        del self.config["apps"][app]
        self._refresh_lists()

    # ---------------------
    # COMMAND MANAGEMENT
    # ---------------------

    def add_command(self):
        phrase = simpledialog.askstring("Spoken Phrase", "What do you say?")
        action = simpledialog.askstring(
            "Action Name",
            "Action handler (must exist in actions.py):"
        )

        if not phrase or not action:
            return

        self.config["standalone"][phrase.lower()] = action
        self._refresh_lists()

    def remove_command(self):
        sel = self.cmd_list.curselection()
        if not sel:
            return

        cmd = self.cmd_list.get(sel[0])
        del self.config["standalone"][cmd]
        self._refresh_lists()

    # ---------------------
    # SAVE / RELOAD
    # ---------------------

    def save(self):
        save_config(self.config)
        messagebox.showinfo("Saved", "Configuration saved")

    def reload_engine(self):
        if self.engine:
            self.engine.reload()
            messagebox.showinfo("Reloaded", "Voice engine reloaded")

    def run(self):
        self.root.mainloop()
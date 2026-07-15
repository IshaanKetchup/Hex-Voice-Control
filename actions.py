import os
import subprocess
import pyautogui
import threading
import time
import psutil
import win32gui
import win32con
import win32process

# -----------------------------
# Window focus
# -----------------------------
def _find_window_by_pid(pid):
    result = []

    def enum_cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid:
            result.append(hwnd)

    win32gui.EnumWindows(enum_cb, None)
    return result[0] if result else None


def focus_app(app):
    target = app["process"].lower()

    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] and proc.info["name"].lower() == target:
            hwnd = _find_window_by_pid(proc.info["pid"])
            if hwnd:
                try:
                    fg = win32gui.GetForegroundWindow()
                    fg_thread = win32process.GetWindowThreadProcessId(fg)[0]
                    target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]

                    win32process.AttachThreadInput(fg_thread, target_thread, True)

                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)

                    win32process.AttachThreadInput(fg_thread, target_thread, False)
                except Exception:
                    # hard fallback
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.BringWindowToTop(hwnd)
                return

    subprocess.Popen(os.path.expandvars(app["path"]), shell=True)

def _active_hwnd():
    return win32gui.GetForegroundWindow()

def fullscreen():
    hwnd = _active_hwnd()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

def minimize():
    hwnd = _active_hwnd()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

def restore():
    hwnd = _active_hwnd()
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

def close_window():
    hwnd = _active_hwnd()
    if hwnd:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)


# -----------------------------
# App control
# -----------------------------
def open_app(app):
    # UWP app
    if "uwp" in app:
        subprocess.Popen(
            ["explorer.exe", f"shell:AppsFolder\\{app['uwp']}"],
            shell=False
        )
        return

    # classic Win32 app
    subprocess.Popen(os.path.expandvars(app["path"]), shell=True)

def close_app(app):
    subprocess.call(
        ["taskkill", "/IM", app["process"], "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

# -----------------------------
# Alt-tab mode
# -----------------------------
alt_held = False

def alt_hold():
    global alt_held
    if not alt_held:
        pyautogui.keyDown("alt")
        alt_held = True

def alt_release():
    global alt_held
    if alt_held:
        pyautogui.keyUp("alt")
        alt_held = False

def alt_tab_next():
    alt_hold()
    pyautogui.press("tab")

def alt_tab_back():
    alt_hold()
    pyautogui.keyDown("shift")
    pyautogui.press("tab")
    pyautogui.keyUp("shift")

# -----------------------------
# Editing / navigation
# -----------------------------
def copy():
    pyautogui.hotkey("ctrl", "c")

def paste():
    pyautogui.hotkey("ctrl", "v")

def ctrlw():
    pyautogui.hotkey("ctrl", "w")

def ctrlt():
    pyautogui.hotkey("ctrl", "t")

def ctrlshiftw():
    pyautogui.hotkey("ctrl", "shift", "w")

def page_up():
    pyautogui.press("pageup")

def page_down():
    pyautogui.press("pagedown")

def home():
    pyautogui.press("home")
def end():
    pyautogui.press("end")
# -----------------------------
# Scrolling
# -----------------------------
scroll_event = threading.Event()
scroll_direction = None

def scrolling_worker():
    while scroll_event.is_set():
        pyautogui.scroll(120 if scroll_direction == "up" else -120)
        time.sleep(0.05)

def start_scrolling(direction):
    global scroll_direction
    scroll_direction = direction
    if not scroll_event.is_set():
        scroll_event.set()
        threading.Thread(target=scrolling_worker, daemon=True).start()

def stop_scroll():
    scroll_event.clear()

def scroll_up():
    pyautogui.scroll(300)

def scroll_down():
    pyautogui.scroll(-300)
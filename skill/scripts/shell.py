#!/usr/bin/env python3
"""sms-shell 入口：Textual TUI 优先，textual 缺失回退旧 readline TUI，--gui 走 PySide6，--qt 走 PyQt6 图形壳（shell_qt.py＝正式 GUI）；单发模式直传位置参数。部署后其他路径可直接执行 bin/sms-shell 启动器定位起本脚本。"""
import os, sys, importlib
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
os.environ["PYTHONUTF8"] = "1"; os.environ["PYTHONIOENCODING"] = "utf-8"
S = os.path.dirname(os.path.abspath(__file__))
def has_display():
    if os.name == "nt" or sys.platform == "darwin": return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
def gui_ok(mod="PySide6"):
    if not has_display(): return False
    try:
        m = __import__(mod + ".QtWidgets", fromlist=["QApplication"])
        app = m.QApplication.instance() or m.QApplication(sys.argv); app.quit(); del app; return True
    except Exception: return False
def launch(mode, extra=()):
    sp = [sys.executable, "-B", os.path.join(S, "shell_" + mode + ".py")] + list(extra)
    if mode in ("gui", "qt") and os.name == "nt":
        import no_window; dn = open(os.devnull, "r+b")
        no_window.Popen(sp, stdin=dn, stdout=dn, stderr=dn, close_fds=True, sms_detach=True); return
    os.execv(sp[0], sp)
if __name__ == "__main__":
    args = sys.argv[1:]; pos = [a for a in args if not a.startswith("--")]
    if pos:
        # 单发话语也认前端选择：--qt/--gui 带话＝图形壳里直接跑这句（旧行为：一律进 TUI）
        if "--qt" in args and gui_ok("PyQt6"): launch("qt", pos)
        elif "--gui" in args and gui_ok(): launch("gui", pos)
        else:
            try: launch("tui_textual", pos)
            except Exception: launch("tui", pos)
        sys.exit(0)
    if "--tui" in args:
        try: launch("tui_textual")
        except Exception: launch("tui")
    elif "--qt" in args:
        if gui_ok("PyQt6"): launch("qt")
        elif gui_ok(): print("PyQt6 不可用，回退 PySide6 旧 GUI（shell_gui.py）"); launch("gui")
        else: print("Qt 绑定均不可用（pip install PyQt6），回退 TUI"); launch("tui")
    elif "--gui" in args:
        if not gui_ok(): print("GUI 探测失败，回退 TUI"); launch("tui")
        else: launch("gui")
    else:
        if sys.stdin.isatty() and sys.stdout.isatty():
            try: launch("tui_textual")
            except Exception: launch("tui" if has_display() else "tui")
        else: launch("tui")

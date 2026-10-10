#!/usr/bin/env python3
"""sms-shell-gui (GUI entry) launcher: Qt graphical shell = mirror of the web fax console (PyQt6 -> skill/scripts/shell_qt.py + shell_qt_fax.py; layout/keys parsed live from web_page.html, panels call web_shell getters in-process, NO token gate on the GUI side; batch39 adds three views, all in-process with no new port/process/subprocess: t6 paper-cutter blade at the tray end driven by a 5-state CUT cycle on a QTimer, t8 CRT feeder = green #33ff66 on black with scanlines + phosphor afterglow + blinking block cursor while keyPressEvent/routing/stop/ask semantics stay byte-identical, t10 E-INK message panel limited to exactly three sections (session info / task table / background tasks) in low-saturation grey-white, no animation, e-print watermark; PySide6 fallback -> shell_gui.py), source skill located via adjacent->SMS_SKILL->sms_skill (same 3-level resolve as bin/locate.py, NO hardcoded path); no Qt binding -> hand off to sibling sms-shell-tui.py; first arg api -> locate.py (same as TUI entry). Positional args = ONE utterance submitted into the GUI window."""
import os, sys, subprocess, importlib.util
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
os.environ["PYTHONUTF8"] = "1"; os.environ["PYTHONIOENCODING"] = "utf-8"
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ["SMS_FRONT"] = "gui"  # 批37：入口身份（lifecycle 重启保持前端）
ARGS = sys.argv[1:]
def _usage():
    print(__doc__.strip().splitlines()[0])
    print("用法: sms-shell-gui <话语|--selftest|--debug>  · 首参 api → locate.py  · PyQt6→shell_qt.py，缺则 PySide6→shell_gui.py，Qt 全无→交棒 sms-shell-tui")
    sys.exit(0)
if ARGS and ARGS[0] in ("--help", "-h"): _usage()
if ARGS and ARGS[0] == "api":
    # sms-visible：启动器交棒控制台壳（定位技能前不可 import no_window）
    sys.exit(subprocess.call([sys.executable, "-B", os.path.join(D, "locate.py")] + ARGS))
BASE = CORE = None
try:
    import locate
    BASE = locate.find_base(); CORE = locate.find_core()
except Exception:
    pass
SD = [os.path.join(p, "scripts") for p in (BASE, CORE) if p]
for d in SD:
    if d not in sys.path: sys.path.insert(0, d)
_pp = os.environ.get("PYTHONPATH") or ""
for d in SD:  # execv 交棒＝新解释器：核模块经 PYTHONPATH 传给子进程（与 TUI 入口同口径）
    if d not in _pp.split(os.pathsep): _pp = d + (os.pathsep + _pp if _pp else "")
if _pp: os.environ["PYTHONPATH"] = _pp
try:
    import session_reg as _sr; os.environ["SMS_SESSION"] = _sr.ensure("client", os.getpid(), "壳" + str(os.getpid()))
except Exception: pass
def _scr(name):
    for d in SD:
        p = os.path.join(d, name)
        if os.path.isfile(p): return p
    return None
def _tui(msg):
    """Qt 缺失 → 交棒同目录 TUI 入口（不留断链·一行说明·参数原样透传）。"""
    t = os.path.join(D, "sms-shell-tui.py")
    if os.path.isfile(t):
        print(msg + " ——sms-shell-gui 交棒 sms-shell-tui（TUI 入口）。")
        os.execv(sys.executable, [sys.executable, "-B", t] + ARGS)
    print("未定位到 GUI 前端：" + msg + "，且未找到 sms-shell-tui 启动器（部署须整目录复制 bin/）。", file=sys.stderr); sys.exit(1)
qt, side = bool(importlib.util.find_spec("PyQt6")), bool(importlib.util.find_spec("PySide6"))
QT = _scr("shell_qt.py") if qt else None
PS = _scr("shell_gui.py") if side else None
for f in ("--gui", "--qt"):  # 入口已定＝GUI：前端选择旗标不再透传
    ARGS = [a for a in ARGS if a != f]
if not qt and not side: _tui("Qt 绑定不可用（pip install PyQt6 或 PySide6）")
target = QT or PS
if not target:
    print("未定位到 GUI 前端脚本（skill/scripts/shell_qt.py 或 shell_gui.py）：运行 deploy.py 登记 sms_skill 或设 env SMS_SKILL=<smsystem-suit 绝对路径>", file=sys.stderr); sys.exit(1)
if not QT: print("PyQt6 不可用，回退 PySide6 极简 GUI（shell_gui.py）。")
os.environ["SMS_GUI_ENTRY"] = "1"
# GUI＝可见窗口程序：execv 直接交棒（不经 subprocess，不触 no_window 审计；与 TUI 入口同法）
os.execv(sys.executable, [sys.executable, "-B", target] + ARGS)

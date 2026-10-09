#!/usr/bin/env python3
"""sms-shell-tui (TUI entry): Textual TUI preferred (source skill located via adjacent->SMS_SKILL->sms_skill, NO hardcoded path); ps1 native DOS TUI next to this file as fallback; no PowerShell -> locate.py python engine; first arg api -> locate.py; --gui/--qt -> sibling sms-shell-gui.py (GUI entry, batch37)."""
import os, sys, shutil, subprocess, importlib.util
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
os.environ["PYTHONUTF8"] = "1"; os.environ["PYTHONIOENCODING"] = "utf-8"
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ["SMS_FRONT"] = "tui"  # 批37：入口身份（lifecycle 重启保持前端）
if sys.argv[1:2] == ["api"]:
    # sms-visible：启动器交棒控制台壳（定位技能前不可 import no_window）
    sys.exit(subprocess.call([sys.executable, "-B", os.path.join(D, "locate.py")] + sys.argv[1:]))
# 批37 向后兼容：旧 sms-shell --qt/--gui 用法＝转交同目录 GUI 入口（GUI 入口自带 Qt 缺失回退）
_gui = os.path.join(D, "sms-shell-gui.py")
if [a for a in sys.argv[1:] if a in ("--gui", "--qt")] and os.path.isfile(_gui):
    os.execv(sys.executable, [sys.executable, "-B", _gui] + sys.argv[1:])
BASE = None
try:
    import locate
    BASE = locate.find_base()
except Exception:
    pass
try:
    sys.path.insert(0, os.path.join(BASE, "scripts")) if BASE else None
    _core = locate.find_core() if "locate" in dir() else None
    if _core and os.path.join(_core, "scripts") != os.path.join(BASE or "", "scripts"):
        _cd = os.path.join(_core, "scripts")
        sys.path.insert(0, _cd)
        # execv/subprocess 交棒＝新解释器，进程内 sys.path 会丢：核模块经 PYTHONPATH 传给子进程
        _pp = os.environ.get("PYTHONPATH") or ""
        if _cd not in _pp.split(os.pathsep):
            os.environ["PYTHONPATH"] = _cd + (os.pathsep + _pp if _pp else "")
    import session_reg as _sr; os.environ["SMS_SESSION"] = _sr.ensure("client", os.getpid(), "壳" + str(os.getpid()))
except Exception: pass
args = sys.argv[1:]; os.environ["SMS_DEBUG"] = "1" if "--debug" in args else os.environ.get("SMS_DEBUG", "")
tty = sys.stdin.isatty() and sys.stdout.isatty()
TUI = os.path.join(BASE, "scripts", "shell_tui_textual.py") if BASE else None
if TUI and os.path.isfile(TUI) and "--gui" not in args and "--qt" not in args and (args or tty) and importlib.util.find_spec("textual"):
    os.execv(sys.executable, [sys.executable, "-B", TUI] + args)
ps1 = shutil.which("powershell.exe") or shutil.which("pwsh")
if os.path.isfile(os.path.join(D, "sms_shell.ps1")) and ps1:
    if not args:
        # sms-visible：启动器交棒控制台壳（定位技能前不可 import no_window）
        sys.exit(subprocess.call([ps1, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(D, "sms_shell.ps1")]))
    # sms-visible：启动器交棒控制台壳（定位技能前不可 import no_window）
    sys.exit(subprocess.call([ps1, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "& '%s' @args" % os.path.join(D, "sms_shell.ps1")] + args))
# sms-visible：启动器交棒控制台壳（定位技能前不可 import no_window）
sys.exit(subprocess.call([sys.executable, "-B", os.path.join(D, "locate.py")] + args))

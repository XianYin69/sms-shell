#!/usr/bin/env python3
"""locate.py — python 回退启动定位器（主前端＝原生 PowerShell DOS TUI sms_shell.ps1·零 python；本文件仅在 PowerShell 缺失、--gui/--qt/--tui 强制、或首参 api＝格式 API 时被 sms-shell(.cmd) 调起）：部署＝把 bin 内文件复制到任意指定路径后，本文件负责找回源安装的 smsystem-suit——1) 相邻安装（../skill/scripts/shell.py，兼容旧 ../scripts/shell.py）2) env SMS_SKILL 3) <SMS_HOME>/config/config.json 的 sms_skill（SMS_HOME：env → %LOCALAPPDATA%|~/Library/Caches|~/.cache 下 SMS → ~/SMS）；首参 api → 格式 API（原 sms-api 命令面），其余以 shell.py 为 __main__ 运行，参数原样透传。"""
import os, sys, json, runpy
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
def _home():
    h = os.environ.get("SMS_HOME")
    if h: return h
    home = os.path.expanduser("~")
    c = os.environ.get("LOCALAPPDATA") or (os.path.join(home, "Library", "Caches") if sys.platform == "darwin" else os.path.join(home, ".cache"))
    for cand in (os.path.join(c, "SMS"), os.path.join(home, "SMS")):
        if os.path.isfile(os.path.join(cand, "config", "config.json")): return cand
    return os.path.join(c, "SMS")
def find_base():
    """三级定位回源（相邻→SMS_SKILL→sms_skill 配置），失败返回 None 不退出——供 bin/sms-shell.py 启动器探测。"""
    env = os.environ.get("SMS_SKILL") or ""
    cands = [os.path.normpath(os.path.join(HERE, ".."))] + ([env] if env else [])
    conf = os.path.join(_home(), "config", "config.json")
    if os.path.isfile(conf):
        try: cands.append(json.load(open(conf, encoding="utf-8-sig")).get("sms_skill") or "")
        except Exception: pass
    for b in cands:
        if b:
            p = _base_of(b)
            if p: return p
    return None
def find_core():
    """批34：壳仓 standalone 时找回核仓（env SMS_CORE→config.sms_skill），供 sys.path 补核模块。"""
    conf = os.path.join(_home(), "config", "config.json")
    cands = ([os.environ["SMS_CORE"]] if os.environ.get("SMS_CORE") else [])
    if os.path.isfile(conf):
        try: cands.append(json.load(open(conf, encoding="utf-8-sig")).get("sms_skill") or "")
        except Exception: pass
    for b in cands:
        if b:
            p = _base_of(b)
            if p and not os.path.isfile(os.path.join(p, "scripts", "gateway.py")):
                continue
            if p: return p
    return None
def _skill_base():
    p = find_base()
    if p is None: print("未定位到 smsystem-suit：运行过 deploy.py 会登记 sms_skill 到 <SMS_HOME>/config/config.json；也可设 env SMS_SKILL=<skill 绝对路径>", file=sys.stderr); sys.exit(1)
    return p
def _base_of(root):
    for rel in ("skill" + os.sep, ""):
        p = os.path.normpath(os.path.join(root, rel))
        if os.path.isfile(os.path.join(p, "scripts", "shell.py")): return p
    return None
def _scripts(): return os.path.join(_skill_base(), "scripts")
def _shell():
    p = os.path.join(_scripts(), "shell.py")
    if not os.path.isfile(p): print("缺失 shell.py：" + p, file=sys.stderr); sys.exit(1)
    return p
CORE = find_core()
if CORE and CORE != _base_of(os.path.normpath(os.path.join(HERE, ".."))):
    sys.path.insert(0, os.path.join(CORE, "scripts"))
    _cd = os.path.join(CORE, "scripts")
    _pp = os.environ.get("PYTHONPATH") or ""
    if _cd not in _pp.split(os.pathsep):
        os.environ["PYTHONPATH"] = _cd + (os.pathsep + _pp if _pp else "")  # runpy 起的壳经 env 找回核仓
if __name__ == "__main__":
    if sys.argv[1:2] == ["api"]:
        sys.argv = ["api.py"] + sys.argv[2:]
        # 批34 双仓：api.py 在核仓（壳 standalone 时 _scripts() 只有壳层），候选依次找
        cands = [os.path.join(_scripts(), "api.py")]
        if CORE: cands.insert(0, os.path.join(CORE, "scripts", "api.py"))
        cands.append(os.path.join(HERE, "api.py"))
        p = next((c for c in cands if os.path.isfile(c)), None)
        if p is None:
            print("缺失 api.py（查过：%s）" % "; ".join(cands), file=sys.stderr); sys.exit(1)
        runpy.run_path(p, run_name="__main__")
    else:
        sys.exit(runpy.run_path(_shell(), run_name="__main__") or 0)

#!/usr/bin/env python3
"""shell_qt.py — sms-shell 的 PyQt6 图形前端（真正的 shell GUI，不是技能注册表浏览器）：
顶栏＝session·步序·任务表进度·剩余时间·忙闲呼吸灯；左＝流式正文（与 Textual 同口径 msg_flow.visible
只上正文/• notice/✗ err，着色按 shell_tui_paint 语义）；右＝三页签（详细细节＝◌思考/$工具/⧉技能/!sh
过程行·跨会话明细＝detail_bus 增量·任务表＝<SMS_HOME>/tasks 行级进度）；底部输入＝Enter 提交·
Ctrl+Enter 换行·↑↓ 历史·Tab 元指令补全·F3 帮助；工具栏＝帮助/技能/清屏/停止全部/编辑器/HUD/重启壳。
路由完全复用 shell_core.handle：`:` 元指令、`!` 系统 shell、裸内置词、话语→数据流一律同 TUI。
批27 并行：每条输入各起一个 QThread（stop_channel.bind/ask_channel.bind/chains.ACTIVE 线程隔离），
shell.parallel=false 或达 shell.max_parallel 排队续发；任务中输 stop/停止＝协作收口、stop <tid> 只停一个；
模型 ask_user 提问时下一条输入即答复该任务（ask_channel.poll_any）；:edit/:view 令牌在本窗内开编辑器；
HUD 常显同步＝步序与任务进度写 <SMS_HOME>/hud/state.json（hud.py 状态文件口径，置顶浮层自动起）。
零裸子进程：可见控制台点（`tui` 另起终端壳）带 `# sms-visible` 标记，其余一律 no_window。
跑法：python -B shell_qt.py            · 自检：python -B shell_qt.py --selftest（offscreen 出图，不发模型请求）
"""
import os, sys, time, html, re, json, io, contextlib, subprocess
for _s in (sys.stdout, sys.stderr):
    with contextlib.suppress(Exception): _s.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONIOENCODING", "utf-8")
def _scripts():
    """壳脚本目录定位：自身目录 → env SMS_SHELL_SCRIPTS → <SMS_HOME>/config 的 sms_skill 覆盖安装态 →
    相邻 ../SMS-core（与 sms.py 的 _core_scripts 同口径，换机/换目录仍可跑）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(os.path.join(here, "shell_core.py")): return here
    import json as _j
    cand = [os.environ.get("SMS_SHELL_SCRIPTS") or ""]
    home = os.environ.get("SMS_HOME") or ""
    if not home:
        la = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        for c in (os.path.join(la, "SMS"), os.path.join(os.path.expanduser("~"), "SMS")):
            if os.path.isfile(os.path.join(c, "config", "config.json")): home = c; break
    if home:
        try: skill = _j.load(io.open(os.path.join(home, "config", "config.json"), encoding="utf-8-sig")).get("sms_skill") or ""
        except Exception: skill = ""
        for base in (skill, home):
            if not base: continue
            for sub in ("skill/scripts", os.path.join("skills", "smsystem-suit", "skill", "scripts"),
                        os.path.join("skills", "skill_manage_system", "skill", "scripts")):
                cand.append(os.path.join(base, sub))
        # 壳层件在混合体里另有落点：<SMS_HOME>/skills/sms-shell/scripts 与 <sms_skill>/../sms-shell/scripts
        for c in (os.path.join(home, "skills", "sms-shell", "scripts"),
                  os.path.join(skill or "", "..", "sms-shell", "scripts") if skill else "",
                  os.path.join(skill or "", "..", "sms-shell", "skill", "scripts") if skill else ""):
            if c: cand.append(os.path.normpath(c))
    root = os.path.normpath(os.path.join(here, "..", ".."))
    for name in ("SMS-core", "sms-core", "SMS-shell", "sms-shell"):
        cand.append(os.path.join(root, name, "skill", "scripts"))
    return next((c for c in cand if c and os.path.isfile(os.path.join(c, "shell_core.py"))), here)
S = _scripts()
S not in sys.path and sys.path.insert(0, S)
import shell_core as core                      # 壳共享路由（元指令＋数据流）＝唯一真源
import msg_flow, detail_bus, atomic_io, settings as st
import stop_channel as stop
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtWidgets import (QApplication, QCompleter, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QPlainTextEdit, QPushButton,
                             QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)
SMS = core.SMS; TD = os.path.join(SMS, "tasks")
SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
M = dict(bg="#1e1e2e", panel="#181825", side="#11111b", fg="#cdd6f4", dim="#6c7086", blue="#89b4fa",
         green="#a6e3a1", yellow="#f9e2af", red="#f38ba8", mauve="#cba6f7", teal="#89dceb",
         peach="#fab387", line="#313244")
def esc(t): return html.escape(str(t), quote=False)
def paint(t):
    """一行文本 → HTML（对齐 shell_tui_paint 语义：⧉技能徽章紫·$ 命令橙·✗ 红·✎ 黄• 绿·路径暗青·`code` 橙）"""
    t = str(t)
    if t.startswith("⧉") and "▸" in t:
        name, _, rest = t[1:].partition("▸")
        body = _rich(rest.lstrip())
        return '<span style="color:%s;font-weight:bold">⧉%s</span> <span style="color:%s">▸</span> %s' % (M["mauve"], esc(name), M["mauve"], body)
    head = {"$ ": (M["peach"], "$ "), "✗ ": (M["red"], "✗ "), "✎ ": (M["yellow"], "✎ "), "• ": (M["green"], "• "), "! ": (M["peach"], "! ")}
    for pre, (col, label) in head.items():
        if t.startswith(pre):
            return '<span style="color:%s;font-weight:bold">%s</span>%s' % (col, esc(label), _rich(t[len(pre):], col if pre == "$ " else None))
    return _rich(t)
PATH = re.compile(r"[A-Za-z]:[\\/][^\s，。！？；：,]+|[\w\-\./\\]+\.(?:py|md|ps1|cmd|json|txt|html|csv|sh|js|ts)\b")
CODE = re.compile(r"`([^`\n]+)`")
def _rich(s, base=None):
    out, pos = [], 0
    ms = sorted(list(PATH.finditer(s)) + list(CODE.finditer(s)), key=lambda m: m.start())
    for m in ms:
        if m.start() < pos: continue
        out.append(esc(s[pos:m.start()]))
        if m.group(0).startswith("`"): out.append('<span style="color:%s;font-weight:bold">%s</span>' % (M["peach"], esc(m.group(1))))
        else: out.append('<span style="color:%s">%s</span>' % (M["teal"], esc(m.group(0))))
        pos = m.end()
    out.append(esc(s[pos:]))
    return '<span style="color:%s">%s</span>' % (base or M["fg"], "".join(out))
def badge(h):
    """〔技能:x〕〔工具:x→y〕徽章着色；入参＝paint 已产出的安全 HTML（不再二次转义）"""
    t = str(h)
    t = re.sub(r"〔(技能|工具):([^〕]*)〕", lambda m: '<span style="color:%s;font-weight:bold">〔%s:%s〕</span>' % (M["mauve"], m.group(1), m.group(2)), t)
    return t

class Task(QThread):
    """一条用户输入＝一个并行任务 worker（tid 绑 stop_channel/ask_channel/chains.ACTIVE 线程本地）。"""
    line = pyqtSignal(str); step = pyqtSignal(str); env = pyqtSignal(object); bye = pyqtSignal(str); over = pyqtSignal(str, object)
    def __init__(self, text, tid):
        super().__init__(); self.text, self.tid, self.t0 = text, tid, time.time()
    def run(self):
        stop.bind(self.tid)
        try:
            import ask_channel; ask_channel.bind(self.tid)
        except Exception: pass
        def _st(n): self.step.emit(str(n))
        done = None
        try:
            done = core.handle(self.text, lambda s: self.line.emit(str(s)), _st, lambda e: self.env.emit(e))
        except stop.Stopped as e:
            self.line.emit("⛔ 任务 %s 已停止（%s）——在途输出中断·旗标已复位" % (self.tid, str(e)[:80]))
        except Exception as e:
            import traceback
            core.debug.enabled() and core.debug.log("EXC " + traceback.format_exc())
            self.line.emit("✗ 处理异常：" + (repr(e)[:200] if not core.debug.enabled() else traceback.format_exc()[-900:]))
        finally:
            try:
                import ask_channel; ask_channel.flush(self.tid)
            except Exception: pass
            stop.clear(self.tid)
        self.over.emit(self.tid, done)

class Editor(QMainWindow):
    """窗内文本编辑器（:edit/:view 令牌与 F8 用），保存＝atomic_io 之外的直写（工作区与用户文件均可）。"""
    def __init__(self, path, ro=False):
        super().__init__(); self.path, self.ro = path, ro
        self.setWindowTitle(("查看 " if ro else "编辑 ") + os.path.basename(path or "") + " — sms-shell GUI")
        self.resize(900, 620)
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        self.bar = QHBoxLayout(); v.addLayout(self.bar)
        self.ed = QPlainTextEdit(); f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace)
        self.ed.setFont(f); v.addWidget(self.ed)
        try:
            self.ed.setPlainText(open(path, encoding="utf-8", errors="replace").read())
        except Exception as e:
            self.ed.setPlainText("（读取失败：%s）" % e)
        self.ed.setReadOnly(ro)
        for label, fn in (("保存", self.save), ("重载", self.reload), ("关闭", self.close)):
            b = QPushButton(label); b.clicked.connect(fn); self.bar.addWidget(b)
        self.stat = QLabel(path or ""); self.stat.setStyleSheet("color:%s" % M["dim"]); self.bar.addWidget(self.stat, 1)
        self.setCentralWidget(w)
    def save(self):
        if self.ro: self.stat.setText("只读——:edit <路径> 可写"); return
        try:
            with open(self.path, "w", encoding="utf-8", newline="\n") as f: f.write(self.ed.toPlainText())
            self.stat.setText("已保存 %s · %s" % (self.path, time.strftime("%H:%M:%S")))
        except Exception as e:
            self.stat.setText("✗ 保存失败：" + str(e)[:160])
    def reload(self):
        try: self.ed.setPlainText(open(self.path, encoding="utf-8", errors="replace").read()); self.stat.setText("已重载")
        except Exception as e: self.stat.setText("✗ 重载失败：" + str(e)[:160])

class Input(QPlainTextEdit):
    """底部输入：Enter 提交 · Ctrl+Enter 换行 · ↑↓ 历史 · Tab 元指令补全。"""
    def __init__(self, win):
        super().__init__(win); self.win = win; self.hist_pos = None
        self.setPlaceholderText("话语回车 → 当前 agent 数据流 · :help 元指令 · stop/停止 收口当前任务 · quit 退出（Ctrl+Enter 换行 · ↑↓ 历史 · Tab 补全）")
        f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace); self.setFont(f)
        self.setFixedHeight(64)
    def keyPressEvent(self, ev):
        k, m = ev.key(), ev.modifiers()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if m & Qt.KeyboardModifier.ControlModifier:
                self.insertPlainText("\n"); return
            self.win.submit(self.toPlainText()); return
        if k == Qt.Key.Key_Tab:
            self.win.complete(self); return
        if k in (Qt.Key.Key_Up, Qt.Key.Key_Down) and self.toPlainText().count("\n") == 0:
            if self.win.history(self, k == Qt.Key.Key_Up): return
        super().keyPressEvent(ev)

class Shell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("sms-shell · PyQt6 图形壳（默认 smsystem-suit 数据流）")
        self.resize(1240, 780)
        self.running, self.pend, self.hist, self.details = {}, [], [], []
        self.seq = self.bus_off = self.hi = 0
        self.awaiting = None; self.task_prog = ""; self.steps = []; self.editors = []
        self._bus_off = None
        try:
            import session_reg as sr; SELF = sr.bind("client", os.getpid(), "Qt壳")
            os.environ.setdefault("SMS_SESSION", SELF)
        except Exception: pass
        self._ui(); self._menu(); self._timers()
        self._side_i = 0
        self.echo(core.banner())
        with contextlib.suppress(Exception):
            sb = core.startup_block(); sb and self.echo(sb)
        with contextlib.suppress(Exception):
            import ask_channel; ask_channel.arm()
        self.refresh_tasks(); self.refresh_side()

    def _ui(self):
        central = QWidget(); self.setCentralWidget(central); root = QVBoxLayout(central); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        self.top = QLabel(""); self.top.setObjectName("top"); root.addWidget(self.top)
        tb = QWidget(); tb.setObjectName("toolbar"); h = QHBoxLayout(tb); h.setContentsMargins(8, 2, 8, 2); h.setSpacing(4)
        for label, fn in ((":help", lambda: self.echo(core.HELP)), (":cmds", lambda: self._meta("cmds")), (":skills", lambda: self._meta("skills")),
                          (":session", lambda: self._meta("session", "overview")), ("清屏", self.clear_log), ("停止全部", lambda: self.stop_all()),
                          ("详细细节", self.focus_details), ("HUD", self.hud_toggle)):
            b = QPushButton(label); b.setObjectName("tb"); b.clicked.connect(fn); h.addWidget(b)
        h.addStretch(1); self.chips = QLabel(""); h.addWidget(self.chips); root.addWidget(tb)
        sp = QSplitter(Qt.Orientation.Horizontal); root.addWidget(sp, 1)
        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0, 0, 0, 0); lv.setSpacing(0)
        self.out = QTextBrowser(); self.out.setObjectName("log"); self.out.setOpenExternalLinks(True); lv.addWidget(self.out, 1)
        self.ent = Input(self); lv.addWidget(self.ent); sp.addWidget(left)
        self.tabs = QTabWidget(); self.tabs.setObjectName("side")
        self.det = QTextBrowser(); self.bus = QTextBrowser(); self.tasks = QListWidget()
        for name, w in (("详细细节", self.det), ("跨会话明细", self.bus), ("任务表", self.tasks)):
            tab = QWidget(); vv = QVBoxLayout(tab); vv.setContentsMargins(0, 0, 0, 0)
            bar = QHBoxLayout(); bar.setContentsMargins(4, 2, 4, 2)
            tlabel = QLabel(name + " "); tlabel.setStyleSheet("color:%s" % M["blue"]); bar.addWidget(tlabel); bar.addStretch(1)
            for bl, fn in (("清空", w.clear), ("复制", lambda x=w: QApplication.clipboard().setText(x.toPlainText() if isinstance(x, QTextBrowser) else "\n".join(str(self.tasks.item(i).data(0)) for i in range(self.tasks.count()))))):
                b = QPushButton(bl); b.setObjectName("tb"); b.clicked.connect(fn); bar.addWidget(b)
            vv.addLayout(bar); vv.addWidget(w); self.tabs.addTab(tab, name)
        sp.addWidget(self.tabs); sp.setStretchFactor(0, 3); sp.setStretchFactor(1, 2)
        self.stat = QLabel(""); self.stat.setObjectName("status"); root.addWidget(self.stat); root.addWidget(self._prog())
        self.setStyleSheet("""QMainWindow{background:%(bg)s}#top{background:%(side)s;color:%(blue)s;padding:3px 8px;font-weight:bold}
#toolbar{background:%(panel)s}QPushButton#tb{background:%(side)s;color:%(fg)s;border:1px solid %(dim)s;border-radius:4px;padding:2px 8px}
QPushButton#tb:hover{color:%(yellow)s;border-color:%(yellow)s}QTextBrowser{background:%(bg)s;color:%(fg)s;border:0;padding:6px}
QListWidget{background:%(side)s;color:%(fg)s;border:0;padding:4px}QTabBar::tab{background:%(side)s;color:%(dim)s;padding:3px 10px;border:1px solid %(dim)s}
QTabBar::tab:selected{color:%(blue)s;background:%(panel)s}QPlainTextEdit{background:%(panel)s;color:%(blue)s;border:0;border-top:1px solid %(dim)s;padding:4px}
#status{background:%(side)s;color:%(dim)s;padding:2px 8px}#prog{background:%(side)s;color:%(yellow)s;padding:1px 8px}QSplitter::handle{background:%(line)s}""" % M)
        self.stat.setText("● 就绪 · Enter 提交 · Ctrl+Q 退出 · F3 帮助 · F8 编辑器 · F12 停止当前任务")

    def _prog(self):
        self.prog = QLabel(""); self.prog.setObjectName("prog"); self.prog.hide(); return self.prog
    def _timers(self):
        self.t_ui = QTimer(self); self.t_ui.timeout.connect(self.tick); self.t_ui.start(150)
        self.t_ask = QTimer(self); self.t_ask.timeout.connect(self.ask_poll); self.t_ask.start(400)
        self.t_bus = QTimer(self); self.t_bus.timeout.connect(self.bus_poll); self.t_bus.start(1000)
        self.t_task = QTimer(self); self.t_task.timeout.connect(self.refresh_tasks); self.t_task.start(2000)
    def _menu(self):
        m = self.menuBar().addMenu("壳(&S)")
        for label, fn, sc in (("帮助 :help", lambda: self.echo(core.HELP), "F3"), ("命令表 :cmds", lambda: self._meta("cmds"), "Ctrl+H"),
                              ("技能清单 :skills", lambda: self._meta("skills"), "Ctrl+K"), ("会话拓扑 :session overview", lambda: self._meta("session", "overview"), "Ctrl+J"),
                              ("配置状态", lambda: self.echo(core._cfgline()), None), ("编辑器（:edit）", self.open_editor, "F8"),
                              ("清屏", self.clear_log, "Ctrl+L"), ("停止全部任务", lambda: self.stop_all(), "F12"),
                              ("另起 TUI 终端壳", lambda: self.submit("tui"), None), ("退出", self.close, "Ctrl+Q")):
            a = QAction(label, self)
            if sc: a.setShortcut(QKeySequence(sc))
            a.triggered.connect(fn); m.addAction(a)
        self.menuBar().hide()  # 快捷键仍生效，顶栏工具条替代菜单视觉
    def echo(self, s, kind=""):
        t = str(s)
        if not t.strip(): return
        if kind != "raw" and not msg_flow.visible(t):
            if not msg_flow.blank(t): self._push(t)
            return
        self._push_cache(t)
        body = "<br>".join(badge(paint(x)) or "&nbsp;" for x in t.split("\n"))
        col = {"err": M["red"], "me": M["blue"]}.get(kind, M["fg"])
        self.out.append('<html><body style="margin:0"><div style="color:%s;margin:0 0 4px 0;white-space:pre-wrap;word-break:break-word">%s</div></body></html>' % (col, body))
        sb = self.out.verticalScrollBar(); sb.setValue(sb.maximum())
    def _push_cache(self, t):
        ("$ " in t or ".py" in t or ".md" in t or "config:" in t) and self.steps.append(t[:160]) if len(self.steps) < 4000 else None
    def _push(self, t):
        d = self.details
        if d and d[-1].startswith(("◌", "〔◌")) and t.startswith(("◌", "〔◌")) and len(d[-1]) < 3000: d[-1] = d[-1] + " " + t.lstrip("◌ ")
        else: d.append(t[:3000])
        self.details = d[-150:]
    def clear_log(self): self.out.clear()
    def focus_details(self): self.tabs.setCurrentIndex(0)

    def probe_finish(self):
        """--probe 端到端回归：把输出区纯文本落盘并退出（供 CLI/CI 无窗验证路由结果）。"""
        try:
            p = os.environ.get("SMS_QT_PROBE_DUMP") or "qt_probe.txt"
            io.open(p, "w", encoding="utf-8").write(self.out.toPlainText())
            sh = os.environ.get("SMS_QT_SHOT")
            sh and self.grab().save(sh)
            print("PROBE_DUMP " + p + " chars=" + str(len(self.out.toPlainText())) + " details=" + str(len(self.details)))
        except Exception as e:
            print("PROBE_FAIL " + repr(e)[:160])
        QApplication.instance().quit()

    def qtver(self):
        try:
            from PyQt6.QtCore import QT_VERSION_STR
            return QT_VERSION_STR
        except Exception:
            return "?"

    def hud_toggle(self):
        """HUD 浮层开关：未显→写 session 行（hud_view 自动拉起置顶浮层）；已显→hide。"""
        try:
            import hud
            if hud._load().get("session"):
                self._hud("hide", "", 0); self.echo("HUD 已隐藏", kind="info")
            else:
                self._hud("session", "sms-shell GUI（PyQt6）· 就绪", 1800)
                self.echo("HUD 已开启（置顶·点击穿透·只读）", kind="info")
        except Exception as e:
            self.echo("HUD 不可用：" + str(e)[:120], kind="info")
    def _par(self):
        try: return bool(st.get("shell.parallel", True))
        except Exception: return True
    def _cap(self):
        try: return int(st.get("shell.max_parallel", 4) or 0)
        except Exception: return 4
    def _room(self):
        if not self._par(): return not self.running
        c = self._cap()
        return not c or len(self.running) < c
    def submit(self, text):
        text = (text or "").strip(); self.ent.clear()
        if not text: return
        w = text.split(" ", 1); one = w[1].strip() if len(w) > 1 else ""
        if stop.is_stop_word(text) or (stop.is_stop_word(w[0]) and one in self.running):
            self.stop_one(one); return
        if self.awaiting:
            import ask_channel
            self.echo("sms> （答复）" + text, kind="me")
            ask_channel.reply(text, self.awaiting[0]); self.awaiting = None; return
        lo = text.lower()
        if lo in (":gui", ":qt", "gui"):
            self.hist.append(text); self.hi = len(self.hist); self.ent.clear()
            self.echo("当前＝PyQt6 图形壳（shell_qt.py）· Qt %s · 并行 %d/%s · 明细 %d 条\n"
                      "可用本地指令：:gui 本壳状态 · :clear 清输出区 · :reload 重载任务表/明细 · tui 另起 Textual 终端壳；"
                      "其余 `:` 元指令一律交 shell_core（同 TUI）。" % (
                          self.qtver(), len(self.running), (self._cap() or "无限"), len(self.details)), kind="info")
            return
        lo = text.lower()
        if lo in (":clear", ":reload"):
            self.hist.append(text); self.hi = len(self.hist); self.ent.clear()
            if lo == ":clear": self.out.clear(); self.echo("（输出区已清·明细仍留在右栏）", kind="info")
            else: self.refresh_tasks(force=True); self.echo("已重载任务表/明细视图", kind="info")
            return
        if lo in ("tui", ":tui"):
            self.hist.append(text); self.hi = len(self.hist); self.ent.clear()
            _dn = open(os.devnull, "r+b")
            # sms-visible：GUI 另起可见 Textual TUI 终端壳（有意开新控制台窗·与 shell_gui.py 同口径）
            subprocess.Popen([sys.executable, "-B", os.path.join(S, "shell_tui_textual.py")],
                             stdin=_dn, stdout=_dn, stderr=_dn, close_fds=True)
            self.echo("已另起 Textual TUI 终端壳", kind="info"); return
        self.hist.append(text); self.hi = len(self.hist)
        if not self._room():
            self.pend.append(text)
            self.echo("已排队 %d 条 · %s·有空位自动续发" % (len(self.pend), "并发已达上限 %d" % self._cap() if self._par() else "并行已关（:config set shell.parallel false）"), kind="info")
            return
        self.start(text)
    def start(self, text):
        self.seq += 1; tid = "t%d" % self.seq
        self.echo("sms> %s%s" % (text, ("   〔并行第 %d 个任务〕" % (len(self.running) + 1)) if self.running else ""), kind="me")
        self.running[tid] = {"text": text, "t0": time.time()}
        self.prog.show(); self._hud("session", (text[:60] or "sms-shell GUI") , 1800)
        w = Task(text, tid)
        w.line.connect(lambda s, t=tid: self.on_line(t, s))
        w.step.connect(lambda s, t=tid: self.on_step(t, s))
        w.env.connect(lambda e, t=tid: self.on_env(t, e))
        w.over.connect(self.on_over)
        w.start(); self.running[tid]["w"] = w
    def on_line(self, tid, s):
        tag = ("[%s] " % tid) if len(self.running) > 1 else ""
        t = str(s)
        if msg_flow.visible(t):
            self.echo((tag or "") + t)
        elif not msg_flow.blank(t):
            self._push((tag + t)[:3000])
    def on_step(self, tid, n):
        tag = ("[%s] " % tid) if len(self.running) > 1 else ""
        self._push(tag + "▸ " + str(n)); self.last_step = str(n)
        self._hud("step", str(n)[:80], 120)
    def on_env(self, tid, e):
        try:
            if not isinstance(e, dict): return
            k, m = e.get("kind"), e.get("meta") or {}
            if k == "task":
                eta = int(m.get("eta_s") or 0)
                self.task_prog = "≡ %s %s/%s%s" % (str(m.get("id", ""))[-6:], m.get("done", 0), m.get("total", 0), (" · " + msg_flow.fmt(eta)) if eta else "")
                self.prog.setText("▍任务表 " + self.task_prog)
            elif k == "edit":
                self._push("✎ " + str(e.get("text") or ""))
            elif k == "err":
                self.echo("✗ " + str(e.get("text") or ""), kind="err")
        except Exception: pass
    def on_over(self, tid, done):
        info = self.running.pop(tid, None) or {}
        el = time.time() - float(info.get("t0") or time.time())
        if self.awaiting and self.awaiting[0] == tid: self.awaiting = None
        if self.running:
            self.echo("✔ 任务 %s 收口（%.1fs）·仍在并行跑 %d 个：%s" % (tid, el, len(self.running), "、".join(sorted(self.running))), kind="info")
        else:
            self.prog.hide(); self.task_prog = ""
            self.stat.setText("● 就绪 · 上一条用时 %.1fs · 明细 %d 条（F3 帮助 · F8 编辑器 · Ctrl+Q 退出）" % (el, len(self.details)))
            self._hud("hide", "", 0)
        if isinstance(done, str) and done.startswith(("edit:", "view:")):
            self.open_editor(done.split(":", 1)[1], ro=done.startswith("view:")); done = None
        if done == "exit": self.close(); return
        if done == "config": self.echo(core._cfgline())
        while self.pend and self._room(): self.start(self.pend.pop(0))
    def stop_one(self, one=""):
        if self.awaiting:
            import ask_channel; ask_channel.reply("用户已请求停止任务（stop）", self.awaiting[0]); self.awaiting = None
        if one and one in self.running:
            stop.request("GUI 输入 stop " + one, one); self.echo("⛔ 已请求停止任务 %s（其余 %d 个不受影响）" % (one, len(self.running) - 1), kind="info"); return
        if one and one not in self.running:
            self.echo("无此在跑任务：%s（现行 %s）" % (one, "、".join(sorted(self.running)) or "无"), kind="info"); return
        if self.running:
            for tid in list(self.running): stop.request("GUI 输入 stop（全部）", tid)
            self.echo("⛔ 已请求停止全部 %d 个在跑任务——各任务在下一检查点收口" % len(self.running), kind="info"); return
        stop.clear(); self.echo("空闲：无进行中任务·停止状态已清", kind="info")
    def stop_all(self): self.stop_one("")

    def tick(self):
        self._side_i = getattr(self, "_side_i", 0) + 1
        if self._side_i % 7 == 0: self.refresh_side()
        if self._side_i % 10 == 0: self.refresh_tasks()
        steps = list(self.details)[-1:]
        cur = self.task_prog or getattr(self, "last_step", "") or "sms-shell·PyQt6 图形壳 · 就绪"
        n = len(self.running)
        sp = SPIN[int(time.time() * 8) % 10] if n else "●"
        sess = ""
        with contextlib.suppress(Exception): sess = core.chains.cur_sess()
        el = ""
        if n:
            el = " · 已用 %.0fs" % (time.time() - min(float(v.get("t0") or time.time()) for v in self.running.values()))
        self.top.setText("%s %s ｜ session=%s ｜ 在跑 %d%s ｜ 排队 %d ｜ 明细 %d" % (sp, cur, sess or "-", n, el, len(self.pend), len(self.details)))
        if not n: self.stat.setText("● 就绪 · Enter 提交 · Ctrl+Q 退出 · F3 帮助 · F8 编辑器 · F12 停止全部 · 明细 %d 条" % len(self.details))
        else:
            ids = "、".join(sorted(self.running)); self.chips.setText("并行中 " + ids)
            self.stat.setText("%s %d 个任务在跑（%s）· stop 停全部 / stop <tid> 停一个 · ask_user 提问时下一条输入即答复" % (SPIN[int(time.time() * 8) % 10], n, ids))
        if not n: self.chips.setText("")
    def ask_poll(self):
        if self.awaiting: return
        try:
            import ask_channel; r = ask_channel.poll_any()
        except Exception: return
        if not r: return
        tid, q = r; self.awaiting = (tid, q)
        self.echo("❓ 大模型提问%s（直接输入即答复 · stop %s 只停它）：" % (("〔任务 %s〕" % tid) if tid else "", tid or ""), kind="info")
        self.out.append('<html><body><div style="color:%s;white-space:pre-wrap">%s</div></body></html>' % (M["mauve"], esc(q)))
    def bus_poll(self):
        try:
            if self.bus_off is None:
                import os as _os
                p = detail_bus.path(core.SMS)
                self.bus_off = _os.path.getsize(p) if _os.path.isfile(p) else 0
                return
            own = os.environ.get("SMS_SESSION") or ""
            off, rows = detail_bus.tail(self.bus_off, 120, core.SMS)
            self.bus_off = off
            for e in rows:
                if e.get("sess") == own: continue
                line = "〔%s·%s〕%s" % (str(e.get("sess") or "-")[-6:], e.get("kind"), str(e.get("text") or ""))
                self.bus.append('<div style="color:%s;white-space:pre-wrap;word-break:break-word">%s</div>' % (M["dim"], esc(line[:600])))
                self._push(line)
            if rows:
                sb = self.bus.verticalScrollBar(); sb.setValue(sb.maximum())
        except Exception: pass
    def refresh_tasks(self, force=False):
        rows = []
        try:
            ids = sorted([f[:-5] for f in os.listdir(TD) if f.endswith(".json")]) if os.path.isdir(TD) else []
        except Exception: ids = []
        for tid in ids[-6:]:
            doc = atomic_io.rjson(os.path.join(TD, tid + ".json"), default=None) or {}
            subs = doc.get("subtasks") or []
            if not subs: continue
            dn = sum(1 for x in subs if x.get("status") == "done")
            rows.append((tid, doc, subs, dn))
        self.tasks.clear()
        for tid, doc, subs, dn in rows:
            it = QListWidgetItem("≡ %s · %d/%d · %s" % (tid[-14:], dn, len(subs), esc(str(doc.get("intent") or "")[:60])))
            f = QFont("Cascadia Mono", 9)
            it.setFont(f); it.setForeground(_c(M["blue"]))
            self.tasks.addItem(it)
            for x in subs:
                mark = {"done": "✔", "running": "▶", "error": "✗", "skipped": "⤳", "stopped": "⛔"}.get(str(x.get("status")), "·")
                line = "   %s %s %s%s" % (mark, x.get("id"), str(x.get("goal") or "")[:78], (" 〔" + str(x.get("skill")) + "〕") if x.get("skill") else "")
                sub = QListWidgetItem(line); sub.setFont(f)
                sub.setForeground(_c({"done": M["green"], "running": M["yellow"], "error": M["red"]}.get(str(x.get("status")), M["dim"])))
                self.tasks.addItem(sub)
    def refresh_side(self):
        html_out = []
        for n, x in enumerate(self.details[-60:], 1):
            html_out.append('<div style="color:%s;margin:0 0 2px 0"><b>── %d ──</b></div><div style="color:%s;white-space:pre-wrap;word-break:break-word">%s</div>' % (M["dim"], n, M["fg"], esc(x)))
        self.det.setHtml("".join(html_out) or ('<div style="color:%s">（暂无——◌思考/$工具/⧉技能/!sh/▸步骤过程行收进这里，主输出只留正文）</div>' % M["dim"]))
    def _hud(self, key, text, ttl):
        """HUD 常显同步：进程内直调 hud._set/_hide（写 <SMS_HOME>/hud/state.json·置顶浮层缺活自动拉起），
        同文本 2s 内不重复写（免每步 spawn 子进程）。"""
        try:
            self._hud_last = getattr(self, "_hud_last", {})
            k = "hud:" + key; now = time.time()
            last_txt, last_at = self._hud_last.get(k, ("", 0))
            if key != "hide" and text == last_txt and now - last_at < 2.0: return
            self._hud_last[k] = (text, now)
            import hud
            if key == "hide": hud._hide(); return
            hud._set(key, text, ttl)
        except Exception: pass
    def _meta(self, cmd, rest=""):
        self.submit(":%s%s" % (cmd, (" " + rest) if rest else ""))
    def open_editor(self, path="", ro=False):
        path = path or (os.environ.get("SMS_TMP") or core.SMS)
        if os.path.isdir(path):
            e = Editor(os.path.join(path, "untitled.md"), ro); path = os.path.join(path, "untitled.md")
        else:
            e = Editor(path, ro)
        e.show(); self.editors.append(e)
        self.echo("已打开编辑器（%s）：%s" % ("查看" if ro else "编辑", path), kind="info")
    def history(self, up):
        if not self.hist: return True
        self.hi = max(0, min(len(self.hist), self.hi + (-1 if up else 1)))
        self.set_text_line(self.hist[self.hi] if self.hi < len(self.hist) else "")
        return True
    def set_text_line(self, t):
        self.ent.setPlainText(t)
        c = self.ent.textCursor(); c.movePosition(c.MoveOperation.End); self.ent.setTextCursor(c)
    def complete(self, ent):
        txt = ent.toPlainText()
        if not txt.strip().startswith(":"): return
        cand = [":help", ":cmds", ":skills", ":config", ":session", ":dispatch", ":sh", ":hud", ":solo", ":agents", ":use", ":resume", ":plan", ":web", ":debug", ":detail", ":edit", ":view", ":deploy", ":workspace", ":grant", ":stop", ":restart", ":shutdown", ":smsocket", ":tts", ":repair", ":task", ":manual", ":quit"]
        head = txt.split("\n")[-1].strip()
        hits = [c for c in cand if c.startswith(head)]
        if len(hits) == 1:
            ent.setPlainText(txt[: len(txt) - len(head)] + hits[0] + " ")
        elif hits:
            self.echo("补全候选：" + "、".join(hits[:16]), kind="info")
    def closeEvent(self, ev):
        for w in list(self.running.values()):
            with contextlib.suppress(Exception): w["w"].requestInterruption(); w["w"].quit(1200)
        with contextlib.suppress(Exception):
            import ask_channel; ask_channel.disarm()
        super().closeEvent(ev)

def _c(hexcol):
    from PyQt6.QtGui import QColor
    return QColor(hexcol)


def main(argv=None):
    argv = [a for a in (argv if argv is not None else sys.argv[1:]) if a != "--"]
    selftest = "--selftest" in argv
    if selftest:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("sms-shell-gui")
    win = Shell()
    if selftest:
        return _selftest(app, win)
    win.show()
    pos = [a for a in argv if a not in ("--selftest",)]
    pos = [a for a in pos if not a.startswith("--probe")]
    probe = next((a.split("=", 1)[1] for a in argv if a.startswith("--probe=")), "")
    if probe:
        os.environ["SMS_QT_PROBE_DUMP"] = os.environ.get("SMS_QT_PROBE_DUMP") or os.path.join(
            os.environ.get("SMS_TMP") or os.getcwd(), "qt_probe.txt")
        parts = [x.strip() for x in probe.split("||") if x.strip()]
        for i, one in enumerate(parts):
            QTimer.singleShot(200 + i * 400, lambda t=one: win.submit(t))
        QTimer.singleShot(int(os.environ.get("SMS_QT_PROBE_MS", "9000")), win.probe_finish)
    elif pos:
        QTimer.singleShot(120, lambda: win.submit(" ".join(pos)))
    return app.exec()

def _selftest(app, win):
    """离线自检（不发模型请求）：布局成图＋行分类/上色/排队/停止词/任务表渲染全跑一遍。"""
    out = {}
    win.show()
    app.processEvents()
    cases = ["sms-shell 速查", "• notice 行", "$ exec ls -la", "◌ 思考过程行", "▸ 步骤行", "✗ 错误行", "⧉general_answer▸ 派发对话正文", "! sh 输出", "≡ task 进度", "带 `代码` 与 C:\\path\\file.py 的正文"]
    for c in cases:
        win.on_line("t9", c)
    win.echo("用户话语测试行", kind="me")
    for e in ({"kind": "task", "meta": {"id": "task-20261009-000000-000", "done": 3, "total": 5, "eta_s": 96}},
              {"kind": "edit", "text": "已改 tmp/a.py"}):
        win.on_env("t9", e)
    win.running.setdefault("t9", {"text": "x", "t0": time.time() - 3})
    win.tick(); app.processEvents()
    win.stop_one("t9")
    win.pend.append("排队行示例")
    win.refresh_tasks(); win.refresh_side(); app.processEvents()
    shot = os.path.join(os.environ.get("SMS_TMP") or os.getcwd(), "qt_selftest.png")
    ok = win.grab().save(shot)
    from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    out = {"visible_rows": win.out.toPlainText().count("\n"), "details": len(win.details),
           "tasks_rows": win.tasks.count(), "bus_widget": win.bus is not None,
           "stop_word_hit": stop.is_stop_word("停止"), "paint_html": bool(paint("$ ls")),
           "queued": len(win.pend), "running": sorted(win.running), "screenshot": shot, "saved": bool(ok),
           "qt": QT_VERSION_STR, "pyqt": PYQT_VERSION_STR,
           "banner_len": len(core.banner()), "hud_state": os.path.join(core.SMS, "hud", "state.json")}
    print("SELFTEST " + json.dumps(out, ensure_ascii=False))
    return 0 if out["saved"] and out["visible_rows"] >= 8 else 1

if __name__ == "__main__":
    if sys.stdout is None or sys.stderr is None:
        # pythonw 无控制台：print 会抛，统一兜到 devnull（日志仍走 debug/log）
        _dn = open(os.devnull, "w", encoding="utf-8")
        sys.stdout = sys.stdout or _dn; sys.stderr = sys.stderr or _dn
    sys.exit(main())

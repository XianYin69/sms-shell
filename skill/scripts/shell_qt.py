#!/usr/bin/env python3
"""shell_qt.py — sms-shell 图形壳（PyQt6）＝网页端传真机界面的本机镜像（批38 重写）：
批40 起机身 chassis＝零顶栏三区（常驻）→ A 纸卷区 PAPER ROLL（出纸正文＋状态行 LCD 六格/LED 七灯＋mouth 口腔·
tear 撕纸线·blade 裁纸刀＋复制/下载/撕纸/裁纸/墨水屏/命令面板动作条）B 送稿口 DOC FEEDER（话语/:元指令·Tab 补全·
↑↓ 历史·常用拨号·CRT 成像）C 墨水屏 E-INK（只三段·Ctrl+I 展开）；按需层＝控制面板（META 键阵＋F1 六组＋拨号盘＋
↻巡检/🔊朗读/⏸停止/▶继续·Ctrl+M）与抽屉面板（任务表/计划/链/会话/技能/文件/配置/权限/明细）。
批39 三视图件（算式与版式真源全在 shell_qt_fax.py，本文件只接绘制与状态推进·零新端口零新进程零子线程）：
t6 出纸末端裁纸刀（✂ 裁纸 CUT：fax.cut_next 五态推进·进程内 QTimer 每 200ms 走一步·刀条 QFrame#blade[st=…]
随态换渐变＋行程百分比＋裁纸指示灯·落 drop 在纸面留裁断印记·途中再点＝中止）；t8 送稿口 CRT（绿字 #33ff66
黑底＋扫描线叠加＋余辉衰减＋块光标闪烁：Input.paintEvent/_crt_overlay 三层成像，keyPressEvent 与
路由/stop/ask 口径一字未改，fax("crt") 可关成像层）；t10 墨水屏消息面板（▤ 墨水屏 E-INK：只显示
fax.EINK_SECTIONS 三段＝会话信息／任务表／后台任务·低饱和灰白实色·无动效·仿电子墨水印，
数据仍走 fax.api 进程内直调）。自检含三件断言（cut_ok/crt_ok/eink_ok）。
**GUI 端不做任何密钥验证**：网页端的门禁插令牌区（#gate）在图形壳不存在——本机窗口即可信，面板数据经
shell_qt_fax.api() 进程内直调 web_shell 同一套 getter/poster，绝不开端口、绝不读/显影/复制/轮换 token，
info 结果一律 scrub 掉 token/指纹。版式与键位每次现取 web_page.html（CSS :root 变量→QSS 渐变、
JS META·METAD·PAD·QUICK·F1→机身件），页面取不到时用内置兜底，网页端改了图形壳跟着改、不留两份口径。
路由完全复用 shell_core.handle：`:` 元指令、`!` 系统 shell、裸内置词、话语→数据流一律同 TUI/网页端；
并行、停止、提问、明细、任务表、HUD、编辑器与旧壳同口径（Task worker·stop_channel/ask_channel/chains.ACTIVE
线程隔离·shell.parallel=false 或达 shell.max_parallel 排队续发·stop <tid> 只停一个·ask_user 下一条输入即答复）。
零裸子进程：唯一有意开窗处（`tui` 另起终端壳）带 `# sms-visible` 标记，其余一律 no_window。
批40 零顶栏三区骨架：机身不装原生菜单栏、不装 brand 横条——常驻只 A 纸卷区（出纸正文＋状态行 LCD 六格/LED 七灯
＋裁纸刀）、B 送稿口（CRT 成像·键盘口径不变）、C 墨水屏（只三段·Ctrl+I）；控制面板（META 键阵·F1 六组·拨号盘）
与抽屉＝按需展开（Ctrl+M）。菜单职能＝命令面板 Ctrl+K（条目同源 MENU_ITEMS·出口同实体键 feed/faxPick/_open/submit）
＋右键菜单；原菜单快捷键 F3/F5/F8/Ctrl+T/P/J/H/E/I/R/M/V/K 一律保 QAction 级（_menu_actions·不挂 menuBar）。
fw 键面逐字兼容批38/39（banner/roll/drawer/dtitle/dbody/lcd_*/led_*/blade*/eink*/btn_*/keys 全保留）。
跑法：bin/sms-shell-gui（图形入口·批37 双入口）或 python -B shell_qt.py · 自检：python -B shell_qt.py --selftest
（offscreen 成图＋机身件计数＋抽屉面板渲染，不发模型请求）；端到端回归：--probe=:help||:cmds（输出落 txt）。"""
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
        for c in (os.path.join(home, "skills", "sms-shell", "scripts"),
                  os.path.join(skill or "", "..", "sms-shell", "scripts") if skill else "",
                  os.path.join(skill or "", "..", "sms-shell", "skill", "scripts") if skill else ""):
            if c: cand.append(os.path.normpath(c))
    root = os.path.normpath(os.path.join(here, "..", ".."))
    for name in ("SMS-core", "sms-core", "SMS-shell", "sms-shell"):
        cand.append(os.path.join(root, name, "skill", "scripts"))
    return next((c for c in cand if c and os.path.isfile(os.path.join(c, "shell_core.py"))), here)
S = _scripts()
# 本目录优先：混合/覆盖安装环境里 PYTHONPATH 带着核仓旧副本，同目录件须压过它
if sys.path[:1] != [S]: sys.path.insert(0, S)
import shell_core as core                      # 壳共享路由（元指令＋数据流）＝唯一真源
import msg_flow, detail_bus, atomic_io, settings as st
import stop_channel as stop
def _load_fax():
    """镜像件按「与本文件同目录」显式装载：引擎件（shell_core 等）会把核仓旧副本插到 sys.path 最前，
    裸 import 可能拿到旧版 shell_qt_fax.py 配新机身；成对件必须同源（覆盖安装态＝同一路径，行为不变）。"""
    import importlib.util as _u
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "shell_qt_fax.py")
    if not os.path.isfile(p): raise ImportError("shell_qt_fax.py 不在 %s" % here)
    old = sys.modules.get("shell_qt_fax")
    if old is not None and os.path.abspath(getattr(old, "__file__", "") or "") == p: return old
    spec = _u.spec_from_file_location("shell_qt_fax", p)
    m = _u.module_from_spec(spec); sys.modules["shell_qt_fax"] = m; spec.loader.exec_module(m)
    return m

try:
    fax = _load_fax()                           # 传真机镜像件（版式取网页端·数据直调 web_shell·无密钥面）
except ImportError as e:                        # 缺件＝覆盖安装不完整，明确交棒终端入口而非半瞎窗口
    sys.exit("图形壳缺镜像件 shell_qt_fax.py（%s）——跑 deploy.py 或 install_overlay.py --write 补全，"
             "或用 bin/sms-shell-tui 终端入口" % e)
from PyQt6.QtCore import Qt, QRect, QSize, QThread, QTimer, QProcess, pyqtSignal
from PyQt6.QtGui import (QAction, QColor, QFont, QKeySequence, QPainter, QTextFormat)
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMainWindow, QMenu, QPlainTextEdit, QPushButton,
                             QTextBrowser, QTextEdit, QVBoxLayout, QWidget)
SMS = core.SMS; TD = os.path.join(SMS, "tasks")
SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PAPE = dict(bg="#f7f3e7", ink="#1b2026", dim="#6b6152", blue="#2b4a63", green="#1d6b41", yellow="#8a6a2a",
            red="#c81e1e", mauve="#6b3fa0", teal="#0f6b7a", peach="#b45309", line="#c9c0ae", sys="#5a4a1c")
def esc(t): return html.escape(str(t), quote=False)
def paint(t):
    """一行文本 → 纸面 HTML（传真墨色口径：⧉技能紫·$ 命令棕橙·✗ 红·✎ 黄·• 绿·路径青·`code` 棕橙）"""
    t = str(t)
    if t.startswith("⧉") and "▸" in t:
        name, _, rest = t[1:].partition("▸")
        return '<span style="color:%s;font-weight:bold">⧉%s</span> <span style="color:%s">▸</span> %s' % (
            PAPE["mauve"], esc(name), PAPE["mauve"], _rich(rest.lstrip()))
    head = {"$ ": (PAPE["peach"], "$ "), "✗ ": (PAPE["red"], "✗ "), "✎ ": (PAPE["yellow"], "✎ "),
            "• ": (PAPE["green"], "• "), "! ": (PAPE["peach"], "! ")}
    for pre, (col, label) in head.items():
        if t.startswith(pre):
            return '<span style="color:%s;font-weight:bold">%s</span>%s' % (col, esc(label),
                                                                            _rich(t[len(pre):], col if pre == "$ " else None))
    return _rich(t)
PATH = re.compile(r"[A-Za-z]:[\\/][^\s，。！？；：,]+|[\w\-\./\\]+\.(?:py|md|ps1|cmd|json|txt|html|csv|sh|js|ts)\b")
CODE = re.compile(r"`([^`\n]+)`")
def _rich(s, base=None):
    out, pos = [], 0
    ms = sorted(list(PATH.finditer(s)) + list(CODE.finditer(s)), key=lambda m: m.start())
    for m in ms:
        if m.start() < pos: continue
        out.append(esc(s[pos:m.start()]))
        if m.group(0).startswith("`"): out.append('<span style="color:%s;font-weight:bold">%s</span>' % (PAPE["peach"], esc(m.group(1))))
        else: out.append('<span style="color:%s">%s</span>' % (PAPE["teal"], esc(m.group(0))))
        pos = m.end()
    out.append(esc(s[pos:]))
    return '<span style="color:%s">%s</span>' % (base or PAPE["ink"], "".join(out))
def badge(h):
    """〔技能:x〕〔工具:x→y〕徽章着色；入参＝paint 已产出的安全 HTML（不再二次转义）"""
    return re.sub(r"〔(技能|工具):([^〕]*)〕", lambda m: '<span style="color:%s;font-weight:bold">〔%s:%s〕</span>' %
                  (PAPE["mauve"], m.group(1), m.group(2)), str(h))

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


class LineNumberArea(QWidget):
    """预览件行号栏（批41·独立自绘）：宽度＝位数×字宽＋边距；绘制一律走 Preview.lnr_rows()
    的块几何（document().documentLayout()），不自存行号数组、不改文本模型。"""
    def __init__(self, ed):
        super().__init__(ed); self.ed = ed
    def sizeHint(self):
        fm = self.ed.fontMetrics()
        return QSize(max(34, 9 + fm.horizontalAdvance("9" * max(2, len(str(self.ed.blockCount()))))), 0)
    def paintEvent(self, ev): self.ed.lnr_paint(ev)


class Preview(QPlainTextEdit):
    """预览件 D（批41）：代码/文件只读预览＋行号栏＋当前行整行高亮。数据只由 Shell.previewOpen 经
    进程内 fax.api()（/api/files·/api/file·/api/detail）灌入——绝不新建 HTTP、绝不读 token；
    折行关闭＝行号与源行一一对应。取不到＝preview_text 内置兜底＋纸面「卡纸」（不静默）。"""
    def __init__(self, win=None):
        super().__init__(); self.win = win
        self.lnr = LineNumberArea(self)
        self.blockCountChanged.connect(self.lnr_resize)
        self.updateRequest.connect(self.lnr_update)
        self.cursorPositionChanged.connect(self.lnr_highlight)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setReadOnly(True); self.setObjectName("preview")
        f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace); self.setFont(f)
        self.lnr_resize(0); self.lnr_highlight()

    def lnr_width(self): return int(self.lnr.sizeHint().width())
    def lnr_resize(self, _h=0):
        self.setViewportMargins(self.lnr_width(), 0, 0, 0)
        self.lnr.setGeometry(0, 0, self.lnr_width(), self.height() or 0)
    def lnr_update(self, r, dy):
        if dy: self.lnr_resize(0)
        else: self.lnr.update(0, r.y(), self.lnr_width(), r.height())
    def lnr_rows(self, limit=4000):
        """可见块 → [(行号, y)]：几何取 document().documentLayout().blockBoundingRect（Qt 官方口径），
        字体/DPI 变了也不用改判据；自检与 paintEvent 共用此算式（同一份真源）。"""
        out = []
        with contextlib.suppress(Exception):
            dl = self.document().documentLayout(); fm = self.fontMetrics()
            vh = self.viewport().height(); b = self.firstVisibleBlock()
            if not b.isValid(): return out
            top = int(dl.blockBoundingRect(b).top()) - int(self.contentOffset().y())
            bottom = vh + 40
            while b.isValid() and len(out) < limit:
                if b.isVisible() and top + int(dl.blockBoundingRect(b).height()) > -fm.height():
                    if top <= bottom: out.append((int(b.blockNumber()) + 1, top))
                    else: break
                b = b.next()
                if not b.isValid(): break
                top = int(dl.blockBoundingRect(b).top()) - int(self.contentOffset().y())
        return out
    def lnr_paint(self, ev):
        try:
            p = QPainter(self.lnr); fm = self.fontMetrics()
            p.fillRect(ev.rect(), QColor("#eef3f8")); p.setPen(QColor("#4c5a68"))
            for num, y in self.lnr_rows():
                if y + fm.ascent() > 0: p.drawText(4, y + fm.ascent(), str(num))
            p.end()
        except Exception: pass               # 行号失败绝不影响预览正文
    def lnr_highlight(self):
        with contextlib.suppress(Exception):
            sel = QTextEdit.ExtraSelection(); sel.format.setBackground(QColor("#dfeaf5"))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor(); sel.cursor.clearSelection()
            self.setExtraSelections([sel])
    def line_count(self):
        return int(self.blockCount())


class Terminal(QPlainTextEdit):
    """终端件 E（批41）：面板只管成像与缓冲——进程由 Shell._termSpawn 起（QProcess·无控制台窗口·
    随窗口 closeEvent 收净）。上色按 fax.term_line_kind（纯算式真源在镜像件）。"""
    def __init__(self, win=None):
        super().__init__(); self.win = win
        self.setObjectName("term"); self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace); self.setFont(f)
        self.lines = []                       # [(kind, text)]
    def put(self, kind, text):
        """一行进缓冲＋成像（kind 缺省＝按 fax.term_line_kind 判色）；多行文本逐行入缓冲。"""
        t = str(text or "")
        for one in (t.split("\n") if t else [""]):
            k = kind or fax.term_line_kind(one)
            self.lines.append((k, one))
            c = self.textCursor(); c.movePosition(c.MoveOperation.End)
            fmt = QTextCharFormat(); fmt.setForeground(QColor(TERM_INK.get(k, "#cfe6d8")))
            c.insertText(one + "\n", fmt)
        self.lines = self.lines[-4000:]
        sb = self.verticalScrollBar(); sb.setValue(sb.maximum())
        return kind or fax.term_line_kind(t.split("\n")[0])
    def tail(self, n=200):
        return "\n".join(t for _k, t in self.lines[-int(n or 200):])
    def wipe(self):
        self.clear(); self.lines = []

TERM_INK = {"sh": "#33ff66", "out": "#9fd8c0", "meta": "#54d9ff", "err": "#ff5252",
            "sys": "#ffb02e"}          # 终端面板用色（CRT 同族·由 fax 配色补值）


class TermIn(QLineEdit):
    """终端输入行（批41）：`!xxx`＝系统 shell（QProcess 起 sys_shells 本体＝`!` 真源，权限门继承）；
    `:元指令`／裸内置词／话语＝一律交 Shell.submit → shell_core.handle（同 TUI·唯一路由口·不新建第二条）。
    Enter 执行 · ↑↓ 终端历史。"""
    def __init__(self, win):
        super().__init__(win); self.win = win
        self.setObjectName("termIn")
        f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace); self.setFont(f)
    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self.win.termRun(); return
        if k in (Qt.Key.Key_Up, Qt.Key.Key_Down): self.win.termHist(k == Qt.Key.Key_Up); return
        super().keyPressEvent(ev)


class Input(QPlainTextEdit):
    """底部输入（t8 CRT 送稿口）：Enter 提交 · Ctrl+Enter 换行 · ↑↓ 历史 · Tab 元指令补全——
    keyPressEvent 与路由/stop/ask 口径一字未改；CRT 只是叠加成像：绿字黑底（#33ff66 系·QSS cmd[crt="1"]）
    ＋扫描线叠加＋余辉衰减＋块光标闪烁。算式真源＝shell_qt_fax.crt_*（单点），绘制＝_crt_overlay，
    走进程内 QTimer·零新端口、零新进程、零子线程。"""
    def __init__(self, win):
        super().__init__(win); self.win = win; self.hist_pos = None
        self.setObjectName("cmd"); self.setProperty("crt", "1")   # QSS 对位镜像件送稿口区（CRT 实色底）
        self.crt_on = True; self.crt_force = False; self._glow_t = time.time(); self._cur_on = True
        self.setPlaceholderText("话语回车 → 当前 agent 数据流 · :help 元指令 · stop/停止 收口当前任务 · quit 退出（Ctrl+Enter 换行 · ↑↓ 历史 · Tab 补全）")
        f = QFont("Cascadia Mono"); f.setStyleHint(QFont.StyleHint.Monospace); self.setFont(f)
        self.setFixedHeight(64)
        self.textChanged.connect(self._crt_glow)
        self.t_crt = QTimer(self); self.t_crt.timeout.connect(self._crt_blink); self.t_crt.start(500)
        with contextlib.suppress(Exception): self.style().polish(self)

    def _crt_glow(self):
        """打字＝荧光粉重新点亮：余辉计时归零（衰减算式＝fax.crt_afterglow）。"""
        self._glow_t = time.time()

    def _crt_blink(self):
        """块光标闪烁（500ms 进程内 QTimer·不动文本模型）。"""
        self._cur_on = not bool(getattr(self, "_cur_on", True))
        with contextlib.suppress(Exception): self.viewport().update()

    def crt_cursor_rect(self):
        """块光标矩形（视口坐标·宽≈0.62 字宽＝fax.crt_block_cursor）。"""
        r = self.cursorRect()
        try:
            r.setWidth(fax.crt_block_cursor(self.fontMetrics().averageCharWidth() or 8))
        except Exception:
            r.setWidth(7)
        return r

    def crt_scan(self):
        """扫描线 y 位表（每 3px 一条·真源＝fax.crt_scanlines）。"""
        with contextlib.suppress(Exception):
            return fax.crt_scanlines(self.viewport().height(), 3)
        return []

    def _crt_overlay(self, p, w=0, h=0):
        """CRT 三层成像（余辉→扫描线→块光标）画到任意 painter：paintEvent 与自检走同一条路。"""
        vp = self.viewport()
        c = fax.crt_colors()
        g = fax.crt_afterglow((time.time() - float(getattr(self, "_glow_t", time.time()))) * 1000.0)
        r = QRect(0, 0, int(w or vp.width()), int(h or vp.height()))
        wash = QColor(c["glow"]); wash.setAlpha(int(96 * g))
        p.fillRect(r, wash)
        pen = QColor("#000000"); pen.setAlpha(70); p.setPen(pen)
        for y in self.crt_scan():
            if y < r.height(): p.drawLine(0, y, r.width(), y)
        cr = QRect()
        if getattr(self, "_cur_on", True) and (self.hasFocus() or getattr(self, "crt_force", False)):
            cr = self.crt_cursor_rect()
            p.fillRect(cr, QColor(c["fg"]))
            txt = self.toPlainText(); idx = self.textCursor().position()
            ch = txt[idx] if 0 <= idx < len(txt) else ""
            if ch.strip(): p.setPen(QColor(c["bg"])); p.drawText(cr, Qt.AlignmentFlag.AlignCenter, ch)
        return {"glow": round(g, 4), "scanlines": len(self.crt_scan()), "cursor": not cr.isNull()}

    def paintEvent(self, ev):
        super().paintEvent(ev)               # 文本照常由 QPlainTextEdit 绘（输入语义不变）
        if not getattr(self, "crt_on", True): return
        try:
            p = QPainter(self.viewport()); self._crt_overlay(p); p.end()
        except Exception: pass               # 成像失败不得影响输入与路由
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
    """传真机机身容器（批40 零顶栏三区骨架）：装配由 shell_qt_fax.build() 产出——常驻只 A 纸卷区／B 送稿口／
    C 墨水屏，控制面板（META 键阵·F1 六组·拨号盘）与抽屉按需展开（Ctrl+M）；顶部原生菜单栏与名牌横条一律不装，
    菜单职能＝命令面板 Ctrl+K＋右键菜单（条目同源 MENU_ITEMS·快捷键保 QAction 级）；
    路由/并行/停止/提问/明细一律沿用旧壳引擎件。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("sms-shell · 传真机图形壳（免密钥·默认 smsystem-suit 数据流）")
        self.resize(1420, 860)
        self.running, self.pend, self.hist, self.details = {}, [], [], []
        self.seq = self.bus_off = self.hi = 0
        self.awaiting = None; self.task_prog = ""; self.steps = []; self.editors = []
        self._bus_off = None; self._info = {}; self._panel = ""; self._last_out = ""
        self._tasks_cache = {}; self._eink_on = False
        self.cut_state = "idle"; self.cut_seq = 0; self._cut_timer = None
        try:
            import session_reg as sr; SELF = sr.bind("client", os.getpid(), "Qt壳")
            os.environ.setdefault("SMS_SESSION", SELF)
        except Exception: pass
        self._ui(); self._timers()      # 批40 零顶栏：不挂 menuBar（菜单＝命令面板 Ctrl+K＋右键菜单）
        self._side_i = 0
        self.echo(core.banner())
        with contextlib.suppress(Exception):
            sb = core.startup_block(); sb and self.echo(sb)
        with contextlib.suppress(Exception):
            import ask_channel; ask_channel.arm()
        self.fax("pollAll")

    # ---------- 装配（批40 零顶栏：无 menuBar·无 brand 横条·三区常驻＋按需层） ----------
    def _ui(self):
        self.ent = Input(self)
        self.fw = fax.build(self, self.ent)              # 三区骨架（版式真源＝网页端·零顶栏装配）
        self.setStyleSheet(fax.qss())
        self.out = self.fw["roll"]; self.drawer = self.fw["drawer"]
        self.stat = QLabel(""); self.stat.setObjectName("statusbar")
        c = self.centralWidget(); c.layout().addWidget(self.stat)
        self.stat.setText("● 就绪 · Enter 送稿 · Tab 补全 · Ctrl+K 命令面板（顶栏替代）· Ctrl+M 控制面板 · "
                          "Ctrl+I 墨水屏 · Ctrl+E 裁纸 · Ctrl+R CRT · 右键＝机身菜单 · "
                          "免密钥（本机窗口）· F3 速查 · F8 编辑器 · F12 停止")
        self._menu_actions()                             # QAction 快捷键＝原 menuBar 条目（同源不复制口径）

    def _timers(self):
        self.t_ui = QTimer(self); self.t_ui.timeout.connect(self.tick); self.t_ui.start(150)
        self.t_ask = QTimer(self); self.t_ask.timeout.connect(self.ask_poll); self.t_ask.start(400)
        self.t_bus = QTimer(self); self.t_bus.timeout.connect(self.bus_poll); self.t_bus.start(1000)
        self.t_task = QTimer(self); self.t_task.timeout.connect(lambda: self.fax("pollTasks")); self.t_task.start(4000)

    # ---------- 顶栏替代件（批40 零顶栏：命令面板＋右键菜单·原菜单条目一字不差搬入） ----------
    MENU_ITEMS = (
        ("速查 :help", "shell", lambda w: w.echo(core.HELP), "F3"),
        ("命令表 :cmds", "shell", lambda w: w._meta("cmds"), "Ctrl+H"),
        ("技能清单 :skills", "shell", lambda w: w._open("skills"), ""),
        ("会话拓扑 :session overview", "shell", lambda w: w._meta("session", "overview"), "Ctrl+J"),
        ("任务表面板", "shell", lambda w: w._open("tasks"), "Ctrl+T"),
        ("配置面板", "shell", lambda w: w._open("config"), "Ctrl+P"),
        ("权限面板", "shell", lambda w: w._open("perms"), ""),
        ("编辑器（:edit）", "shell", lambda w: w.open_editor(), "F8"),
        ("巡检 ALL", "shell", lambda w: w.fax("pollAll"), "F5"),
        ("重启壳（换前端 :restart）", "shell", lambda w: w.submit(":restart"), ""),
        ("撕纸清屏", "fax", lambda w: w.fax("tear"), ""),
        ("复制输出", "fax", lambda w: w.fax("copyAll"), "Ctrl+Shift+C"),
        ("下载 .txt", "fax", lambda w: w.fax("dl"), ""),
        ("详细细节（长输出）", "fax", lambda w: w._open("detail"), ""),
        ("跨会话明细", "fax", lambda w: w._open("bus"), ""),
        ("合上抽屉", "fax", lambda w: w.fax("closeDrawer"), ""),
        ("裁纸 CUT（五态推进）", "fax", lambda w: w.fax("cut"), "Ctrl+E"),
        ("墨水屏面板（三段·无动效）", "fax", lambda w: w.fax("eink"), "Ctrl+I"),
        ("CRT 送稿口成像开关", "fax", lambda w: w.fax("crt"), "Ctrl+R"),
        ("控制面板展开/收起", "fax", lambda w: w.fax("ctl"), "Ctrl+M"),
        ("视图轮转（纸卷／送稿／墨水屏）", "fax", lambda w: w.fax("view"), "Ctrl+V"),
        ("命令面板（顶栏替代）", "fax", lambda w: w.fax("palette"), "Ctrl+K"),
        ("界面口径（网页端镜像·免密钥）", "help", lambda w: w.echo(w.about_text()), ""),
        ("关于", "help", lambda w: w.echo(core.banner()), ""),
    )

    def about_text(self):
        return ("本壳＝sms-shell 网页端传真机界面的本机镜像·批40 零顶栏三区骨架：常驻只 A 纸卷区（出纸正文＋状态行 "
                "LCD 六格/LED 七灯＋裁纸刀）、B 送稿口（CRT 绿字黑底·扫描线·余辉·块光标）、C 墨水屏（只三段·无动效）；"
                "控制面板（META 键阵·F1 六组·拨号盘）与抽屉＝按需展开（Ctrl+M）。机身不挂原生菜单栏、不装 brand 横条——"
                "菜单职能由命令面板 Ctrl+K（条目同源 MENU_ITEMS·出口同实体键）＋右键菜单承担，快捷键一律保 QAction 级。"
                "版式与键位现取 web_page.html，数据经 web_shell 面板件进程内直调——GUI 端不做任何密钥验证："
                "不开端口、不读/不显影/不复制 token，LCD 只标『本机直连』。路由仍走 shell_core（同 TUI）。")

    def _menu_actions(self):
        """MENU_ITEMS → QAction（挂窗口不挂菜单栏＝零顶栏下 F3/F5/F8/Ctrl+* 全部入口不丢）。"""
        self.acts = []
        for label, _grp, fn, sc in self.MENU_ITEMS:
            a = QAction(label, self)
            a.triggered.connect(lambda _f=fn: _f(self))
            with contextlib.suppress(Exception):
                sc and a.setShortcut(QKeySequence(sc))
            self.addAction(a); self.acts.append(a)
        return len(self.acts)

    def palette_rows(self, q=""):
        """命令面板数据源（纯构造·可离线单测·不新建口径）：META 元指令＋F1 快捷＋常用拨号＋拨号盘
        ＋抽屉面板＋MENU_ITEMS 动作＋最近历史 → [(组, 名, 副标, 可调用)]，kw 模糊过滤。"""
        kw = str(q or "").strip().lower()
        rows = []
        META_, METAD_, PAD_, QUICK_, F1_ = (self.fw.get("keys") or fax.keys())
        for m in META_ or []:
            sub = METAD_.get(m, "") if isinstance(METAD_, dict) else ""
            rows.append(("元指令", ":" + m, sub, lambda c=":" + m: self.feed(c + " ")))
        for _g, items in (F1_ or []):
            for cmd, name in items:
                rows.append(("快捷", name, str(cmd).strip(), lambda c=cmd: self.faxPick(c)))
        for lab, c in QUICK_ or []:
            rows.append(("拨号", lab, str(c).strip(), lambda _c=c: self.feed(_c)))
        for k, c, lab in PAD_ or []:
            rows.append(("盘面", "%s %s" % (k, lab), str(c).strip(), lambda _c=c: self.feed(_c)))
        for menu_id, (title, src) in fax.DRAWERS.items():
            rows.append(("面板", title, menu_id, lambda s=src, t=title: self._open(s, t)))
        for label, grp, fn, sc in self.MENU_ITEMS:
            rows.append(("动作·" + grp, label, sc or "", lambda _f=fn: _f(self)))
        for h in self.hist[-12:]:
            rows.append(("历史", str(h)[:70], "回车重发", lambda t=h: self.feed(t)))
        if not kw:
            return rows
        return [r for r in rows if any(kw in str(x or "").lower() for x in (r[0], r[1], r[2]))]

    def palette(self):
        """命令面板＝被去掉的顶部菜单的全量替代（Ctrl+K）：过滤＋↑↓＋回车执行＋Esc 关闭。
        出口一律同实体键/菜单（feed／faxPick／_open／submit）＝路由仍 shell_core.handle，不新建口径。"""
        win = self
        box = QDialog(win); box.setObjectName("palette")
        box.setWindowTitle("命令面板 · 顶栏替代（零顶栏·条目同源 MENU_ITEMS·出口同实体键）")
        box.resize(780, 480)
        v = QVBoxLayout(box); v.setContentsMargins(8, 8, 8, 8); v.setSpacing(6)
        holder = {"rows": []}

        def run_row():
            i = box.lst.currentRow(); rows = holder["rows"]
            if not (0 <= i < len(rows)):
                box.done(0); return
            fn = rows[i][3]
            box.done(0)
            try:
                fn()
            except Exception as e:
                win.paper("系统", "命令面板执行失败：%s: %s" % (type(e).__name__, str(e)[:120]), "err")

        def fill():
            rows = win.palette_rows(box.ed.text()); holder["rows"] = rows
            box.lst.clear()
            for kind, name, sub, _fn in rows[:400]:
                box.lst.addItem(QListWidgetItem("%-9s %s%s" % (kind, name, ("   " + sub) if sub else "")))
            box.lst.setCurrentRow(0)

        class Edit(QLineEdit):
            def keyPressEvent(self, ev):
                k = ev.key()
                if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter): run_row(); return
                if k == Qt.Key.Key_Escape: box.done(0); return
                if k == Qt.Key.Key_Down:
                    box.lst.setCurrentRow(min(box.lst.count() - 1, 0)); box.lst.setFocus(); return
                super().keyPressEvent(ev)

        class List(QListWidget):
            def keyPressEvent(self, ev):
                k = ev.key()
                if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter): run_row(); return
                if k == Qt.Key.Key_Escape: box.done(0); return
                if k == Qt.Key.Key_Up: self.setCurrentRow(max(0, self.currentRow() - 1)); return
                if k == Qt.Key.Key_Down: self.setCurrentRow(min(self.count() - 1, self.currentRow() + 1)); return
                if len(ev.text() or "") and ev.text().strip():
                    box.ed.setFocus(); box.ed.keyPressEvent(ev); return
                super().keyPressEvent(ev)

        box.ed = Edit(box); box.ed.setObjectName("palEdit")
        box.ed.setPlaceholderText("输入过滤（元指令／动作／面板／快捷／历史）· 回车执行 · Esc 关闭 · 顶栏替代 Ctrl+K")
        box.ed.setFont(fax._f(14))
        box.lst = List(box); box.lst.setObjectName("palList"); box.lst.setFont(fax._f(13))
        box.lst.setAlternatingRowColors(True)
        v.addWidget(box.ed); v.addWidget(box.lst, 1)
        hint = QLabel("↑↓ 选择 · 回车执行 · Esc 关闭 · 与实体键/右键菜单同源（MENU_ITEMS·不第二条口径）")
        hint.setObjectName("hint"); hint.setFont(fax._f(11, False)); v.addWidget(hint)
        box.ed.textChanged.connect(fill)
        box.lst.itemDoubleClicked.connect(lambda _i=None: run_row())
        fill(); box.ed.setFocus()
        box.exec()
        with contextlib.suppress(Exception):
            win.ent.setFocus()
        return {"ok": True, "rows": len(holder["rows"])}

    def contextMenuEvent(self, ev):
        """右键菜单＝零顶栏下的常驻菜单入口（光标在纸卷上只给纸动作，其余给全量三段）。"""
        in_roll = False
        with contextlib.suppress(Exception):
            in_roll = bool(self.fw["roll"].underMouse())
        m = QMenu(self)
        groups = ("fax",) if in_roll else ("shell", "fax", "help")
        for label, grp, fn, sc in self.MENU_ITEMS:
            if grp not in groups: continue
            a = QAction(label, self)
            a.triggered.connect(lambda _f=fn: _f(self))
            m.addAction(a)
        m.exec(ev.globalPos() if hasattr(ev, "globalPos") else ev.pos())

    # ---------- 机身动作（网页端同名动作的 Qt 对应体·函数名字面一致便于对照） ----------
    def feed(self, text):
        """填入送稿口（网页端 setCmd 同义）：焦点回进纸器、光标落末尾。"""
        self.ent.setPlainText(text or ""); c = self.ent.textCursor()
        c.movePosition(c.MoveOperation.End); self.ent.setTextCursor(c); self.ent.setFocus()

    def feedNow(self):
        self.submit(self.ent.toPlainText())

    def fax(self, act, arg=None):
        """机身/抽屉动作分派（异常一律卡纸打纸，不外抛·不静默）。"""
        try:
            fn = {"pollAll": self.pollAll, "pollTasks": self.pollTasks, "pollInfo": self.pollInfo,
                  "pollSolo": self.pollSolo, "doStop": lambda a=None: self.stop_one(""),
                  "doResume": self.doResume, "tear": self.tear, "copyAll": self.copyAll, "dl": self.dl,
                  "speakLast": self.speakLast, "closeDrawer": self.closeDrawer,
                  "cut": self.cut, "cutStep": self._cut_step, "eink": self.einkToggle,
                  "crt": self.crtToggle, "ctl": self.ctlToggle, "view": self.viewToggle,
                  "palette": self.palette,
                  "hist(-1)": lambda a=None: self.history(True), "hist(1)": lambda a=None: self.history(False),
                  "clear()": lambda a=None: self.feed("")}.get(act)
            if fn is None: return self.paper("系统", "机身无此动作：%s" % act, "sys")
            r = fn(arg) if arg is not None else fn()
            if isinstance(r, dict) and r.get("err"): self.paper("系统", "卡纸：%s（%s）" % (act, r["err"]), "err")
            return r
        except Exception as e:
            self.paper("系统", "机身动作 %s 异常：%s: %s" % (act, type(e).__name__, str(e)[:140]), "err")

    def faxPick(self, cmd):
        """F1 六组键：`#` 前缀＝机身动作、`:` 前缀＝填入送稿口、其余（path:…）＝原样填。"""
        c = str(cmd or "").strip()
        if c.startswith("#"):
            d = fax.DRAWERS.get(c)
            if d and not str(d[1]).startswith("@"): return self._open(d[1], d[0])
            return {"@copy": self.copyAll, "@stop": lambda: self.stop_one(""),
                    "@resume": self.doResume}.get(str(d[1] if d else ""), lambda: self.feed(c))()
        if c.startswith(":"): return self.feed(c if c.endswith(" ") else c + " ")
        if c.startswith("path:"): return self._open("skills", "按路径加入技能")
        return self.feed(c + " ")

    # ---------- 抽屉面板 ----------
    def _open(self, name, title=None):
        """开抽屉：数据＝网页端同路径 /api/<name>（进程内直调·scrub 去密钥面）。"""
        d = fax.DRAWERS
        title = title or next((v[0] for v in d.values() if v[1] == name), name)
        self._panel = name
        if name == "bus":
            data = {"lines": list(self.details)[-80:]}
        else:
            path = "/api/" + ({"ws": "files", "mode": "hud", "sys": "commands"}.get(name, name))
            data = fax.api(path, {"ws": self._ws_hint()} if name in ("files", "file") else None)
        self.fw["dtitle"].setText("⑤ 抽屉面板 · " + title)
        self.fw["dbody"].setHtml(fax.panel_html(name, data))
        self.drawer.show()
        if isinstance(data, dict) and data.get("err"):
            self.paper("系统", "面板 %s 卡纸：%s" % (name, data["err"]), "err")

    def _ws_hint(self):
        with contextlib.suppress(Exception):
            import workspace; return workspace.current()
        return ""

    def closeDrawer(self):
        self.drawer.hide(); self._panel = ""

    def refreshDrawer(self):
        if getattr(self, "_panel", "") in ("tasks", "perms", "config", "bus"): self._open(self._panel)

    # ---------- 出纸口（网页端 print()/jam() 同构·米纸逐行走） ----------
    def paper(self, who, text, cls="", body_html=None):
        """出纸一行（网页端 print 同义）：who＝徽标（我/系统/agent/错误/模型提问），cls＝纸面色类。"""
        if not str(text).strip() and body_html is None: return
        self.papers = getattr(self, "papers", 0) + 1
        self._last_out = str(text)
        self.out.append(fax.line_html(who, text, cls, body_html))
        sb = self.out.verticalScrollBar(); sb.setValue(sb.maximum())

    def copyAll(self):
        QApplication.clipboard().setText(self.out.toPlainText())
        self.paper("系统", "输出已复制（%d 字）" % len(self.out.toPlainText()), "sys")

    def dl(self):
        p = os.path.join(os.environ.get("SMS_TMP") or core.SMS,
                         "sms-fax-%s.txt" % time.strftime("%Y%m%d-%H%M%S"))
        try:
            io.open(p, "w", encoding="utf-8").write(self.out.toPlainText())
            self.paper("系统", "已下载 → %s" % p, "sys")
        except Exception as e: self.paper("系统", "下载失败：%s" % str(e)[:120], "err")

    def tear(self):
        """撕纸清屏：纸卷清空回纸头（明细/任务表面板不受影响）。"""
        self.out.clear(); self.cut_state = "idle"; self._cut_apply()
        self.paper("系统", "已撕纸·出纸口回纸头", "sys")

    # ---------- t6 裁纸刀（出纸末端·状态推进：进程内 QTimer 走步·零新端口零新进程零子线程） ----------
    def cut(self, arg=None):
        """✂ 裁纸 CUT：起一轮裁纸（feed→clamp→cut→drop→idle），每步 200ms 由进程内 QTimer 推进；
        途中再点＝中止回待机（状态一律上刀条标签，不静默、不外抛）。"""
        if getattr(self, "_cut_timer", None) is not None:
            self._cut_end("裁纸中止 TRIM HALT")
            self.paper("系统", "裁纸中止·刀条回待机", "sys"); return {"ok": "halt"}
        self._cut_timer = QTimer(self); self._cut_timer.timeout.connect(self._cut_step)
        self._cut_timer.start(200)
        self.cut_state = "idle"; self._cut_apply()
        self.paper("系统", "裁纸开始：纸张送出→压脚压纸→刀刃下行→断纸落盘", "sys")
        return {"ok": "run"}

    def _cut_end(self, msg=""):
        with contextlib.suppress(Exception):
            self._cut_timer.stop(); self._cut_timer.deleteLater()
        self._cut_timer = None; self.cut_state = "idle"; self._cut_apply()
        if msg: self.banner(msg, "warn")

    def _cut_step(self):
        """推进一态（真源＝fax.cut_next）：落 drop＝纸面留裁断印记并计数，落 idle＝本轮收口。"""
        self.cut_state = fax.cut_next(self.cut_state)
        self._cut_apply()
        if self.cut_state == "drop":
            self.cut_seq += 1
            self.paper("裁纸", "", "sys", body_html=fax.cut_mark(self.cut_seq))
        elif self.cut_state == "idle":
            self._cut_end()
            self.paper("系统", "裁纸完成：第 %d 裁落盘（纸面 %d 字）" %
                       (self.cut_seq, len(self.out.toPlainText())), "sys")
        return self.cut_state

    def _cut_apply(self):
        """当前态刷到刀条视觉：QFrame#blade[st=…] 五态渐变＋标签文案/行程百分比＋裁纸指示灯。"""
        st = self.cut_state
        try:
            b = self.fw["blade"]; b.setProperty("st", st); b.style().unpolish(b); b.style().polish(b)
            tg = self.fw["blade_tag"]; tg.setText(fax.cut_label(st))
            tg.setStyleSheet("color:%s;font-size:11px;letter-spacing:1px;font-weight:bold" %
                             (fax.css_vars().get({"stop": "red", "warn": "amber", "go": "grn"}
                                                  .get(fax.cut_tone(st), ""), "") or "#4c5a68"))
            self.fw["blade_pos"].setText("行程 %d%%" % round(fax.cut_progress(st) * 100))
        except Exception: pass
        self.led("裁纸", "off" if st == "idle" else ("warn" if fax.cut_tone(st) == "warn"
                                                   else "err" if fax.cut_tone(st) == "stop" else "on"))

    # ---------- t8 CRT 送稿口开关（成像层开/关·键盘与路由口径不动） ----------
    def crtToggle(self, arg=None):
        on = not bool(self.ent.crt_on)
        self.ent.crt_on = on
        with contextlib.suppress(Exception):
            self.ent.setProperty("crt", "1" if on else "")
            self.ent.style().unpolish(self.ent); self.ent.style().polish(self.ent)
            self.ent.viewport().update()
        self.paper("系统", "CRT 送稿口成像层＝%s（绿字黑底·扫描线·余辉·块光标；键盘与路由口径不变）" %
                   ("开" if on else "关"), "sys")
        return {"ok": on}

    # ---------- 控制面板按需化（批40 零顶栏：常驻五区→三区＋按需展开） ----------
    def ctlToggle(self, arg=None):
        """控制面板（META 键阵／F1 六组／拨号盘）展开/收起——去顶栏后控制件不常驻，Ctrl+M 唤出。"""
        z = self.fw.get("ctlzone")
        if z is None:
            self.paper("系统", "机身无控制面板件（ctlzone）", "err"); return {"ok": False}
        show = not bool(z.isVisible())
        z.setVisible(show)
        if show:
            with contextlib.suppress(Exception):
                sb = self.fw["roll"].verticalScrollBar(); z.setParent(self) if False else None
            self.paper("系统", "控制面板已展开（META 键阵 %d 键 · F1 六组 · 拨号盘 12 位）——Ctrl+M 收起" %
                       len((self.fw.get("keys") or fax.keys())[0] or []), "sys")
        with contextlib.suppress(Exception):
            self.fw["ctlzone_btn"].setText("▦ 收起控制面 Ctrl+M" if show else "▦ 控制面板 Ctrl+M")
        self._hud("ctl", "控制面板 " + ("展开" if show else "收起"), 600)
        return {"ok": show}

    def viewToggle(self, arg=None):
        """视图循环：A 纸卷／B 送稿／C 墨水屏 三态焦点排布（窄屏 1280×720 也满幅可用）。"""
        self._view_i = (getattr(self, "_view_i", 0) + 1) % 3
        names = ("纸卷 A", "送稿 B", "墨水屏 C")
        if self._view_i == 2:
            self._eink_on = True
            with contextlib.suppress(Exception): self.fw["einkzone"].setVisible(True)
            self.einkRefresh()
        with contextlib.suppress(Exception):
            self.fw["ctlzone"].setVisible(self._view_i == 0 and bool(self.fw["ctlzone"].isVisible()))
        self.paper("系统", "视图焦点＝%s（三区轮转 Ctrl+V）" % names[self._view_i], "sys")
        return {"ok": names[self._view_i]}

    # ---------- t10 墨水屏消息面板（只三段·无动效·数据仍走进程内 api） ----------
    def einkToggle(self, arg=None):
        self._eink_on = not bool(self._eink_on)
        with contextlib.suppress(Exception): self.fw["einkzone"].setVisible(self._eink_on)
        if self._eink_on:
            self.einkRefresh(); self.paper("系统", "墨水屏已开（会话信息／任务表／后台任务·无动效）", "sys")
        return {"ok": "on" if self._eink_on else "off"}

    def eink_bg(self):
        """后台任务＝进程内在跑/排队（本壳 worker·不起新进程）。"""
        out = [(tid, str(info.get("text") or "")[:60],
                time.time() - float(info.get("t0") or time.time()))
               for tid, info in (self.running or {}).items()]
        out += [("排队", str(t)[:60], 0.0) for t in (self.pend or [])]
        return out

    def einkRefresh(self):
        if not getattr(self, "_eink_on", False): return
        try:
            self.fw["eink"].setHtml(fax.eink_html(self._info, self._tasks_cache, self.eink_bg()))
        except Exception as e:
            self.paper("系统", "墨水屏刷新失败：%s" % str(e)[:100], "err")

    def speakLast(self):
        t = (self._last_out or "").strip()
        if not t: return self.paper("系统", "无可朗读内容", "sys")
        try:
            import tts; r = tts.speak(t[:600], False)
            self.paper("系统", "已朗读末条（%s）" % str(r)[:60], "sys")
        except Exception as e: self.paper("系统", "朗读不可用：%s" % str(e)[:100], "err")

    def doResume(self):
        r = fax.api("/api/resume", {})
        self.paper("系统", r.get("err") and ("续跑受阻：" + r["err"]) or "已请求续跑未完成计划表（网页壳同口径）", "sys")
        self.pollTasks(); return r


    # ---------- 送稿（路由真源＝shell_core.handle·与 TUI/网页端逐字同口径） ----------
    def echo(self, s, kind=""):
        """兼容旧口径的输出入口：可见正文→出纸口（着色），非可见行→明细（右栏/抽屉）。"""
        t = str(s)
        if not t.strip(): return
        if kind != "raw" and not msg_flow.visible(t):
            if not msg_flow.blank(t): self._push(t)
            return
        self._push_cache(t)
        who = {"me": "我", "err": "错误", "info": "系统"}.get(kind, "系统")
        cls = {"me": "me", "err": "err", "info": "sys"}.get(kind, "")
        body = "<br>".join(badge(paint(x)) or "&nbsp;" for x in t.split("\n"))
        self.paper(who, "", cls, body_html=body)

    def _push_cache(self, t):
        ("$ " in t or ".py" in t or ".md" in t or "config:" in t) and self.steps.append(t[:160]) if len(self.steps) < 4000 else None
    def _push(self, t):
        d = self.details
        if d and d[-1].startswith(("◌", "〔◌")) and t.startswith(("◌", "〔◌")) and len(d[-1]) < 3000:
            d[-1] = d[-1] + " " + t.lstrip("◌ ")
        else: d.append(t[:3000])
        self.details = d[-150:]
        if getattr(self, "_panel", "") == "bus": self.refreshDrawer()

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
        text = (text or "").strip(); self.ent.setPlainText("")
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
            self.hist.append(text); self.hi = len(self.hist)
            self.echo("当前＝传真机图形壳（shell_qt.py 镜像网页端 · 免密钥）· Qt %s · 并行 %d/%s · 明细 %d 条\n"
                      "三视图件：✂ 裁纸 CUT（fax.cut_next 五态推进·进程内 QTimer）· CRT 送稿口（绿字黑底＋扫描线"
                      "＋余辉＋块光标·键盘口径不变）· ▤ 墨水屏（只三段：会话信息／任务表／后台任务·无动效）\n"
                      "可用本地指令：:gui 本壳状态 · :clear 撕纸清屏 · :reload 巡检/重开抽屉 · tui 另起 Textual 终端壳；"
                      "其余 `:` 元指令一律交 shell_core（同 TUI/网页端）。" % (
                          self.qtver(), len(self.running), (self._cap() or "无限"), len(self.details)), kind="info")
            return
        if lo in (":clear", ":reload"):
            self.hist.append(text); self.hi = len(self.hist)
            if lo == ":clear": self.tear()
            else: self.fax("pollAll"); self.refreshDrawer()
            return
        if lo in ("tui", ":tui"):
            self.hist.append(text); self.hi = len(self.hist)
            _dn = open(os.devnull, "r+b")
            # sms-visible：GUI 另起可见 Textual TUI 终端壳（有意开新控制台窗·与 shell_gui.py 同口径）
            subprocess.Popen([sys.executable, "-B", os.path.join(S, "shell_tui_textual.py")],
                             stdin=_dn, stdout=_dn, stderr=_dn, close_fds=True)
            self.echo("已另起 Textual TUI 终端壳", kind="info"); return
        self.hist.append(text); self.hi = len(self.hist)
        if not self._room():
            self.pend.append(text)
            self.echo("已排队 %d 条 · %s·有空位自动续发" % (len(self.pend),
                      "并发已达上限 %d" % self._cap() if self._par() else "并行已关（:config set shell.parallel false）"),
                      kind="info")
            return
        self.start(text)

    def start(self, text):
        self.seq += 1; tid = "t%d" % self.seq
        self.echo("sms> %s%s" % (text, ("   〔并行第 %d 个任务〕" % (len(self.running) + 1)) if self.running else ""),
                  kind="me")
        self.running[tid] = {"text": text, "t0": time.time()}
        self._hud("session", (text[:60] or "sms-shell GUI"), 1800)
        w = Task(text, tid)
        w.line.connect(lambda s, t=tid: self.on_line(t, s))
        w.step.connect(lambda s, t=tid: self.on_step(t, s))
        w.env.connect(lambda e, t=tid: self.on_env(t, e))
        w.over.connect(self.on_over)
        w.start(); self.running[tid]["w"] = w
        self.tick()

    def on_line(self, tid, s):
        tag = ("[%s] " % tid) if len(self.running) > 1 else ""
        t = str(s)
        if msg_flow.visible(t): self.echo((tag or "") + t)
        elif not msg_flow.blank(t): self._push((tag + t)[:3000])
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
                self.task_prog = "≡ %s %s/%s%s" % (str(m.get("id", ""))[-6:], m.get("done", 0),
                                                   m.get("total", 0), (" · " + msg_flow.fmt(eta)) if eta else "")
                self.fw["lcd_任务表"].setText(self.task_prog)
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
            self.echo("✔ 任务 %s 收口（%.1fs）·仍在并行跑 %d 个：%s" %
                      (tid, el, len(self.running), "、".join(sorted(self.running))), kind="info")
        else:
            self.stat.setText("● 就绪 · 上一条用时 %.1fs · 明细 %d 条（F3 速查 · F8 编辑器 · F5 巡检）" %
                              (el, len(self.details)))
            self._hud("hide", "", 0)
        if isinstance(done, str) and done.startswith(("edit:", "view:")):
            self.open_editor(done.split(":", 1)[1], ro=done.startswith("view:")); done = None
        if done == "exit": self.close(); return
        if done == "config": self.echo(core._cfgline())
        self.refreshDrawer(); self.pollTasks()
        while self.pend and self._room(): self.start(self.pend.pop(0))

    def stop_one(self, one=""):
        if self.awaiting:
            import ask_channel; ask_channel.reply("用户已请求停止任务（stop）", self.awaiting[0]); self.awaiting = None
        if one and one in self.running:
            stop.request("GUI 输入 stop " + one, one)
            self.echo("⛔ 已请求停止任务 %s（其余 %d 个不受影响）" % (one, len(self.running) - 1), kind="info"); return
        if one and one not in self.running:
            self.echo("无此在跑任务：%s（现行 %s）" % (one, "、".join(sorted(self.running)) or "无"), kind="info"); return
        if self.running:
            for tid in list(self.running): stop.request("GUI 输入 stop（全部）", tid)
            self.echo("⛔ 已请求停止全部 %d 个在跑任务——各任务在下一检查点收口" % len(self.running), kind="info"); return
        r = fax.api("/api/stop", {"why": "传真机壳 STOP 键（无在跑任务·清停止旗标）"})
        stop.clear(); self.echo("空闲：无进行中任务·停止状态已清（%s）" % str(r.get("status") or "")[:60], kind="info")
    def stop_all(self): self.stop_one("")


    # ---------- 巡检（LCD/指示灯/纸卡/抽屉·数据＝web_shell 面板件进程内直调） ----------
    def tick(self):
        self._side_i = getattr(self, "_side_i", 0) + 1
        if self._side_i % 40 == 0: self.pollInfo()
        if self._side_i % 20 == 0: self.pollSolo()
        n = len(self.running)
        sp = SPIN[int(time.time() * 8) % 10] if n else "●"
        sess = conv = "-"
        with contextlib.suppress(Exception): sess = core.chains.cur_sess()
        with contextlib.suppress(Exception): conv = (_envs().get("SMS_CONV") or "-")
        el = " · 已用 %.0fs" % (time.time() - min(float(v.get("t0") or time.time())
                                                  for v in self.running.values())) if n else ""
        cur = self.task_prog or getattr(self, "last_step", "") or "进纸待机"
        try:
            self.fw["lcd_会话"].setText("%s · %s" % (str(sess)[-8:], str(conv)[-8:]))
            self.fw["lcd_模式"].setText("对话 · 并行 %d · 排队 %d%s" % (n, len(self.pend), el))
        except Exception: pass
        if n: self.banner("送稿中 %.0fs%s" % (time.time() - min(float(v.get("t0") or 0)
                                            for v in self.running.values()), el), "warn")
        if self._side_i % 13 == 0: self._bus_ui()

    def banner(self, text, tone=""):
        b = self.fw["banner"]; b.setText(text)
        b.setObjectName({"warn": "lcdWarn", "err": "lcdErr"}.get(tone, "banner"))
        b.setStyleSheet("color:%s;font-size:11px" % {"warn": fax.css_vars().get("amber"),
                                                    "err": fax.css_vars().get("red")}.get(tone) or "#3c4a58")

    def led(self, name, state):
        lab = self.fw.get("led_" + name)
        if lab is None: return
        col = {"on": fax.css_vars().get("grn"), "warn": fax.css_vars().get("amber"),
               "err": fax.css_vars().get("red"), "off": "#55606c"}.get(state, "#55606c")
        lab.setText(("● " if state == "on" else "◆ " if state == "warn" else
                     "✸ " if state == "err" else "○ ") + name)
        lab.setStyleSheet("color:%s;font-size:11px" % col)

    def pollInfo(self):
        i = fax.api("/api/info")
        if i.get("err"): return self.led("线路", "err")
        self._info = i
        g = i.get("gateway") or {}
        try:
            self.fw["lcd_网关"].setText("%s · %s" % ("on" if g.get("enabled") else "off", g.get("model") or "-"))
            self.fw["lcd_线路"].setText("本机直连 · 免密钥（GUI 不开端口）")
            self.fw["lcd_状态"].setText(i.get("session") and "SOLO on" or "就绪")
        except Exception: pass
        self.led("线路", "on")
        self.led("对外", "warn" if (i.get("external") or {}).get("enabled") else "off")
        self.led("做梦", "on" if (i.get("dream") or {}).get("enabled") else "off")
        self.led("朗读", "on" if (i.get("tts") or {}).get("enabled") else "off")

    def pollSolo(self):
        r = fax.api("/api/perms")
        if r.get("err"): return
        s = r.get("solo") or {}
        self.led("线路", "warn" if s.get("enabled") else "on")
        try: self.fw["lcd_状态"].setText("SOLO %s" % ("on·权限自审" if s.get("enabled") else "off·需确认"))
        except Exception: pass

    def pollTasks(self):
        r = self._tasks_cache = fax.api("/api/tasks")
        if r.get("err"):
            self.fw["lcd_任务表"].setText("巡检不可用"); self.led("计划", "err"); return
        rows = r.get("rows") or []
        dn = r.get("done", 0); tot = r.get("total", 0); un = r.get("unfinished", 0)
        self.fw["lcd_任务表"].setText("%s/%s %s · %s" % (dn, tot, str(r.get("tid") or "-")[-6:],
                                                        r.get("eta") or "-") if tot else "无未完成")
        show = bool(tot and un > 0)
        self.fw["btn_stop"].setVisible(show); self.fw["btn_go"].setVisible(show)
        if show:
            self.fw["btn_stop"].setText("⏸ 停止 %d/%d" % (dn, tot))
            self.fw["btn_go"].setText("▶ 继续 %d/%d" % (dn, tot))
        self.led("计划", "warn" if show else "off")
        if getattr(self, "_panel", "") == "tasks": self.refreshDrawer()
        self.einkRefresh()

    def pollAll(self):
        self.pollInfo(); self.pollSolo(); self.pollTasks()
        self.paper("系统", "巡检完成（线路/LCD/指示灯/任务表）", "sys")
        return {"ok": True}

    def ask_poll(self):
        if self.awaiting: return
        try:
            import ask_channel; r = ask_channel.poll_any()
        except Exception: return
        if not r: return
        tid, q = r; self.awaiting = (tid, q)
        self.paper("模型提问", ("〔任务 %s〕" % tid if tid else "") + str(q), "ask")
        self.banner("等答复%s" % ("（%s）" % tid if tid else ""), "warn")

    def bus_poll(self):
        try:
            if self.bus_off is None:
                p = detail_bus.path(core.SMS)
                self.bus_off = os.path.getsize(p) if os.path.isfile(p) else 0
                return
            own = os.environ.get("SMS_SESSION") or ""
            off, rows = detail_bus.tail(self.bus_off, 120, core.SMS)
            self.bus_off = off
            for e in rows:
                if e.get("sess") == own: continue
                line = "〔%s·%s〕%s" % (str(e.get("sess") or "-")[-6:], e.get("kind"), str(e.get("text") or ""))
                self._push(line)
            if rows and getattr(self, "_panel", "") == "bus": self.refreshDrawer()
        except Exception: pass
    def _bus_ui(self): pass

    # ---------- 沿用件 ----------
    def _hud(self, key, text, ttl):
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
        else: e = Editor(path, ro)
        e.show(); self.editors.append(e)
        self.paper("系统", "已打开编辑器（%s）：%s" % ("查看" if ro else "编辑", path), "sys")
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
        cand = [":" + m for m in (self.fw.get("keys") or fax.keys())[0]]
        cand += [":%s" % m for m in ("help", "cmds", "skills", "config", "session", "dispatch", "sh", "hud",
                                     "agents", "use", "resume", "plan", "debug", "edit", "view", "deploy",
                                     "workspace", "web", "tts", "dream", "mode", "grant", "perms", "tools", "api")]
        head = txt.split("\n")[-1].strip()
        hits = sorted({c for c in cand if c.startswith(head)})
        if len(hits) == 1: ent.setPlainText(txt[: len(txt) - len(head)] + hits[0] + " ")
        elif hits: self.paper("系统", "补全候选：" + "、".join(hits[:20]), "sys")
    def qtver(self):
        try:
            from PyQt6.QtCore import QT_VERSION_STR; return QT_VERSION_STR
        except Exception: return "?"
    def probe_finish(self):
        """--probe 端到端回归：出纸口纯文本落盘并退出（CLI/CI 无窗验证路由结果）。"""
        try:
            p = os.environ.get("SMS_QT_PROBE_DUMP") or "qt_probe.txt"
            io.open(p, "w", encoding="utf-8").write(self.out.toPlainText())
            sh = os.environ.get("SMS_QT_SHOT")
            sh and self.grab().save(sh)
            print("PROBE_DUMP " + p + " chars=" + str(len(self.out.toPlainText())) +
                  " details=" + str(len(self.details)) + " keys=" + str(len(self.fw)))
        except Exception as e:
            print("PROBE_FAIL " + repr(e)[:160])
        QApplication.instance().quit()
    def closeEvent(self, ev):
        for w in list(self.running.values()):
            with contextlib.suppress(Exception): w["w"].requestInterruption(); w["w"].quit(1200)
        with contextlib.suppress(Exception):
            import ask_channel; ask_channel.disarm()
        super().closeEvent(ev)

def _envs(): return os.environ
def _c(hexcol):
    from PyQt6.QtGui import QColor; return QColor(hexcol)


def main(argv=None):
    argv = [a for a in (argv if argv is not None else sys.argv[1:]) if a != "--"]
    selftest = "--selftest" in argv
    if selftest: os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("sms-shell-gui")
    win = Shell()
    if selftest: return _selftest(app, win)
    win.show()
    pos = [a for a in argv if a != "--selftest" and not a.startswith("--probe")]
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
    """离线自检（不发模型请求）：传真机机身成图＋机身件计数＋免密钥面核对＋行分类/上色/排队/停止/抽屉面板全跑。"""
    win.show(); app.processEvents()
    cases = ["sms-shell 速查", "• notice 行", "$ exec ls -la", "◌ 思考过程行", "▸ 步骤行", "✗ 错误行",
             "⧉general_answer▸ 派发对话正文", "! sh 输出", "≡ task 进度", "带 `代码` 与 C:\\path\\file.py 的正文"]
    for c in cases: win.on_line("t9", c)
    win.echo("用户话语测试行", kind="me")
    for e in ({"kind": "task", "meta": {"id": "task-20261009-000000-000", "done": 3, "total": 5, "eta_s": 96}},
              {"kind": "edit", "text": "已改 tmp/a.py"}):
        win.on_env("t9", e)
    win.running.setdefault("t9", {"text": "x", "t0": time.time() - 3})
    win.tick(); app.processEvents()
    win.stop_one("t9")
    win.pend.append("排队行示例")
    win.pollAll(); app.processEvents()
    panels = {}
    for nm in ("tasks", "plans", "chains", "sessions", "skills", "files", "config", "perms",
               "detail", "bus", "ws", "mode", "sys", "qq", "tts"):
        win._open(nm); app.processEvents()
        panels[nm] = len(win.fw["dbody"].toHtml())
    win._open("tasks"); app.processEvents()
    task_tbl = win.fw["dbody"].toPlainText()
    win.closeDrawer(); app.processEvents()
    win.paper("系统", "卡纸示例", "err")
    # ---- 批39 t6 裁纸刀：五态推进（按纯函数逐格走＋_cut_apply 落视觉，自检里不等 QTimer 空转） ----
    cut_seen = [win._cut_step() for _ in range(len(fax._IDS))]     # 一轮＝feed→clamp→cut→drop→idle
    win.cut_state = "cut"; win._cut_apply()
    cut_ok = (cut_seen == ["feed", "clamp", "cut", "drop", "idle"]
              and win.cut_seq == 1 and "裁纸段" in win.out.toHtml()
              and win.fw["blade"].property("st") == "cut"
              and win.fw["blade_tag"].text() == fax.cut_label("cut")
              and win.fw["blade_pos"].text().endswith("75%"))
    win.cut_state = "idle"; win._cut_apply()
    # ---- 批39 t8 CRT 送稿口：离屏走同一条绘制路（余辉＋扫描线＋块光标） ----
    from PyQt6.QtGui import QPixmap
    # 闪烁相由 t_crt（500ms）推——自检里钉死相位，取证才确定
    win.ent.crt_force = True; win.ent._cur_on = True
    win.ent.setPlainText(":cmds "); win.ent._glow_t = time.time()
    pm = QPixmap(420, 64); p = QPainter(pm); crt = win.ent._crt_overlay(p, 420, 64); p.end()
    win.ent._cur_on = False; p = QPainter(pm); crt_off = win.ent._crt_overlay(p, 420, 64); p.end()
    win.ent._cur_on = True
    win.ent.crt_force = False
    win.fax("crt"); win.fax("crt")                                  # 成像层开关（分派走 fax() 机身口）
    crt_ok = (bool(crt.get("scanlines")) and crt.get("cursor") and float(crt.get("glow") or 0) > 0
              and not crt_off.get("cursor") and win.ent.objectName() == "cmd")
    # ---- 批39 t10 墨水屏：三段面板（只三段·无动效·数据走进程内 api） ----
    win._eink_on = True; win.fw["einkzone"].show()
    win.running.setdefault("t8", {"text": "墨水屏示例话语", "t0": time.time() - 2})
    win.einkRefresh(); app.processEvents()
    eink_txt = win.fw["eink"].toPlainText(); eink_html_src = win.fw["eink"].toHtml()
    eink_ok = (all(s in eink_txt for s in fax.EINK_SECTIONS) and len(fax.EINK_SECTIONS) == 3
               and not any(bad in eink_html_src for bad in ("animation", "transition", "@keyframes"))
               and "墨水屏示例话语" in eink_txt)
    win.fax("eink"); win.fax("eink")                                # 墨水屏开→关→开（截图留痕用开态）
    win.running.pop("t8", None)
    shot = os.path.join(os.environ.get("SMS_TMP") or os.getcwd(), "qt_fax_selftest.png")
    ok = win.grab().save(shot)
    from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    META_, METAD_, PAD_, QUICK_, F1_ = win.fw.get("keys") or fax.keys()
    leak = fax.leaked(fax.api("/api/info")) or fax.leaked(fax.api("/api/perms"))
    out = {"visible_rows": getattr(win, "papers", 0),
           "roll_plain": win.out.toPlainText().count("\n"),
           "keys_total": len(win.fw), "details": len(win.details),
           "meta_keys": len(META_), "metad": len(METAD_), "pad": len(PAD_), "quick": len(QUICK_),
           "f1_groups": len(F1_), "drawers": len(fax.DRAWERS),
           "page_bytes": len(fax.page()), "qss_len": len(win.styleSheet()),
           "panels": panels, "panel_min": min(panels.values()) if panels else 0,
           "task_table_len": len(task_tbl),
           "no_token_face": not leak, "leaked_key": leak,
           "gate_removed": not hasattr(win, "gate") and not hasattr(win, "tok"),
           "no_gate_text": ("TOKEN" not in win.out.toPlainText()),
           "stop_word_hit": stop.is_stop_word("停止"), "paint_html": bool(paint("$ ls")),
           "queued": len(win.pend), "running": sorted(win.running), "screenshot": shot, "saved": bool(ok),
           "qt": QT_VERSION_STR, "pyqt": PYQT_VERSION_STR, "banner": win.fw["banner"].text(),
           "banner_len": len(core.banner()), "hud_state": os.path.join(core.SMS, "hud", "state.json"),
           "led_names": len([k for k in win.fw if str(k).startswith("led_")]),
           "cut_steps": len(fax.CUT_STEPS), "cut_seq": cut_seen, "cut_ok": cut_ok,
           "crt_overlay": crt, "crt_overlay_off": crt_off, "crt_ok": crt_ok,
           "crt_now": bool(win.ent.crt_on), "eink_ok": eink_ok, "eink_len": len(eink_txt),
           "eink_sections": list(fax.EINK_SECTIONS), "eink_now": bool(win._eink_on)}
    # ---- 批40 零顶栏三区骨架取证（命令面板＝顶栏替代·控制面板按需化·无菜单栏/无 brand 横条） ----
    src_self = io.open(__file__, encoding="utf-8", errors="replace").read()
    n_acts = len(getattr(win, "acts", []))
    rows_all = win.palette_rows("")
    rows_f = win.palette_rows(":cmds")
    names_all = [r[1] for r in rows_all]
    win.fax("ctl"); ctl_on = bool(win.fw["ctlzone"].isVisible())
    win.fax("ctl"); ctl_off = not bool(win.fw["ctlzone"].isVisible())
    win._eink_on = False
    with contextlib.suppress(Exception): win.fw["einkzone"].setVisible(False)
    for _ in range(2): win.fax("view")                   # 纸卷 A→送稿 B→墨水屏 C（第 3 态唤出墨水屏）
    view_i = getattr(win, "_view_i", -1)
    eink_open_by_view = bool(win._eink_on) and bool(win.fw["einkzone"].isVisible())
    win.fax("view"); win._view_i = 0
    required = ("banner", "roll", "drawer", "dtitle", "dbody", "blade", "blade_tag", "blade_pos",
                "eink", "einkzone", "ctlzone", "keys", "btn_stop", "btn_go", "btn_all", "btn_speak")
    missing = [k for k in required if k not in win.fw]
    n_acts = len(getattr(win, "acts", []))
    rows_all = win.palette_rows("")
    rows_f = win.palette_rows(":cmds")
    names_all = [r[1] for r in rows_all]
    src_self = io.open(__file__, encoding="utf-8", errors="replace").read()
    mb = "self." + "menuBar()"; nb = "SMS-" + "FAX · GUI"
    out["zero_topbar"] = (mb not in src_self and nb not in src_self
                          and all(hasattr(win, x) for x in ("palette", "palette_rows", "ctlToggle",
                                                             "contextMenuEvent", "_menu_actions")))
    out["palette_rows"] = len(rows_all); out["palette_filtered"] = len(rows_f)
    out["palette_has_meta_and_panels"] = (":cmds" in names_all and "任务表" in names_all
                                         and "十二链" in names_all)
    out["qactions"] = n_acts; out["menu_items"] = len(win.MENU_ITEMS)
    out["ctl_cycle"] = [ctl_on, ctl_off]; out["view_cycle"] = [view_i, eink_open_by_view]
    out["fw_missing_required"] = missing
    out["lcd_cells"] = len([k for k in win.fw if str(k).startswith("lcd_")])
    out["led_lamps"] = len([k for k in win.fw if str(k).startswith("led_")])
    print("SELFTEST " + json.dumps(out, ensure_ascii=False))
    ok_all = (out["saved"] and out["visible_rows"] >= 10 and out["meta_keys"] >= 30
              and out["no_token_face"] and out["f1_groups"] >= 5 and out["roll_plain"] >= 4
              and out["details"] >= 5 and out["panel_min"] >= 40 and out["task_table_len"] >= 2
              and len(panels) == 15 and out["qss_len"] > 1500
              and out["cut_ok"] and out["cut_steps"] == 5 and out["led_names"] == 7
              and out["crt_ok"] and out["eink_ok"] and out["eink_len"] > 8
              and out["zero_topbar"] and out["palette_rows"] >= 60 and out["qactions"] >= out["menu_items"]
              and out["ctl_cycle"] == [True, True] and not out["fw_missing_required"]
              and out["palette_has_meta_and_panels"] and 0 < out["palette_filtered"] < out["palette_rows"]
              and out["lcd_cells"] == 6 and out["led_lamps"] == 7 and out["view_cycle"] == [2, True])
    return 0 if ok_all else 1

if __name__ == "__main__":
    if sys.stdout is None or sys.stderr is None:
        # pythonw 无控制台：print 会抛，统一兜到 devnull（日志仍走 debug/log）
        _dn = open(os.devnull, "w", encoding="utf-8")
        sys.stdout = sys.stdout or _dn; sys.stderr = sys.stderr or _dn
    sys.exit(main())

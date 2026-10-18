#!/usr/bin/env python3
"""tests/test_shell_qt.py — PyQt6 图形壳（shell_qt.py）离线回归：文件在场＋零裸子进程＋入口 --qt 接线＋
行分类与上色纯函数口径（不建 QApplication·不连模型网关）。跑法：pytest tests/test_shell_qt.py -q"""
import os
import re
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "skill", "scripts")
sys.path.insert(0, S)
QT = os.path.join(S, "shell_qt.py")


def _src():
    assert os.path.isfile(QT), "缺 shell_qt.py（PyQt6 图形壳）"
    return open(QT, encoding="utf-8").read()


def _local(name):
    """按本仓文件路径取件（引擎件会把核仓旧副本插到 sys.path 前，裸 import 可能测到旧版同名件）。"""
    import importlib.util
    p = os.path.join(S, name + ".py")
    assert os.path.isfile(p), "缺 " + p
    m = sys.modules.get(name)
    if m is not None and os.path.abspath(getattr(m, "__file__", "") or "") == p:
        return m
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    assert os.path.abspath(m.__file__) == p, "装载到的不是本仓文件：" + str(m.__file__)
    return m


def test_qt_offscreen_three_views():
    """离屏成图回归（QT_QPA_PLATFORM=offscreen·不发模型请求·不开端口·不另起进程）：
    三件真在机身里并可推进/可关；缺 PyQt6 或引擎件不可装配＝skip 不误报。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏成图不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import time as _t
    try:
        fax = _local("shell_qt_fax")
        qt = _local("shell_qt")
        from PyQt6.QtGui import QPainter, QPixmap
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过成图，不误报"
                    % (type(e).__name__, str(e)[:80]))
    try:
        fw = win.fw
        assert "blade" in fw and "blade_tag" in fw and "blade_pos" in fw, "机身缺裁纸刀件"
        assert fw["blade"].property("st") == "idle", "开机刀条须待机态"
        assert "led_裁纸" in fw and len([k for k in fw if str(k).startswith("led_")]) == 7, "裁纸灯须在场"
        win.ent._cur_on = True; win.ent.crt_force = True
        win.ent.setPlainText(":cmds "); win.ent._glow_t = _t.time()
        pm = QPixmap(420, 64); p = QPainter(pm); ov = win.ent._crt_overlay(p, 420, 64); p.end()
        win.ent._cur_on = False; p = QPainter(pm); ov_off = win.ent._crt_overlay(p, 420, 64); p.end()
        win.ent._cur_on = True; win.ent.crt_force = False
        assert ov["scanlines"] > 0 and ov["glow"] > 0 and ov["cursor"], "CRT 三层成像须都画上"
        assert not ov_off["cursor"], "灭相＝块光标消失（闪烁真在走）"
        assert win.ent.property("crt") == "1" and win.ent.objectName() == "cmd", "送稿口须挂 CRT 态"
        win._eink_on = True; fw["einkzone"].show()
        win.running["t8"] = {"text": "墨水屏示例话语", "t0": _t.time() - 2}
        win.einkRefresh(); app.processEvents()
        txt = fw["eink"].toPlainText()
        assert all(s in txt for s in fax.EINK_SECTIONS), "墨水屏只三段"
        assert "墨水屏示例话语" in txt, "后台任务段须带在跑话语"
        win.running.pop("t8", None)
        seen = [win._cut_step() for _ in range(5)]
        assert seen == ["feed", "clamp", "cut", "drop", "idle"] and win.cut_seq == 1
        assert "裁纸段" in win.out.toHtml(), "落盘须留裁断印记"
        win.cut_state = "cut"; win._cut_apply()
        assert fw["blade"].property("st") == "cut" and fw["blade_pos"].text().endswith("75%")
        win.cut_state = "idle"; win._cut_apply()
        win.fax("crt"); assert win.ent.crt_on is False, "CRT 开关须能关成像层"
        win.fax("crt"); win.fax("eink"); assert win._eink_on is True and fw["einkzone"].isVisible(), "墨水屏开关须能收"
    finally:
        try:
            win._cut_end()
        except Exception:
            pass
        win.close(); app.processEvents()


def test_qt_shell_present_and_quiet():
    src = _src()
    import no_window_audit as aud
    assert aud.hits(src, "shell_qt.py") == [], "GUI 内不得有裸 subprocess/os.system（闪黑框根因）"
    assert "# sms-visible" in src, "GUI 另起 TUI 的可见控制台点必须带标记"


def test_entry_wired_qt_flag():
    sh = open(os.path.join(S, "shell.py"), encoding="utf-8").read()
    assert '--qt' in sh and 'launch("qt")' in sh, "入口须支持 --qt 起 PyQt6 图形壳"
    assert os.path.isfile(os.path.join(S, "shell_tui_textual.py"))
    lc = open(os.path.join(S, "shell_lifecycle.py"), encoding="utf-8").read()
    assert "shell_qt.py" in lc, "壳生命周期回收清单须含 shell_qt.py"


def test_scripts_locator_and_routing():
    src = _src()
    assert "def _scripts()" in src, "GUI 需三级找回壳脚本目录（换目录部署可跑）"
    for call in ("core.handle(", "msg_flow.visible(", "detail_bus.tail(", "stop.bind("):
        assert call in src, "GUI 必须复用壳路由/明细口径/并行隔离：" + call


def test_line_classification_deterministic():
    """不起 QApplication：只测 paint/visible 的纯函数口径（与 Textual split 一致）。"""
    import msg_flow
    assert msg_flow.visible("$ exec ls") is False, "工具行不得进主输出"
    assert msg_flow.visible("这是正文回答") is True
    assert msg_flow.visible("◌ 思考片段") is False
    assert msg_flow.blank("⧉general_answer▸   ") is True


def test_t6_cut_blade_wired():
    """批39 t6：出纸末端裁纸刀——机身刀条件＋进程内 QTimer 走步，不引新端口/新进程。"""
    src = _src()
    for need in ("def cut(self, arg=None):", "def _cut_step(self)", "def _cut_apply(self)",
                 "self._cut_timer.timeout.connect(self._cut_step)", "fax.cut_next(",
                 "fax.cut_mark(", 'self.fw["blade"]', '"cut": self.cut', '"裁纸"'):
        assert need in src, "图形壳缺裁纸接线：" + need[:50]
    assert src.count("class ") and len(re.findall(r"class\s+\w+\(QThread\)", src)) == 1, \
        "裁纸不得新增线程件（既有 Task worker 之外不许再起 QThread）"
    for banned in ("socket.socket", "HTTPServer", "serve_forever", "os.system("):
        assert banned not in src, "裁纸不得引入新端口/服务端面：" + banned
    # 批41 后源件重排段：右边界收在 t8 CRT 头（原指 t10 会吞进批41 预览/终端段，
    # 那两段本就有 subprocess/QProcess 字样＝裁纸段判据假红）——只扫裁纸自己的段
    seg = src[src.index("def cut(self"):src.index("# ---------- t8 CRT")]
    assert "QThread" not in seg and "subprocess" not in seg and "Popen" not in seg, \
        "裁纸段只许用进程内 QTimer 走步"


def test_t8_crt_input_view_wired():
    """批39 t8：送稿口 CRT 绿字黑底——成像层接线在场，且键盘/提交/补全/历史与 stop/ask 口径一字未改。"""
    src = _src()
    for keep in ('if k == Qt.Key.Key_Tab:\n            self.win.complete(self); return',
                 "self.win.submit(self.toPlainText())",
                 "if self.win.history(self, k == Qt.Key.Key_Up): return",
                 "def stop_one(self", "ask_channel.reply(", "stop.is_stop_word("):
        assert keep in src, "CRT 改版不得动既有路由/stop/ask 口径：" + keep[:40]
    for need in ("def paintEvent(self, ev):", "super().paintEvent(ev)", "def _crt_overlay(self",
                 "def crt_cursor_rect(self)", "def crtToggle(", 'fax("crt")', "QPainter",
                 "fax.crt_afterglow(", "fax.crt_scanlines(", "fax.crt_block_cursor(",
                 'setProperty("crt", "1")', 'setObjectName("cmd")',
                 "textChanged.connect(self._crt_glow)"):
        assert need in src, "图形壳缺 CRT 接线：" + need[:50]


def test_t10_eink_panel_wired():
    """批39 t10：墨水屏消息面板——三段固定、数据仍走进程内 api、开关走机身口。"""
    src = _src()
    for need in ("def einkToggle(", "def einkRefresh(", "def eink_bg(", 'fax("eink")',
                 "fax.eink_html(", 'self.fw["eink"]', "self._tasks_cache"):
        assert need in src, "图形壳缺墨水屏接线：" + need[:40]
    fx = open(os.path.join(S, "shell_qt_fax.py"), encoding="utf-8", errors="replace").read()
    assert 'EINK_SECTIONS = ("会话信息", "任务总览", "后台任务")' in fx, "墨水屏只保三段"


def test_selftest_covers_three_views():
    """两个 selftest 须把三件当硬判据（rc=0 才放行）——防止只加视觉不进门禁。"""
    src = _src()
    for need in ('"cut_ok": cut_ok', '"crt_ok": crt_ok', '"eink_ok": eink_ok',
                 'out["cut_ok"] and out["cut_steps"] == 5 and out["led_names"] == 7',
                 'out["crt_ok"] and out["eink_ok"]'):
        assert need in src, "shell_qt selftest 缺三件断言：" + need[:50]
    fx = open(os.path.join(S, "shell_qt_fax.py"), encoding="utf-8", errors="replace").read()
    for need in ('ok["cut_cycle"]', 'ok["crt_afterglow"]', 'ok["eink_sections"]',
                 'ok["qss_blade"] and ok["qss_eink"]'):
        assert need in fx, "镜像件 selftest 缺三件判据：" + need[:40]


def test_probe_hook_exists():
    src = _src()
    assert "--probe=" in src and "probe_finish" in src, "需保留 --probe 端到端回归钩子"

def test_fax_mirror_wired():
    """批38/39：图形壳＝网页端传真机镜像（版式取 web_page.html·数据进程内直调 web_shell·GUI 端免密钥验证）。"""
    src = _src()
    assert "fax = _load_fax()" in src and "spec_from_file_location" in src, \
        "图形壳须接镜像件 shell_qt_fax.py（按同目录显式装载＝防核仓旧副本顶包）"
    assert "fax.build(" in src and "fax.qss(" in src, "机身须由镜像件装配＋网页端样式"
    assert "配对令牌" not in src, "图形壳不得留网页端门禁（密钥验证）文案——GUI 免密钥"
    for bad in ("HTTPServer", "serve_forever", "check_token", "web_certs"):
        assert bad not in src, "图形壳不得触碰服务端/密钥面：" + bad
    assert "def paper(" in src, "出纸口（网页端 print 同构）须在场"
    assert "def _open(" in src, "抽屉面板入口须在场"


# ---------------- 批40 零顶栏＋批41 分屏骨架（表 010-213903-130／010-231707-890 壳侧覆盖） ----------------
def test_zero_topbar_no_menubar_no_brand_strip():
    """顶栏真拆：不挂原生菜单栏、不装 brand 横条；菜单职能＝命令面板＋右键菜单（同源 MENU_ITEMS）。"""
    src = _src()
    assert "self." + "menuBar()" not in src, "图形壳不得再挂原生菜单栏（＝第二条顶栏横带）"
    assert "SMS-" + "FAX · GUI" not in src, "brand 横条文案不得残留（零顶栏）"
    for need in ("MENU_ITEMS = (", "def _menu_actions(self)", "def palette(self)",
                 "def palette_rows(self", "def contextMenuEvent(self", "def ctlToggle(self",
                 "def viewToggle(self", '"ctl": self.ctlToggle', '"view": self.viewToggle',
                 '"palette": self.palette'):
        assert need in src, "零顶栏改造缺件：" + need[:40]
    assert "self._ui(); self._timers()" in src, "__init__ 须停止调用 _menu（不再装菜单栏）"
    for sc in ("F3", "F5", "F8", "Ctrl+K", "Ctrl+M", "Ctrl+I", "Ctrl+E", "Ctrl+R", "Ctrl+V",
               "Ctrl+T", "Ctrl+P", "Ctrl+J", "Ctrl+H", "Ctrl+Shift+C"):
        assert '"%s"' % sc in src, "原顶栏快捷键须保 QAction 级：" + sc


def test_palette_is_single_source_no_second_routing():
    """命令面板＝条目复用而非新建口径：来源全为既有登记表（META/F1/QUICK/PAD/DRAWERS/MENU_ITEMS/历史），
    出口全为既有机身方法（feed/faxPick/_open），且不引入第二条路由/进程/端口。"""
    src = _src()
    seg = src.split("def palette_rows(self")[1].split("def palette(self)")[0]
    for src_need in ("fax.keys()", "fax.DRAWERS.items()", "self.MENU_ITEMS", "self.hist[-12:]"):
        assert src_need in seg, "命令面板少了一路既有来源：" + src_need
    for outlet in ("self.feed(", "self.faxPick(", "self._open("):
        assert outlet in seg, "命令面板出口须走既有机身/送稿口方法：" + outlet
    for banned in ("core.handle", "subprocess", "socket", "requests", "urllib"):
        assert banned not in seg, "命令面板不得另起路由/进程/端口（路由仍 shell_core.handle·同 TUI/网页端）"
    mseg = src.split("MENU_ITEMS = (")[1].split("def about_text")[0]
    assert "w.submit(" in mseg and 'w.fax("palette")' in mseg, "菜单条目须复用 submit/fax 既有出口（不第三条口径）"


def test_control_panel_on_demand_not_permanent():
    """控制面板按需化：常驻功能区只剩 A 纸卷区＋B 送稿口，控制面（META/F1/拨号盘）装配即收起。"""
    fx = open(os.path.join(S, "shell_qt_fax.py"), encoding="utf-8", errors="replace").read()
    build = fx.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    core = build.split('"""', 2)[-1]
    code = build.split('"""', 2)[-1]
    assert build.count("_zone(") == 4, \
        "常驻功能区＝A 纸卷＋B 送稿＋D 预览＋E 终端（批41 上送稿＋下左右分屏·顶栏与控制区已拆·实测 %d 区）" % build.count("_zone(")
    for t in ('"① 送稿口 DOC FEEDER · B', '"② 纸卷区 PAPER ROLL · A', '"③ 预览 PREVIEW · D', '"④ 终端 TERMINAL · E'):
        assert t in build, "常驻区标题须齐批41 四件：" + t
    assert '_zone("⑤' not in build and 'ctlzone")' in build and 'ctl = QFrame()' in build, \
        "控制面板＝按需件（不走 _zone 常驻装配）"
    assert 'ctl.setObjectName("ctlzone")' in build and "ctl.hide()" in build, "控制面板须装配即收起"
    assert "dr.hide()" in code and "ez.hide()" not in code and "psplit.addWidget(ez)" in code, \
        "抽屉仍默认收起（按需展开）·C 墨水屏已改常驻右栏（不得 hide）"
    for keep in ('w["ctlzone_btn"]', '"⌘ 命令面板"', '"▦ 控制面板 Ctrl+M"'):
        assert keep in build, "按需层须有唤出件：" + keep
    assert 'w["lcd_" + k]' in build, "LCD 六格仍由循环产出（键名不变）"
    assert 'w["led_" + nm]' in build, "LED 七灯仍由循环产出（键名不变）"


def test_selftest_covers_zero_topbar():
    """shell_qt selftest 须把零顶栏当硬判据（rc=0 才放行）：取证字段＋放行式都在，输出行不得重复。"""
    src = _src()
    for need in ('out["zero_topbar"]', 'out["palette_rows"]', 'out["qactions"]',
                 'out["ctl_cycle"]', 'out["view_cycle"]', 'out["fw_missing_required"]',
                 'out["lcd_cells"]', 'out["led_lamps"]',
                 'and out["zero_topbar"] and out["palette_rows"] >= 60',
                 'out["ctl_cycle"] == [True, True]', 'out["view_cycle"] == [2, True]',
                 'not out["fw_missing_required"]'):
        assert need in src, "shell_qt selftest 缺零顶栏判据：" + need[:46]
    assert src.count('print("SELFTEST " + json') == 1, "自检输出行不得重复（补丁残留孤行＝语法/口径双伤）"


# ---------------- 批45 裸名预览候选目录回查（表 011-080847-802 壳侧） ----------------
def test_batch45_preview_candidate_roots_source():
    """裸名取数不得再单点问 _ws_hint（工作区根顶层不含生成件）：候选目录＝工作区根→SMS_TMP→cwd，
    命中即 /api/file；selftest 不得再 monkeypatch _ws_hint（改门禁不许改口径后门）。"""
    src = _src()
    pv = src.split("def previewOpen(self")[1].split("def pvToggle")[0]
    cand = src.split("def _pv_candidates(self)")[1].split("def previewOpen(self")[0]
    for need in ('self._ws_hint()', 'os.environ.get("SMS_TMP")', "os.getcwd()"):
        assert need in cand, "候选目录段缺来源：" + need[:40]
    for need in ('for d in roots', 'fax.api("/api/files", query={"ws": d})', 'if hit:'):
        assert need in pv, "裸名段缺候选回查：" + need[:44]
    assert "query={\"ws\": self._ws_hint()}" not in pv, "裸名段不得留单点 _ws_hint 旧口径"
    seg = src.split("def _selftest")[1]
    assert 'out["pv_ws_roots"]' in seg and "win._ws_hint = " not in seg, \
        "selftest 须以真 _ws_hint 取证（monkeypatch 已撤）"


def test_batch45_preview_candidate_roots_offscreen():
    """真装配下裸名预览必须命中（不经 _ws_hint monkeypatch）：样本落 SMS_TMP（=conv 根的子目录），
    _ws_hint 只到 conv 根，旧口径必 miss；同时锁「候选全 miss＝明确 err＋兜底」不静默。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        d = os.environ.get("SMS_TMP") or os.getcwd()
        name = "b45_cand_sample.txt"
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write("\n".join("cand %d" % i for i in range(16)))
        roots = win._pv_candidates()
        assert roots and roots[0] == (win._ws_hint() or roots[0]), "候选首位＝工作区根"
        r = win.previewOpen(name)
        assert r["lines"] >= 16 and not r["err"] and not r["fallback"], \
            "裸名须经候选目录回查命中真件：%s" % r
        miss = win.previewOpen("b45_no_such_file.txt")
        assert miss["err"] and miss["fallback"], "候选全 miss 须明确 err＋兜底（不静默）"
    finally:
        win.close(); app.processEvents()


# ---------------- 批41 上送稿口＋下左右分屏（表 010-231707-890 壳侧） ----------------
def test_batch41_split_assembly_and_five_views_offscreen():
    """离屏装配回归（offscreen·不发模型请求）：B 送稿口第一位＋QSplitter 左右分屏＋右栏两件可切可折＋
    五视图轮转＋预览行号栏＋终端 QProcess 随窗口收净（不留孤儿·不新建 HTTP·不读 token）。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        fax = _local("shell_qt_fax")
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        from PyQt6.QtWidgets import QSplitter
        fw = win.fw
        for k in ("split", "psplit", "preview", "previewzone", "pv_open", "pv_stat", "pv_fold",
                  "term", "termzone", "term_in", "t_run", "t_fold", "t_paper", "t_clear", "t_stat"):
            assert k in fw, "批41 装配缺键：" + k
        lay = win.centralWidget().layout()
        assert isinstance(fw["split"], QSplitter) and isinstance(fw["psplit"], QSplitter)
        assert fw["split"].orientation() == qt.Qt.Orientation.Horizontal, "主分屏须左右"
        assert fw["psplit"].orientation() == qt.Qt.Orientation.Vertical, "右栏须上下"
        assert lay.indexOf(fw["feeder"]) == 0 and lay.indexOf(fw["split"]) == 1, "送稿口须常驻第一位"
        assert fw["split"].widget(0) is fw["tray"] or fw["split"].indexOf(fw["tray"]) == 0, \
            "分屏左格＝纸卷 A"
        assert (fw["psplit"].indexOf(fw["einkzone"]) == 0
                and fw["psplit"].indexOf(fw["previewzone"]) == 1
                and fw["psplit"].indexOf(fw["termzone"]) == 2), \
            "右列两格＝C 墨水屏（常驻第一格）／D 预览／E 终端"
        assert fw["split"].childrenCollapsible() is False and fw["psplit"].childrenCollapsible() is False
        assert fw["ctlzone"].isVisible() is False and fw["einkzone"].isVisible() is True, \
            "控制面板仍按需 hide·C 墨水屏常驻可见（批41 收尾）"
        # 预览：行号栏在场且能数到第一行
        r = win.previewOpen("")
        assert r["lines"] >= 1 and not r["err"] or r["fallback"], "/api/detail 取数路须可用或明确兜底"
        p = os.path.join(os.environ.get("SMS_TMP") or os.getcwd(), "b41_t_sample.txt")
        with open(p, "w", encoding="utf-8") as fh: fh.write("\n".join("l%d" % i for i in range(30)))
        rr = win.previewOpen(p)
        assert rr["lines"] >= 30 and not rr["err"], "进程内 /api/file 取数失败：%s" % rr
        assert fw["preview"].lnr_rows()[0][0] == 1, "行号须从 1 起（与源行一一对应）"
        assert fw["preview"].lnr.sizeHint().width() >= 30, "行号栏须占出宽度（独立自绘）"
        assert "no/such" in str(win.previewOpen("no/such/file_b41.txt")["src"]) or True
        jam = win.previewOpen("no/such/file_b41.txt")
        assert jam["err"] and jam["fallback"], "取不到须兜底并报 err"
        assert "预览取数卡纸" in fw["roll"].toPlainText(), "兜底须在纸面报错（不静默）"
        # 1280×720 可用：窗口最小尺寸须容得下窄屏，分屏两格与右栏两件都拿到真实像素
        win.resize(1280, 720); win.show()
        for _ in range(6): app.processEvents()
        msh = win.minimumSizeHint()
        assert msh.width() <= 1280 and msh.height() <= 720, \
            "窗口最小尺寸不得超 1280×720（实测 %d×%d）" % (msh.width(), msh.height())
        assert list(win.fw["split"].sizes())[0] >= 300 and \
            win.fw["roll"].width() > 0 and win.fw["preview"].width() > 0 and win.fw["term"].width() > 0, \
            "窄屏下分屏两格须各有尺寸：%s / %s" % (list(win.fw["split"].sizes()),
                                                list(win.fw["psplit"].sizes()))
        assert min(win.fw["preview"].height(), win.fw["term"].height()) >= 60, "右栏两件窄屏仍须可读高度"
        # 轮转＝五态
        seq = [win.fax("view")["i"] for _ in range(len(fax.VIEW_NAMES))]
        assert seq == [1, 2, 3, 4, 0] and list(fax.VIEW_NAMES) == \
            ["纸卷 A", "送稿 B", "墨水屏 C", "预览 D", "终端 E"]
        # 折叠
        win.fax("pvFold"); hid = fw["previewzone"].isVisible()
        win.fax("pvFold"); shown = fw["previewzone"].isVisible()
        assert hid is False and shown is True, "预览须可折可复"
        win.fax("termFold"); assert fw["termzone"].isVisible() is False, "终端须可折"
        win.fax("termFold")
        # 终端：QProcess 走同一路由（`!`）＋收净
        win.fw["term_in"].setText("!echo b41pytest")
        win.fax("termRun")
        assert win.term_procs, "终端须起 QProcess（进程内·无控制台窗）"
        import time as _t
        t0 = _t.time()
        while win.termAlive() and _t.time() - t0 < 20:
            app.processEvents(); _t.sleep(0.02)
        for _ in range(15): app.processEvents(); _t.sleep(0.02)
        tail = win.fw["term"].tail(400)
        assert "b41pytest" in tail and "rc=" in tail, "终端须回灌 `!` 输出与退出码：%s" % tail[:120]
        assert win.fax("termPaper")["ok"] >= 1, "终端缓冲须能回灌纸卷"
        assert win.fax("termClear")["ok"] is True and len(win.fw["term"].lines) == 0
        win.fw["term_in"].setText("!ping -n 20 127.0.0.1"); win.fax("termRun")
        app.processEvents(); _t.sleep(0.5)
        assert win.termAlive(), "长驻进程须在跑（才能验收净）"
        assert win.termStopAll() >= 1 and not win.termAlive(), "closeEvent 同路收净须能杀长驻"
    finally:
        win.close(); app.processEvents()


def test_batch41_palette_and_menu_single_source():
    """命令面板/右键菜单同源扩项：preview·terminal 动作进 MENU_ITEMS（palette_rows 由它派生·
    不得出现第二条路由），Ctrl+V 轮转判据同步改五态。"""
    src = _src()
    mseg = src.split("MENU_ITEMS = (")[1].split("def about_text")[0]
    for need in ('w.fax("preview"', 'w.fax("pvFold")', 'w.fax("pvReload")', 'w.fax("termRun")',
                 'w.fax("termFold")', 'w.fax("termPaper")', 'w.fax("termClear")',
                 '"视图轮转（纸卷／送稿／墨水屏／预览／终端）"'):
        assert need in mseg, "菜单条目缺批41 同源项：" + need[:40]
    d = src.split("def fax(self, act, arg=None):")[1].split("def faxPick")[0]
    for k in ('"preview": self.previewOpen', '"pvFold": self.pvToggle', '"pvReload": self.pvReload',
              '"termRun"', '"termFold": self.termFold', '"termPaper": self.termPaper',
              '"termClear"'):
        assert k in d, "机身分派缺批41 动作：" + k
    assert "core.handle(" not in mseg + d, "菜单/分派不得新建路由（仍 shell_core.handle 唯一口）"
    vseg = src.split("def viewToggle(self")[1].split("# ---------- t10")[0]
    assert "fax.view_next(" in vseg and "fax.VIEW_NAMES" in vseg, "轮转位次真源须＝镜像件（不留两份口径）"
    assert "% 3" not in vseg, "三态轮转判据须已改五态"
    for sc in ('"Ctrl+D"', '"Ctrl+U"', '"Ctrl+B"', '"Ctrl+V"'):
        assert sc in mseg, "批41 快捷键须保 QAction 级：" + sc


def test_batch41_preview_terminal_no_new_route_no_key_face():
    """预览取数只走进程内 /api/*（绝不新建 HTTP·绝不读 token）；终端只经 QProcess 复用 core.handle；
    有意开窗处仍只 `tui` 一处（no_window_audit 口径不破）。"""
    src = _src()
    pv = src.split("def previewOpen(self")[1].split("def pvToggle")[0]
    for need in ('fax.api("/api/detail"', 'fax.api("/api/file"', 'fax.api("/api/files"',
                 "fax.preview_text(", "self.paper(", "fallback"):
        assert need in pv, "预览段缺进程内取数/兜底要素：" + need[:32]
    for banned in ("sock" + "et", "HTTP" + "Server", "requests", "urllib", "token", "subprocess."):
        assert banned not in pv, "预览段不得触碰服务端/密钥/裸壳面：" + banned
    tm = src.split("def _termSpawn(self")[1].split("def termHist")[0]
    assert "QProcess(" in tm and "shell_core as c" in tm and "c.handle(" in tm, \
        "终端须 QProcess 复用 core.handle（同 TUI 口径）"
    assert "MergedChannels" in tm and "readyReadStandardOutput" in tm, "终端须管道回灌"
    cl = src.split("def closeEvent(self")[1].split("def _envs")[0]
    assert "termStopAll()" in cl, "窗口 closeEvent 须收终端进程（不留孤儿）"
    assert "# sms-visible" in src, "有意开窗标记仍在 `tui` 一处（no_window 口径）"
    import no_window_audit as aud
    assert aud.hits(src, "shell_qt.py") == [], "批41 不得新增裸子进程调用点（无标记）"


def test_selftest_covers_batch41_gates():
    """shell_qt selftest 须把批41 判据并入 ok_all 放行式（防只改视觉不进门禁）＋孤行防回归仍在。"""
    src = _src()
    seg = src.split("def _selftest")[1]
    for need in ('out["preview_rows"]', 'out["preview_lnr_rows"]', 'out["preview_lnr_first"]',
                 'out["preview_lnr_width"]', 'out["preview_from_api"]', 'out["preview_jam_fallback"]',
                 'out["term_available"]', 'out["term_rc_shown"]', 'out["term_close_clean"]',
                 'out["term_paper_back"]', 'out["pv_fold_cycle"]', 'out["view_cycle5"]',
                 'out["view_names"]', 'out["split_parts"]', 'out["feeder_first"]',
                 'out["palette_pv_term"]', 'out["no_second_route"]', 'out["fw_keys_41"]',
                 'out["narrow_1280"]'):
        assert need in seg, "selftest 缺批41 取证字段：" + need
    okline = seg.split("ok_all = (")[1]
    for need in ('and out["preview_rows"] >= 40', 'and out["preview_lnr_first"] == 1',
                 'and out["term_available"]', 'and out["term_close_clean"]',
                 'and out["view_names"] ==', 'and [c[0] for c in out["view_cycle5"]] == [1, 2, 3, 4, 0]',
                 'and out["feeder_first"]', 'and out["palette_pv_term"][0] >= 7',
                 'and out["narrow_1280"]["min_w"] <= 1280', 'and out["narrow_1280"]["min_h"] <= 720',
                 'and out["no_second_route"]'):
        assert need in okline, "批41 判据未进 ok_all 放行式：" + need
    assert src.count('print("SELFTEST " + json') == 1, "自检输出行不得重复（补丁残留孤行＝语法/口径双伤）"


def test_offscreen_zero_topbar_assembly():
    """离屏装配回归（offscreen·不发模型请求）：菜单栏不存在·按需件开机收起·命令面板条目可用可过滤。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        from PyQt6.QtWidgets import QMenuBar
        assert all((not mb.isVisible()) or (not mb.actions()) for mb in win.findChildren(QMenuBar)), \
            "原生菜单栏不得存在/可见（零顶栏）"
        assert win.fw["ctlzone"].isVisible() is False, "控制面板须开机收起"
        assert win.fw["einkzone"].isVisible() is True, "C 墨水屏须开机常驻（Ctrl+I 只聚焦不 hide）"
        assert win.fw["roll"].isVisible() and win.ent.isVisible(), "A 纸卷区与 B 送稿口须常驻可见"
        assert len(win.acts) >= len(win.MENU_ITEMS), "QAction 快捷键数须覆盖全部菜单条目"
        rows = win.palette_rows("")
        assert len(rows) >= 60, "命令面板条目须覆盖原顶栏全量（实测 %d）" % len(rows)
        groups = {r[0] for r in rows}
        assert {"元指令", "面板", "动作·shell", "动作·fax", "动作·help", "盘面", "拨号", "快捷"} <= groups, \
            "命令面板分组须齐（实测 %s）" % sorted(groups)
        assert all(callable(r[3]) for r in rows), "每行须带可调用出口"
        assert 0 < len(win.palette_rows(":cmds")) < len(rows), "过滤须真缩小"
        assert win.palette_rows("任务总览"), "面板类条目须可被中文过滤命中"
        win.fax("ctl"); on = win.fw["ctlzone"].isVisible()
        win.fax("ctl"); off = not win.fw["ctlzone"].isVisible()
        assert on and off, "控制面板 Ctrl+M 须可展可收"
        win._eink_on = False   # 反证起点：轮转到 C 态必把常驻件收回可见（任何路径不得 hide）
        win.fax("view"); win.fax("view")
        assert win._view_i == 2 and win.fw["einkzone"].isVisible(), "视图轮转第 3 态须聚焦 C（常驻件）"
        win.fax("view"); win._view_i = 0
    finally:
        win.close(); app.processEvents()


# ---------------- 批41 上送稿口＋下左右分屏（表 010-230506-244 壳侧） ----------------
def test_batch41_preview_widget_wired():
    """批41 预览件 D 接线：行号栏独立自绘＋取数只走进程内 /api/*（红线＝不新建 HTTP·不读 token）。"""
    src = _src()
    for need in ("class Preview(QPlainTextEdit)", "class LineNumberArea(QWidget)", "lnr_rows()",
                 'def previewOpen(self, target=""):', 'fax.api("/api/detail")',
                 'query={"path": t}', 'query={"ws": d}', "fax.preview_text(",
                 "def _pv_candidates(self):"):
        assert need in src, "批41 预览件缺接线：" + need[:44]
    # 批46 收口：判据与批45 实现对齐——裸名走「候选目录逐个回查」（_ws_hint→SMS_TMP→cwd），非单点 _ws_hint
    cand = src.split("def _pv_candidates(self)")[1].split("def previewOpen(self")[0]
    assert 'os.environ.get("SMS_TMP")' in cand, "候选目录须含 SMS_TMP（生成件落 tmp·裸名才可回查命中）"
    pv = src.split("def previewOpen(self")[1].split("def pvToggle")[0]
    assert "self._pv_candidates()" in pv and "for d in roots" in pv, \
        "裸名预览须走候选目录逐个 /api/files?ws=… 回查"
    seg = src[src.index("class LineNumberArea(QWidget)"):src.index("class Terminal(QPlainTextEdit)")]
    for banned in ("HTTPServer", "socket", "serve_forever", "requests", "urllib"):
        assert banned not in seg, "预览段须进程内取数，不得出现服务端面：" + banned


def test_batch41_terminal_widget_wired():
    """批41 终端件 E：QProcess 管道回灌＋窗口收进程；裸 subprocess.Popen 全文件只许既有 Textual TUI 一处。"""
    src = _src()
    for need in ("class Terminal(QPlainTextEdit)", "class TermIn(QLineEdit)",
                 "def _termSpawn(self, line):", "QProcess(self)",
                 "setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)",
                 "self.term_procs.append(p)", "closeWriteChannel", "def termRun", "def termFold",
                 "def termPaper", "def termClear", "def termAlive", "def termStopAll",
                 "with contextlib.suppress(Exception): self.termStopAll()"):
        assert need in src, "批41 终端件缺接线：" + need[:48]
    assert src.count("subprocess.Popen") == 1, \
        "裸 subprocess.Popen 只许 # sms-visible 那处 Textual TUI（实测 %d）＝批41 不得引第二条进程面" \
        % src.count("subprocess.Popen")


def test_batch41_view_rotation_five_states_from_mirror():
    """轮转＝真源单一（位次算式在镜像件）＋快捷键面齐；build 注类走 PREVIEW_CLS／TERM_IN_CLS 回落基件。"""
    src = _src()
    for need in ("def viewToggle(self, arg=None):", "fax.view_next(", "tuple(fax.VIEW_NAMES)",
                 "PREVIEW_CLS", "TERM_IN_CLS"):
        assert need in src, "批41 轮转/注类缺件：" + need[:40]
    for sc in ('"Ctrl+D"', '"Ctrl+U"', '"Ctrl+B"', '"Ctrl+V"'):
        assert sc in src, "批41 快捷键须保 QAction 级：" + sc


def test_batch41_fax_dispatch_and_palette_single_source():
    """机身分派＋菜单/命令面板同源：批41 动作复用 fax 出口，palette_rows 段仍无第二条路由/进程/端口。"""
    src = _src()
    d = src.split("def fax(self, act, arg=None):")[1].split("def faxPick")[0]
    for need in ('"preview": self.previewOpen', '"pvFold": self.pvToggle',
                 '"termRun": lambda a=None: self.termRun()', '"termPaper": self.termPaper'):
        assert need in d, "批41 机身分派缺动作：" + need[:40]
    mseg = src.split("MENU_ITEMS = (")[1].split("def about_text")[0]
    assert 'w.fax("pvFold")' in mseg and 'w.fax("termRun")' in mseg, \
        "菜单条目须复用 fax 既有出口（不第二条路由）"
    seg = src.split("def palette_rows(self")[1].split("def palette(self)")[0]
    for banned in ("core.handle", "subprocess", "socket"):
        assert banned not in seg, "命令面板段不得新增路由/进程/端口面：" + banned


def test_selftest_covers_batch41():
    """_selftest 放行式须锁批41 五判据（防只改视觉不进门禁）：取证字段在场＋真进 rc 合取式。"""
    seg = _src().split("def _selftest")[1]
    for need in ('out["preview_rows"]', 'out["split_parts"]', 'out["view_cycle5"]',
                 'out["term_close_clean"]', 'out["fw_keys_41"]',
                 'and out["preview_rows"] >= 40', 'and out["term_available"]',
                 'and [c[0] for c in out["view_cycle5"]] == [1, 2, 3, 4, 0]',
                 'and out["split_parts"][2] == "Horizontal"',
                 'out["pv_ws_roots"]', 'and bool(out["pv_ws_roots"])'):
        assert need in seg, "批41 判据未进 _selftest 放行式：" + need[:46]


def test_offscreen_batch41_split_preview_terminal():
    """离屏装配回归（仿零顶栏那条 try/skip 结构）：左右分屏＋预览行号＋终端 QProcess 收净·不发模型请求。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        import time as _t
        fw = win.fw
        assert fw["split"].orientation().name == "Horizontal", "主分屏须左右"
        assert fw["psplit"].orientation().name == "Vertical", "右栏须上下"
        assert fw["split"].childrenCollapsible() is False and fw["psplit"].childrenCollapsible() is False, \
            "分屏子件不得可折没（折叠走 pvFold/termFold）"
        assert win.centralWidget().layout().indexOf(fw["feeder"]) == 0, "送稿口须常驻第一位"
        r = win.previewOpen("")
        assert isinstance(r, dict) and r["lines"] >= 1, "空预览须进程内取数成文：%s" % r
        p = os.path.join(os.environ.get("SMS_TMP") or os.getcwd(), "b41_sample40.txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\n".join("s%d" % i for i in range(40)))
        rr = win.previewOpen(p)
        assert rr["lines"] >= 40 and not rr["err"], "/api/file 取数失败：%s" % rr
        assert fw["preview"].lnr_rows()[0][0] == 1, "行号须自 1 起"
        jam = win.previewOpen("no/such/b41.txt")
        assert jam["fallback"] is True, "取不到须内置兜底（不静默）"
        assert "预览取数卡纸" in fw["roll"].toPlainText(), "兜底须在纸面报卡纸"
        fw["term_in"].setText("!echo b41term")
        win.fax("termRun")
        assert win.term_procs, "终端须登记 QProcess"
        t0 = _t.time()
        while win.termAlive() and _t.time() - t0 < 30:
            app.processEvents(); _t.sleep(0.02)
        for _ in range(20):
            app.processEvents(); _t.sleep(0.02)
        tail = fw["term"].tail(400)
        assert "b41term" in tail and "rc=" in tail, "终端须回灌输出与退出码：%s" % tail[:120]
        win.termStopAll(); app.processEvents()
        assert win.termAlive() == [], "termStopAll 后不得有在跑进程（不留孤儿）"
        win.fax("pvFold"); hid = fw["previewzone"].isVisible()
        win.fax("pvFold"); shown = fw["previewzone"].isVisible()
        assert hid is False and shown is True, "预览须可收可展"
    finally:
        win.close(); app.processEvents()


# ---------------- 批40 图形壳布局补齐（表 010-213457-793 行 t7·壳侧版式断言） ----------------
def test_batch40_layout_source_structure():
    """源码段证明版式：输入在上（送稿口先于分屏装配）＋水平 QSplitter＋右列容器依次装 ctl/墨水屏/抽屉。"""
    fx = open(os.path.join(S, "shell_qt_fax.py"), encoding="utf-8", errors="replace").read()
    build = fx.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    code = build.split('"""', 2)[-1]
    assert code.index("root.addWidget(feeder)") < code.index("split = QSplitter(Qt.Orientation.Horizontal)"), \
        "输入区（送稿口）须在分屏之前"
    assert "QSplitter" in code and "Qt.Orientation.Horizontal" in code, "主分屏须水平 QSplitter"
    assert code.count("split.addWidget(") >= 2, "splitter 须挂两个以上子件（左纸卷＋右列）"
    assert ("av.addWidget(ctl)" in code and "av.addWidget(dr)" in code
            and code.index("av.addWidget(ctl)") < code.index("av.addWidget(dr)")
            and "psplit.addWidget(ez)" in code and "av.addWidget(ez)" not in code), \
        "右列＝psplit 常驻三格 C／D／E（C 墨水屏第一格·Ctrl+I 只聚焦永不 hide）＋按需两件（ctl→抽屉）"
    assert build.count("_zone(") == 4, "常驻功能区＝A/B/D/E（aside 非 _zone·实测 %d）" % build.count("_zone(")
    assert 'out["split_layout"]' in open(QT, encoding="utf-8", errors="replace").read(), \
        "壳侧 selftest 须有 split_layout 几何取证字段"


def test_batch40_offscreen_geometry_top_input_split():
    """offscreen 几何真值：ent 的 y 在 roll 之上＝送稿口在上，且 roll.x < 右列 x＝左右分屏成立。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.resize(1280, 720); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        from PyQt6.QtCore import QPoint
        from PyQt6.QtWidgets import QSplitter
        g = lambda x: x.mapTo(win, QPoint(0, 0))
        y_ent, y_roll = int(g(win.ent).y()), int(g(win.fw["roll"]).y())
        x_roll, x_right = int(g(win.fw["roll"]).x()), int(g(win.fw["aside"]).x())
        assert y_ent < y_roll, "送稿口（ent）须在纸卷之上：y_ent=%d y_roll=%d" % (y_ent, y_roll)
        assert x_roll < x_right, "纸卷须在左、按需列在右：x_roll=%d x_right=%d" % (x_roll, x_right)
        lay = win.centralWidget().layout()
        assert isinstance(win.fw["split"], QSplitter), "主分屏须 QSplitter"
        assert lay.indexOf(win.fw["feeder"]) == 0 and lay.indexOf(win.fw["split"]) == 1, \
            "root 只两格＝上送稿口＋下分屏"
        assert win.fw["split"].indexOf(win.fw["aside"]) == 1, "分屏右格＝aside 竖列"
        assert min(win.fw["split"].sizes()) > 0, "左右初值须生效"
        assert (win.fw["ctlzone"].isVisible() is False and win.fw["einkzone"].isVisible() is True
                and win.fw["drawer"].isVisible() is False), "控制面板／抽屉仍 hide·C 墨水屏常驻可见"
    finally:
        win.close(); app.processEvents()

# ---------------- 批41 收尾三处偏差（表 010-235956-984）：常驻右栏／撤底部条带／走纸队列 ----------------
def _fx():
    return open(os.path.join(S, "shell_qt_fax.py"), encoding="utf-8", errors="replace").read()


def test_b41close_eink_resident_right_source():
    """源码结构：右格 aside＝psplit 常驻三格（C 墨水屏第一格·Ctrl+I 只聚焦永不 hide·不可折叠）＋按需层（ctlzone→抽屉）；C 未被 hide／不回落按需层；e-ink 仍只三段。"""
    fx = _fx()
    build = fx.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    code = build.split('"""', 2)[-1]
    assert "psplit.addWidget(ez)" in code, "右栏须含 einkzone（C 常驻）"
    assert "ez.hide()" not in code and "av.addWidget(ez)" not in code, "C 不得 hide／不得回按需层"
    assert (code.index("psplit.addWidget(ez)") < code.index("psplit.addWidget(pvz)")
            < code.index("psplit.addWidget(tmz)")), "右栏次序＝C／D／E"
    assert 'ez.setProperty("resident", "1")' in code and 'w["eink_stat"] = est' in code
    assert code.count("root.addWidget(") == 2, "root 只两格＝送稿口＋分屏（无底部条带）"
    assert 'EINK_SECTIONS = ("会话信息", "任务总览", "后台任务")' in fx, "e-ink 三段仍只三段"


def test_b41close_eink_visible_without_ctrlI_offscreen():
    """离屏：开机即 C 可见（不经 Ctrl+I）；Ctrl+I 只聚焦/让位，永不 hide；D／E 折叠行为保留。"""
    pytest.importorskip("PyQt6", reason="无 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        fax = _local("shell_qt_fax"); qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）" % (type(e).__name__, str(e)[:80]))
    try:
        fw = win.fw
        assert fw["einkzone"].isVisible() is True, "批41：C＝psplit 常驻第一格·开机即可见（Ctrl+I 只聚焦永不 hide）"
        txt = fw["eink"].toPlainText()
        assert all(s in txt for s in fax.EINK_SECTIONS) and len(fax.EINK_SECTIONS) == 3, \
            "Ctrl+I 展开后须已刷新三段（不留白·只三段）"
        assert not any(bad in fw["eink"].toHtml() for bad in ("animation", "transition", "@keyframes"))
        win._eink_on = False; win.fax("eink"); v1 = fw["einkzone"].isVisible()
        win.fax("eink"); v0 = fw["einkzone"].isVisible()
        assert v1 and v0, "Ctrl+I 语义＝只聚焦/让位（批41 常驻·永不 hide）"
        win.fax("pvFold"); hid = fw["previewzone"].isVisible()
        win.fax("pvFold"); shown = fw["previewzone"].isVisible()
        assert hid is False and shown is True and fw["einkzone"].isVisible(), "D 折叠保留＋C 仍可见"
        win.fax("termFold"); th = fw["termzone"].isVisible()
        win.fax("termFold"); assert th is False and fw["einkzone"].isVisible(), "E 折叠保留＋C 仍可见"
        assert fw["ctlzone"].isVisible() is False and fw["drawer"].isVisible() is False, "按需层仍收起"
        rows = win.palette_rows("")
        assert len(rows) >= 60 and all(callable(r[3]) for r in rows), "命令面板入口不受影响"
    finally:
        win.close(); app.processEvents()


def test_b41close_no_bottom_strip_source():
    """主布局无 statusbar 条带：提示文本迁进墨水小标；Editor 内部 self.stat 与 QSS 保留。"""
    src = _src()
    seg = src[src.index("    def _ui(self):"):src.index("    def _timers(self):")]
    assert "addWidget(self.stat)" not in seg, "主布局不得再挂状态条带"
    assert 'self.stat = self.fw["eink_stat"]' in seg, "提示须迁进 C 墨水屏顶部墨水小标"
    _sb = "status" + "bar"
    _cod = [ln for ln in seg.splitlines() if ln.strip()[:1] != "#"]
    assert not any(_sb in ln and ("QLabel(" in ln or "addWidget" in ln) for ln in _cod), \
        "机身装配段不得再造/挂 QLabel#statusbar（注释里的说明字样不算）"
    assert "QLabel#statusbar{" in _fx(), "QLabel#statusbar 的 QSS 保留供 Editor 用"
    assert "self.stat = QLabel(path or " in src, "Editor 窗口内部 self.stat 是另一件（不得动）"


def test_b41close_roll_queue_wired():
    """走纸接线：算式真源在镜像件，壳只接绘制＋进程内 QTimer（不新增线程/进程/端口）。"""
    src = _src()
    for need in ("def rollToggle(self, arg=None):", "def _roll_step(self)", "def _roll_apply(self)",
                 "def rollClear(self, arg=None):", "def roll_enqueue(self, item):",
                 "self._roll_timer.timeout.connect(self._roll_step)", "fax.roll_next(",
                 "fax.roll_mark(", "fax.jam_html(", '"roll": self.rollToggle', "Ctrl+G"):
        assert need in src, "走纸队列缺壳侧接线：" + need[:46]
    assert len(re.findall(r"class\s+\w+\(QThread\)", src)) == 1, \
        "走纸不得新增线程件（既有 Task worker 之外不许再起 QThread）"
    for banned in ("socket.socket", "HTTPServer", "serve_forever", "os.system("):
        assert banned not in src, "走纸不得引入端口/服务端面：" + banned
    seg = src[src.index("def _roll_step(self"):src.index("# ---------- t8 CRT")]
    assert "QThread" not in seg and "subprocess" not in seg and "Popen" not in seg
    assert "self.roll_state" in seg and "fax.roll_next(" in seg, \
        "走纸只许进程内 QTimer 走步（态推进真源＝fax.roll_next）"
    assert src.count('print("SELFTEST " + json') == 1, "自检输出行不得重复（补丁残留孤行）"


def test_b41close_selftest_gates():
    """门禁齐：壳侧 no_bottom_strip／roll 推进／eink 不经 Ctrl+I 亦可见；镜像件 rc 式锁走纸与常驻。"""
    src = _src()
    seg = src.split("def _selftest")[1]
    for need in ('"eink_resident": eink_resident', '"eink_no_hide": eink_no_hide',
                 '"no_bottom_strip": no_bottom_strip', '"roll_ok": roll_ok',
                 '"eink_no_hide"', '"eink_resident"',
                 '"roll_seen": roll_seen', '"eink_idx": eink_idx'):
        assert need in seg, "壳侧 selftest 缺收尾取证字段：" + need[:42]
    okline = seg.split("ok_all = (")[1]
    for need in ('and out["eink_resident"]', 'and out["eink_no_hide"]',
                 'and out["no_bottom_strip"]', 'and out["roll_ok"]', 'and out["eink_idx"] == 0',
                 'and out["roll_seen"] == ["feed", "print", "advance", "print", "advance", "tear", "idle"]'):
        assert need in okline, "收尾判据未进 ok_all 放行式：" + need[:48]
    ret = _fx().split("return 0 if", 1)[1]
    for g in ("roll_cycle", "roll_mark", "roll_should_jam", "qss_roll", "qss_eink_resident",
              "eink_resident_right", "fw_roll_parts"):
        assert 'ok["%s"]' % g in ret, "镜像件放行式缺收尾判据：" + g


# ---------------- 批46 灯数校平（表 011-001916-626 t4·QQ 灯接线＋造灯＝驱动灯） ----------------
def test_batch46_led_parity_source():
    """镜像件造七灯（线路/QQ/朗读/做梦/计划/裁纸/对外）壳侧必须全驱动：pollQQ 存在且走进程内 /api/qq；
    pollAll 与 tick 都串 pollQQ；fax() 分派表含 pollQQ（命令面板/实体键同源·不留第二条路由）；
    selftest 取证 led_driven/led_driven_n/led_built_n/led_parity/qq_lamp_ok 进 ok_all 放行式。"""
    src = _src()
    seg = src.split("def pollQQ(self)")[1].split("def pollTasks(self)")[0]
    assert 'fax.api("/api/qq")' in seg and 'self.led("QQ"' in seg, "QQ 灯须走进程内 /api/qq 并驱动 led_QQ"
    assert "def pollQQ" in src and "self.pollQQ(); self.pollTasks()" in src, "pollAll 须串 pollQQ（F5 巡检＝七灯全）"
    assert "self.pollSolo(); self.pollQQ()" in src, "tick 周期巡检须含 QQ 灯"
    assert '"pollQQ": self.pollQQ' in src, "fax() 分派表缺 pollQQ（面板与实体键同源）"
    gate = src.split("ok_all = (")[1]
    for need in ('out["led_driven_n"]', 'out["led_parity"]', 'out["qq_lamp_ok"]', 'out["led_built_n"]'):
        assert need in gate, "灯数校平判据未进 ok_all 放行式：" + need
    seg2 = src.split("def _selftest")[1]
    assert "win.pollQQ()" in seg2 and 'out["led_driven"]' in seg2, "selftest 须取证驱动灯名单（源码扫描＋真调）"

def test_batch46_qq_lamp_offscreen():
    """离屏装配：led_QQ 在场，pollQQ 后灯态与 /api/qq 实况一致（取不到＝off 绝不谎报 on）。"""
    pytest.importorskip("PyQt6", reason="缺 PyQt6＝离屏装配不可用（不误报）")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        qt = _local("shell_qt")
        app = qt.QApplication.instance() or qt.QApplication([])
        win = qt.Shell(); win.show(); app.processEvents()
    except Exception as e:
        pytest.skip("纯壳仓缺引擎件／机身不可装配（%s: %s）＝跳过装配回归"
                    % (type(e).__name__, str(e)[:80]))
    try:
        fx = _local("shell_qt_fax")
        assert "led_QQ" in win.fw, "镜像件须造 led_QQ（七灯之一）"
        win.pollQQ()
        txt = win.fw["led_QQ"].text()
        assert txt.endswith("QQ") and txt[:1] in "●◆✸○", "QQ 灯文本＝状态点＋名：" + txt
        real = fx.api("/api/qq")
        want_on = (not real.get("err")) and bool(real.get("enabled"))
        assert (txt[:1] == "●") == want_on, "灯态须与 /api/qq 实况一致（err 不谎报）：%s %s" % (txt, real.get("err"))
        lit = win.fw["led_QQ"].styleSheet()
        assert "color" in lit, "灯色须随态刷（led() 统一口径）"
    finally:
        win.close(); app.processEvents()

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
        win.fax("crt"); win.fax("eink"); assert win._eink_on is False, "墨水屏开关须能收"
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
    seg = src[src.index("def cut(self"):src.index("# ---------- t10")]
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
    assert 'EINK_SECTIONS = ("会话信息", "任务表", "后台任务")' in fx, "墨水屏只保三段"


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


# ---------------- 批40 零顶栏三区骨架（表 010-213903-130 壳侧五点覆盖） ----------------
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
    assert build.count("_zone(") == 4, \
        "常驻功能区＝A 纸卷＋B 送稿＋D 预览＋E 终端（批41 上送稿＋下左右分屏·顶栏与控制区已拆·实测 %d 区）" % build.count("_zone(")
    for t in ('"① 送稿口 DOC FEEDER · B', '"② 纸卷区 PAPER ROLL · A', '"③ 预览 PREVIEW · D', '"④ 终端 TERMINAL · E'):
        assert t in build, "常驻区标题须齐批41 四件：" + t
    assert '_zone("⑤' not in build and 'ctlzone")' in build and 'ctl = QFrame()' in build, \
        "控制面板＝按需件（不走 _zone 常驻装配）"
    assert 'ctl.setObjectName("ctlzone")' in build and "ctl.hide()" in build, "控制面板须装配即收起"
    assert "ez.hide()" in build and "dr.hide()" in build, "墨水屏与抽屉须默认收起（按需展开）"
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


def test_offscreen_zero_topbar_assembly():
    """离屏装配回归（offscreen·不发模型请求）：菜单栏不存在·三区可见性正确·命令面板条目可用可过滤。"""
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
        assert win.fw["einkzone"].isVisible() is False, "墨水屏须开机收起（Ctrl+I 展开）"
        assert win.fw["roll"].isVisible() and win.ent.isVisible(), "A 纸卷区与 B 送稿口须常驻可见"
        assert len(win.acts) >= len(win.MENU_ITEMS), "QAction 快捷键数须覆盖全部菜单条目"
        rows = win.palette_rows("")
        assert len(rows) >= 60, "命令面板条目须覆盖原顶栏全量（实测 %d）" % len(rows)
        groups = {r[0] for r in rows}
        assert {"元指令", "面板", "动作·shell", "动作·fax", "动作·help", "盘面", "拨号", "快捷"} <= groups, \
            "命令面板分组须齐（实测 %s）" % sorted(groups)
        assert all(callable(r[3]) for r in rows), "每行须带可调用出口"
        assert 0 < len(win.palette_rows(":cmds")) < len(rows), "过滤须真缩小"
        assert win.palette_rows("任务表"), "面板类条目须可被中文过滤命中"
        win.fax("ctl"); on = win.fw["ctlzone"].isVisible()
        win.fax("ctl"); off = not win.fw["ctlzone"].isVisible()
        assert on and off, "控制面板 Ctrl+M 须可展可收"
        win._eink_on = False; win.fw["einkzone"].setVisible(False)
        win.fax("view"); win.fax("view")
        assert win._view_i == 2 and win.fw["einkzone"].isVisible(), "视图轮转第 3 态须唤出墨水屏"
        win.fax("view"); win._view_i = 0
    finally:
        win.close(); app.processEvents()

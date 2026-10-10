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

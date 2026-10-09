#!/usr/bin/env python3
"""tests/test_shell_qt_fax.py — 批38 图形壳「网页端传真机镜像」离线回归：
镜像件在场（shell_qt_fax.py）＋零裸子进程＋版式常量真源＝网页端（META/PAD/QUICK/F1 从 web_page.html 现取）＋
样式表由 CSS 变量派生（渐变落地）＋密钥面结构性剔除（GUI 免密钥＝不起 HTTP·不读 token·不呈现 token/指纹）＋
抽屉面板数据桥＝web_shell 同一批 getter 名字。不建 QApplication·不连模型网关·不起端口。
跑法：pytest tests/test_shell_qt_fax.py -q"""
import os
import re
import sys
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "skill", "scripts")
sys.path.insert(0, S)
FAX = os.path.join(S, "shell_qt_fax.py")
QT = os.path.join(S, "shell_qt.py")
PAGE = os.path.join(S, "web_page.html")
def _src(p, why):
    assert os.path.isfile(p), why
    return open(p, encoding="utf-8", errors="replace").read()
def test_fax_module_present_and_quiet():
    src = _src(FAX, "缺 shell_qt_fax.py（图形壳传真机镜像件）")
    import no_window_audit as aud
    assert aud.hits(src, "shell_qt_fax.py") == [], "镜像件内不得有裸 subprocess/os.system（闪黑框根因）"
    assert os.path.isfile(QT), "缺 shell_qt.py（图形壳本体）"
    aud2 = _src(QT, "")
    assert aud.hits(aud2, "shell_qt.py") == [], "图形壳内裸子进程须带 # sms-visible 标记"
    assert "# sms-visible" in aud2, "GUI 另起 TUI 的可见控制台点必须带标记"
def test_version_source_is_web_page():
    """版式/键位真源＝网页端页面文本：CSS :root 变量与 JS 常量都在页面里，镜像件只解析不复制值。"""
    page = _src(PAGE, "缺 web_page.html（网页端界面＝图形壳版式真源）")
    import shell_qt_fax as fax
    v = fax.css_vars(page)
    for k in ("edge", "lcdfg", "paper", "ink", "amber"):
        assert v.get(k), "CSS 变量 --%s 未从网页端解析到" % k
        assert ("--" + k) in page, "页面里没有 --%s（镜像口径失真）" % k
    for name, minlen in (("META", 30), ("PAD", 10), ("QUICK", 6), ("F1", 4)):
        got = fax.js_const(name, page)
        assert got and len(got) >= minlen, "页面常量 %s 解析失败/过少" % name
    meta = fax.js_const("META", page)
    for m in ("help", "cmds", "config", "session"):
        assert m in meta, "META 键阵缺 :%s（网页端同名键）" % m
    q = fax.qss(fax.css_vars(page))
    assert "qlineargradient" in q, "样式表须由网页端渐变派生（qlineargradient）"
    assert '[sm="1"]' in q and 'tone="acc"' in q and 'tone="stop"' in q, "实体键五态×两尺寸须齐"
    assert "%s" not in q and "${" not in q, "样式表占位符未替换干净"
def test_gui_has_no_key_face():
    """GUI 端不做密钥验证：镜像件不开服务/不读 token 文件，壳侧只走进程内 api()。"""
    src = _src(FAX, "")
    qt = _src(QT, "")
    for bad in ("HTTPServer", "socketserver", "ssl.", "web.token", "check_token", "token(True)",
                "rotate", "serve_forever"):
        assert bad not in src, "镜像件不得触碰密钥/服务端面：" + bad
        assert bad not in qt, "图形壳不得触碰密钥/服务端面：" + bad
    assert "web_certs" not in src and "web_certs" not in qt, "GUI 不需要证书指纹面"
    assert re.search(r"def leaked", src), "需密钥面结构核对函数（自检硬判据）"
def test_data_bridge_same_names_as_web_shell():
    """面板数据＝web_shell 同一批 getter/poster（进程内直调），路径名与网页端逐字一致。"""
    src = _src(FAX, "")
    wsp = os.path.join(S, "web_shell.py")
    if not os.path.isfile(wsp):
        pytest.skip("web_shell.py 的真源在核仓（纯 SMS-shell 源仓无此件，覆盖安装后的混合体才有）")
    ws = _src(wsp, "缺 web_shell.py（面板 getter 真源）")
    import shell_qt_fax as fax
    for p in ("/api/tasks", "/api/perms", "/api/skills", "/api/plans", "/api/chains",
              "/api/sessions", "/api/files", "/api/detail", "/api/hud", "/api/qq", "/api/tts"):
        assert p in src, "镜像件缺面板路径 " + p
        assert p in ws, "网页端没有该路径（口径漂移）：" + p
    for post in ("/api/stop", "/api/resume", "/api/task/status", "/api/grant", "/api/plan/add"):
        assert post in src and post in ws, "写路径须两端同名：" + post
    assert "def api(" in src and "def scrub(" in src and "def panel_html(" in src
    assert fax.leaked({"token": "x"}) == "token", "密钥面核对须抓到 dict 里的 token 键"
    assert fax.leaked({"a": [{"fingerprint": "y"}]}) == "fingerprint", "须递归核对"
    assert fax.leaked(fax.scrub({"token": "x", "fingerprint": "y", "ok": 1})) == "", "scrub 后须干净"
def test_paper_and_drawer_render():
    import shell_qt_fax as fax
    h = fax.line_html("系统", "正文 <b> & 测试", "sys")
    assert "<b>" not in h and "&lt;b&gt;" in h, "纸面文本须转义（防串位注入）"
    assert "卡纸 JAM" in fax.jam_html("面板不可用")
    t = fax.table(["id:行", "goal:目标"], [{"id": "t1", "goal": "x<&"}])
    assert "<th>行</th>" in t and "&lt;&amp;" in t, "抽屉表格须转义＋中文表头"
    for nm in ("tasks", "perms", "skills", "config", "plans", "chains", "sessions"):
        assert fax.panel_html(nm, {"err": "面板坏了"}).find("卡纸 JAM") >= 0, nm + " 出错须打纸卡"
    assert "（空）" in fax.panel_html("tasks", {})
def test_shell_wired_to_fax():
    qt = _src(QT, "")
    for call in ("import shell_qt_fax as fax", "fax.build(self, self.ent)", "fax.qss()",
                 "fax.api(", "fax.line_html(", "shell_qt_fax.py"):
        assert call in qt, "图形壳须接镜像件：" + call
    assert "配对令牌" not in qt, "图形壳不得留网页端门禁（密钥验证）文案"
    for keep in ("core.handle(", "msg_flow.visible(", "detail_bus.tail(", "stop.bind(",
                 "--probe=", "probe_finish", "def _scripts()"):
        assert keep in qt, "旧壳引擎口径不得丢：" + keep
def test_lifecycle_and_entries_know_fax():
    lc = _src(os.path.join(S, "shell_lifecycle.py"), "")
    assert "shell_qt.py" in lc, "壳生命周期回收清单须含 shell_qt.py"
    ent = _src(os.path.join(ROOT, "bin", "sms-shell-gui.py"), "缺图形入口")
    assert "shell_qt.py" in ent, "图形入口须指向 shell_qt.py"
def test_overlay_keeps_fax_pair():
    """覆盖安装边界：镜像件属壳层件（shell*），否则会进 core 却被 stale 清理 prune＝图形壳瞎掉。"""
    src = open(os.path.join(os.path.dirname(ROOT), "SMS-shell", "install_overlay.py"),
               encoding="utf-8", errors="replace").read() if os.path.isfile(
        os.path.join(os.path.dirname(ROOT), "SMS-shell", "install_overlay.py")) else ""
    if src:
        assert "shell[^/]*" in src, "壳层清单正则须以 shell* 覆盖新件（shell_qt_fax.py）"
        assert os.path.isfile(FAX) and os.path.isfile(os.path.join(os.path.dirname(ROOT), "SMS-shell",
                                       "skill", "scripts", "shell_qt_fax.py")), "镜像件须同时在壳层仓与核仓"

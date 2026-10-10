#!/usr/bin/env python3
"""tests/test_shell_qt_fax.py — 批38 图形壳「网页端传真机镜像」离线回归：
镜像件在场（shell_qt_fax.py）＋零裸子进程＋版式常量真源＝网页端（META/PAD/QUICK/F1 从 web_page.html 现取）＋
样式表由 CSS 变量派生（渐变落地）＋密钥面结构性剔除（GUI 免密钥＝不起 HTTP·不读 token·不呈现 token/指纹）＋
抽屉面板数据桥＝web_shell 同一批 getter 名字。不建 QApplication·不连模型网关·不起端口。
跑法：pytest tests/test_shell_qt_fax.py -q"""
import os
import re
import sys
import time
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
def _local(name):
    """按本仓文件路径取镜像件：混合安装环境里引擎件会把核仓旧副本插到 sys.path 前，
    裸 import 可能测到旧版 shell_qt_fax.py（本批三视图件就在本仓文件里）。"""
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


def test_t6_cut_blade_states_and_visual():
    """t6 裁纸：五态推进闭环＋刀条视觉随态换（纯算式＋QSS，无新端口/新进程）。"""
    fax = _local("shell_qt_fax")
    states = [s[0] for s in fax.CUT_STEPS]
    assert states == ["idle", "feed", "clamp", "cut", "drop"], "裁纸须五态：送纸→压脚→刀刃→落盘→待机"
    s, seen = "idle", []
    for _ in range(len(states)):
        s = fax.cut_next(s); seen.append(s)
    assert seen == ["feed", "clamp", "cut", "drop", "idle"], "状态推进须成环回 idle"
    assert fax.cut_next("bogus") == "feed", "非法态当 idle 起步"
    assert fax.cut_progress("idle") == 0.0 and fax.cut_progress("drop") == 1.0
    assert 0 < fax.cut_progress("cut") < 1 and fax.cut_progress("nope") == 0.0
    assert fax.cut_label("cut") and fax.cut_tone("cut") == "stop" and fax.cut_tone("feed") == "warn"
    m = fax.cut_mark(3)
    assert "裁纸段 3" in m and "<script" not in m and "animation" not in m
    q = fax.qss()
    for st in ("feed", "clamp", "cut", "drop"):
        assert 'QFrame#blade[st="%s"]' % st in q, "刀条缺态样式：" + st
    assert "QLabel#bladeTag" in q and "QFrame#blade{" in q, "刀条本体/标签样式须在场"
    src = _src(FAX, "")
    for banned in ("QThread", "subprocess", "socket", "HTTPServer", "serve_forever"):
        assert banned not in src, "裁纸（镜像件）不得引入新进程/端口面：" + banned


def test_css_vars_ttl_cache_keeps_live_source():
    """配色取样缓存：每帧取样（LED/banner/CRT 成像）不得逐帧读盘，但显式传 src 与 TTL 过期仍现算。
    （不用 importlib.reload——meta_path 会按 sys.path 重新解析到核仓同名旧件，把本仓件换掉。）"""
    fax = _local("shell_qt_fax")
    src = _src(PAGE, "缺 web_page.html")
    fax._cache.pop("vars", None)
    a = fax.css_vars()                      # 缺省路径：现取页面并入 5s TTL 缓存
    assert a.get("crtf") == "#33ff66" and a.get("einkb"), "内置兜底须把 CRT/E-INK 变量补进配色表"
    assert "vars" in fax._cache, "缺省取样须落缓存（每帧取样不逐帧读盘）"
    b = fax.css_vars()
    assert b == a and b is not a, "二次取样＝命中缓存（值同·非同一对象，防调用方就地改表）"
    c = fax.css_vars(src)                   # 显式 src：不吃缓存、现算
    assert c == a, "显式传页面文本仍须同值（口径不分裂）"
    fax._cache["vars"] = (time.time() - 999, dict(a))      # 假过期
    assert fax.css_vars().get("lcdfg"), "TTL 过期须回现取页面"
    assert fax.css_vars("") == {k: fax.ROOT_DEFAULT[k] for k in fax.ROOT_DEFAULT}, "空页面＝全兜底"


def test_t8_crt_phosphor_math_and_qss():
    """t8 CRT：绿字黑底（#33ff66 系）＋扫描线＋余辉衰减＋块光标算式＋送稿口 QSS 实色底。"""
    fax = _local("shell_qt_fax")
    c = fax.crt_colors({})
    assert c["fg"] == "#33ff66" and c["bg"] == "#04070a", "CRT 须绿字黑底"
    assert fax.crt_colors({"crtf": "#00ff88"})["fg"] == "#00ff88", "网页端同名 :root 变量须优先"
    assert fax.crt_scanlines(60, 3) == list(range(0, 60, 3)), "扫描线按 gap 逐条"
    assert len(fax.crt_scanlines(9, 2)) == 5 and fax.crt_scanlines(0) == [] and fax.crt_scanlines(-5) == []
    assert fax.crt_scanlines(6, 1) == [0, 2, 4], "gap 下限 2 防糊"
    assert fax.crt_afterglow(0) == 1.0 and fax.crt_afterglow(-3) == 1.0
    assert abs(fax.crt_afterglow(260) - 0.5) < 1e-6 and abs(fax.crt_afterglow(520) - 0.25) < 1e-6
    assert fax.crt_afterglow(260, 130) == 0.25, "半衰期可调"
    assert fax.crt_afterglow("x") == 1.0, "非法输入不得抛（成像失败不影响输入）"
    assert fax.crt_block_cursor(13) == 8 and fax.crt_block_cursor(0) == 2, "块光标≈0.62 字宽·下限 2px"
    q = fax.qss()
    assert 'QPlainTextEdit#cmd[crt="1"]' in q and 'QPlainTextEdit#cmd[crt="1"]:focus' in q, "送稿口须有 CRT 态样式"
    assert "${crtb}" not in q and "${crtf}" not in q, "CRT 色须替换干净（Template 无漏）"
    assert "#33ff66" in q, "QSS 里须见绿字真值"


def test_t10_eink_three_sections_only():
    """t10 墨水屏：三段固定＝会话信息／任务表／后台任务；低饱和灰白＋无动效＋仿电子墨水印。"""
    fax = _local("shell_qt_fax")
    assert list(fax.EINK_SECTIONS) == ["会话信息", "任务表", "后台任务"], "墨水屏只保三段"
    h = fax.eink_html({"session": "sess1234", "gateway": {"enabled": True, "model": "m"},
                       "solo": {"enabled": True}},
                      {"tid": "task-7", "done": 2, "total": 5, "unfinished": 3, "eta": "1m",
                       "intent": "示例", "rows": [{"id": "t1", "goal": "g", "status": "done", "skill": "s"}]},
                      [("t9", "话语", 1.5)])
    assert all(s in h for s in fax.EINK_SECTIONS)
    assert "sess1234" in h and "task-7" in h and "话语" in h, "三段须各带本体数据"
    assert h.count('border:1px solid #b9bfba') == 3, "只此三个盒（其余面板不上屏）"
    for bad in ("animation", "transition", "@keyframes", "gradient", "rgba(", "blur"):
        assert bad not in h, "墨水屏须无动效/无渐变（仿电子墨水印刷）：" + bad
    assert fax.eink_html().count("（无）") >= 1, "无数据时显（无），不静默"
    assert "E-INK" in h, "须带仿电子墨水印"
    assert fax.leaked(fax.scrub(hink := {"token": "x", "fingerprint": "y"})) == "", "上屏数据须过密钥面剔除"
    q = fax.qss()
    assert "QTextBrowser#eink{" in q and "QFrame#einkzone{" in q, "墨水屏区带样式须在场"


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
    for call in ("def _load_fax()", "fax = _load_fax()", "spec_from_file_location",
                 "fax.build(self, self.ent)", "fax.qss()", "fax.api(", "fax.line_html(",
                 "shell_qt_fax.py"):
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

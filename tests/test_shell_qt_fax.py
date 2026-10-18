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
import inspect
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
    """t10 墨水屏：三段固定＝会话信息／任务总览／后台任务；低饱和灰白＋无动效＋仿电子墨水印。"""
    fax = _local("shell_qt_fax")
    assert list(fax.EINK_SECTIONS) == ["会话信息", "任务总览", "后台任务"], "墨水屏只保三段"
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


# ---------------- 批40 零顶栏＋批41 分屏骨架（表 010-213903-130／010-231707-890 镜像件侧覆盖） ----------------
def test_fax_qss_covers_on_demand_layer():
    """样式表须补齐按需层且不再含 brand 横条选择器：ctlzone／palette／palList／palEdit／mouth 走纸态。"""
    fax = _local("shell_qt_fax")
    q = fax.qss(fax.css_vars())
    for need in ("QFrame#ctlzone{", "QDialog#palette{", "QListWidget#palList{", "QLineEdit{",
                 'QFrame#mouth[st="feed"]', "QFrame#tear[st="):
        assert need in q, "按需层样式缺失：" + need
    assert "QLabel#" + "brand{" not in q and "brand" + "Sub" not in q, "brand 横条样式须随顶栏一并拆掉"
    assert "${" not in q and "%s" not in q, "样式表占位符未替换干净"
    assert "qlineargradient" in q, "零顶栏后机身仍须网页端渐变派生"


def test_fax_build_zero_topbar_and_key_compat():
    """装配件＝零顶栏：无 brand 横条、控制面装配即收起；fw 键面与批38/39 逐字兼容（tests 与壳两侧共用）。"""
    src = _src(FAX, "")
    build = src.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    assert "SMS-" + "FAX · GUI" not in src, "brand 横条文案不得残留于镜像件"
    assert 'w["ctlzone"]' in build and 'w["ctlzone_btn"]' in build, "控制面板须按需化（含唤出键）"
    assert "ctl.hide()" in build, "控制面板装配即收起（不常驻占高）"
    for keep in ("w[\"banner\"]", 'w["roll"]', 'w["mouth"]', 'w["tear"]', 'w["blade"]',
                 'w["blade_tag"]', 'w["blade_pos"]', 'w["eink"]', 'w["einkzone"]',
                 'w["drawer"]', 'w["dtitle"]', 'w["dbody"]', 'w["btn_stop"]', 'w["btn_go"]',
                 'w["btn_all"]', 'w["btn_speak"]', 'w["keys"]'):
        assert keep in build, "批38/39 fw 键面须逐字保留：" + keep
    assert 'w["lcd_" + k]' in build and 'w["led_" + nm]' in build, "LCD/LED 仍由循环产出（键名不变）"
    assert "menuBar" not in src, "镜像件不得代壳挂原生菜单栏"


def test_fax_selftest_gates_zero_topbar():
    """镜像件 selftest 须把零顶栏当硬判据并入放行式（rc=0 才放行·防只改视觉不进门禁）。"""
    src = _src(FAX, "")
    for need in ('ok["qss_topbar"]', 'ok["build_zero_topbar"]',
                 'and ok["qss_topbar"] and ok["build_zero_topbar"]',
                 'nb = "SMS-" + "FAX · GUI"', 'bs = "brand" + "Sub"',
                 'pf = ("sub" + "process"'):
        assert need in src, "镜像件 selftest 缺零顶栏判据/自指拆分：" + need[:44]
    # 放行式只锁「判据进了 rc 式」这一语义（不锁行尾邻接：后续批次增判据会让 ) else 1 移位＝脆锁）
    ret = src.split("return 0 if", 1)[1]
    for g in ("qss_topbar", "build_zero_topbar", "assembly_no_process_face", "fw_batch41_keys"):
        assert 'ok["%s"]' % g in ret, "判据未进放行式（rc 不受它约束）：" + g
    assert "else 1" in ret, "放行式须留 rc=1 拒绝支"
    seg = src.split("def selftest")[1]
    assert "SMS-FAX · GUI" not in seg.replace('nb = "SMS-" + "FAX · GUI"', ""), \
        "判据字面量须拆分，否则自指含被检串＝恒假阴（本批踩过）"


# ---------------- 批41 上送稿口＋下左右分屏（表 010-231707-890 镜像件侧） ----------------
def test_fax_qss_covers_split_preview_terminal():
    """样式表须补齐批41 分屏／预览／终端三段选择器（QSplitter 手柄·纸墨预览底·行号栏·CRT 同族终端面）。"""
    fax = _local("shell_qt_fax")
    q = fax.qss(fax.css_vars())
    for need in ("QSplitter#split", "QSplitter#psplit", "QSplitter#split::handle:horizontal",
                 "QSplitter#psplit::handle:vertical", "QFrame#previewzone{", "QPlainTextEdit#preview{",
                 "QLabel#lnr{", "QLineEdit#pvOpen{", "QFrame#termzone{", "QPlainTextEdit#term{",
                 "QLineEdit#termIn{"):
        assert need in q, "批41 样式缺失：" + need
    assert "${" not in q and "%s" not in q, "样式表占位符未替换干净"
    assert "qlineargradient" in q and "QLabel#" + "brand{" not in q, "仍须网页端渐变派生·不得回流 brand 横条"


def test_fax_build_batch41_split_and_parts():
    """装配真源＝镜像件 build()：上送稿口（第一位）＋QSplitter 左右分屏＋右栏两件；批38/39/40 键面逐字保留。"""
    src = _src(FAX, "")
    build = src.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    core = build.split('"""', 2)[-1]
    code = core
    assert build.count("_zone(") == 4, "功能区＝A 纸卷／B 送稿／D 预览／E 终端（实测 %d）" % build.count("_zone(")
    for need in ('w["split"] = split', 'w["psplit"] = psplit', "split.addWidget(tray)",
                 "split.addWidget(aside)", "av.addWidget(psplit, 1)", "psplit.addWidget(pvz)", "psplit.addWidget(tmz)",
                 "setChildrenCollapsible(False)", "split.setSizes([760, 640])",
                 "root.addWidget(split, 1)", 'w["feeder"] = feeder', "feeder.setMinimumHeight(96)"):
        assert need in build, "批41 装配缺项：" + need[:40]
    assert "root.addWidget(tray, 3)" not in build, "纸卷 A 不再直挂 root（已进分屏左格）"
    for k in ("preview", "previewzone", "pv_open", "pv_stat", "pv_fold", "pv_src",
              "term", "termzone", "term_in", "t_run", "t_fold", "t_paper", "t_clear", "t_stat"):
        assert ('w["%s"]' % k) in build, "批41 fw 键缺：" + k
    for keep in ('w["banner"]', 'w["roll"]', 'w["mouth"]', 'w["tear"]', 'w["blade"]', 'w["blade_tag"]',
                 'w["blade_pos"]', 'w["eink"]', 'w["einkzone"]', 'w["drawer"]', 'w["dtitle"]',
                 'w["dbody"]', 'w["btn_stop"]', 'w["btn_go"]', 'w["btn_all"]', 'w["btn_speak"]',
                 'w["keys"]', 'w["ctlzone"]', 'w["ctlzone_btn"]'):
        assert keep in build, "批38/39/40 键面须逐字保留：" + keep
    assert 'w["lcd_" + k]' in build and 'w["led_" + nm]' in build, "LCD/LED 仍由循环产出（键名不变）"
    assert "ctl.hide()" in code and "dr.hide()" in code and "ez.hide()" not in code, \
        "控制面板／抽屉仍装配即 hide·C 墨水屏常驻右栏（批41 收尾不得 hide）"
    assert '"① 送稿口 DOC FEEDER · B' in build and '"② 纸卷区 PAPER ROLL · A' in build, \
        "区序须＝送稿口第一（编号与位次一致）"
    assert "menuBar" not in src and "SMS-" + "FAX · GUI" not in src, "零顶栏口径不得回退"


def test_fax_batch41_pure_math_single_source():
    """轮转位次／预览取数／终端行分类算式＝镜像件真源（壳只接绘制与状态·不留两份口径）。"""
    fax = _local("shell_qt_fax")
    assert list(fax.VIEW_NAMES) == ["纸卷 A", "送稿 B", "墨水屏 C", "预览 D", "终端 E"]
    assert [fax.view_next(i) for i in range(5)] == [1, 2, 3, 4, 0]
    assert fax.view_next("x") == 0 and fax.view_next(-2) == 0 and fax.view_next(None) == 0
    assert fax.view_name(3) == "预览 D" and fax.view_name(7) == "墨水屏 C", "轮转越界回绕"
    r = fax.preview_text({"content": "a\nb\nc"})
    assert r["lines"] == 3 and r["text"] == "a\nb\nc" and not r["fallback"]
    assert fax.preview_text({})["fallback"] and fax.preview_text(None)["fallback"], "取不到须内置兜底"
    lst = fax.preview_text({"files": [{"name": "a.py", "path": "C:/x/a.py", "size": 9, "type": "file"}]})
    assert lst["lines"] == 1 and "a.py" in lst["text"] and not lst["fallback"]
    assert fax.preview_text({"err": "越界", "content": "x"})["err"] == "越界", "err 须原样带回由壳侧打纸"
    assert fax.term_line_kind("$ dir") == "sh" and fax.term_line_kind(":cmds") == "meta"
    assert fax.term_line_kind("JAM 卡纸") == "err" and fax.term_line_kind("rc=2") == "err"
    assert fax.term_line_kind("Traceback (most recent call last):") == "err"
    assert fax.term_line_kind("plain") == "out" and fax.term_line_kind("") == "out"
    assert fax.TERM_PROMPT == "$ "


def test_fax_api_query_get_inprocess_only():
    """批41 预览取数仍＝进程内 web_shell 同名 getter（query＝网页端 ?k=v 同义），POST 路一字未动。"""
    import inspect
    fax = _local("shell_qt_fax")
    assert "query" in inspect.signature(fax.api).parameters, "api() 须带 query（/api/file?path=…）"
    src = _src(FAX, "")
    for p in ("/api/files", "/api/file", "/api/detail"):
        assert p in src, "镜像件缺预览路径 " + p
    wsp = os.path.join(os.path.dirname(S), "..", "SMS-core", "skill", "scripts", "web_shell.py")
    if not os.path.isfile(wsp):
        wsp = os.path.join(S, "web_shell.py")
    if os.path.isfile(wsp):
        ws = _src(wsp, "")
        for fn in ("g_files", "g_file", "g_detail"):
            assert ('"%s": "%s"' % ("/api/" + fn[2:], fn)) in src, \
                "路径名须与 web_shell getter 同名：" + fn
            assert ("def %s(" % fn) in ws, "网页端没有该 getter（口径漂移）：" + fn
    for banned in ("HTTPServer", "sock" + "etserver", "serve_forever", "requests", "urllib", "check_token"):
        assert banned not in src, "镜像件不得触碰服务端/密钥面：" + banned
    assert "def preview_text(" in src and "FALLBACK_TEXT" in src, "预览兜底须内置（离仓仍可成图）"


def test_fax_selftest_gates_batch41():
    """镜像件 selftest 须把批41 判据并入放行式（rc=0 才放行·防只改视觉不进门禁）。"""
    src = _src(FAX, "")
    for need in ('ok["view_cycle5"]', 'ok["qss_split"]', 'ok["qss_preview"]', 'ok["qss_terminal"]',
                 'ok["build_split_assembly"]', 'ok["build_preview_parts"]', 'ok["build_terminal_parts"]',
                 'ok["build_feeder_first"]', 'ok["assembly_no_process_face"]', 'ok["fw_batch41_keys"]',
                 'ok["api_query_get"]', 'ok["preview_helpers"]', 'ok["term_helpers"]',
                 'and ok["view_cycle5"] and ok["qss_split"]', 'and ok["preview_helpers"] and ok["term_helpers"]'):
        assert need in src, "镜像件 selftest 缺批41 判据/放行：" + need[:46]
    seg = src.split("def selftest")[1]
    tail = seg.split('print("FAX_SELFTEST')[1]
    for g in ('ok["view_cycle5"]', 'ok["qss_split"]', 'ok["qss_preview"]', 'ok["qss_terminal"]',
              'ok["build_split_assembly"]', 'ok["build_preview_parts"]', 'ok["build_terminal_parts"]',
              'ok["build_feeder_first"]', 'ok["assembly_no_process_face"]', 'ok["fw_batch41_keys"]',
              'ok["api_query_get"]', 'ok["preview_helpers"]', 'ok["term_helpers"]'):
        assert g in tail, "批41 判据须进 return 放行式（rc=0 才放行）：" + g
    assert seg.count('print("FAX_SELFTEST " + json') == 1, "镜像件自检输出行须唯一"


# ---------------- 批41 分屏／预览／终端（镜像件纯算式与 QSS·表 010-230506-244） ----------------
def test_fax_batch41_pure_math():
    """批41 纯算式真源＝镜像件（壳只接绘制与状态）：五态轮转／预览收口／终端行分类，逐项可对。"""
    fax = _local("shell_qt_fax")
    assert list(fax.VIEW_NAMES) == ["纸卷 A", "送稿 B", "墨水屏 C", "预览 D", "终端 E"]
    assert [fax.view_next(i) for i in range(5)] == [1, 2, 3, 4, 0], "轮转须成环回 0"
    assert fax.view_next("x") == 0, "非法位次当首位起步"
    assert fax.view_name(3) == "预览 D"
    assert fax.preview_text({"content": "x\ny"})["lines"] == 2
    assert fax.preview_text({"err": "没门"})["fallback"] is True, "取不到须内置兜底"
    assert fax.preview_text({"files": [{"name": "a.py", "size": 3,
                                        "type": "file"}]})["lines"] == 1, "文件列表收一行一件"
    assert fax.term_line_kind("$ dir") == "sh", "命令回显＝提示符行"


# ---------------- 批40 图形壳布局补齐（表 010-213457-793 行 t7·镜像件侧版式结构断言） ----------------
def test_fax_build_batch40_top_input_bottom_split_layout():
    """版式结构（取证＝build 源码段）：(a) 送稿口（输入 ent）装配在分屏之前＝上输入；
    (b) 主分屏＝QSplitter＋水平方向；(c) splitter 至少 addWidget 两次，右列容器 aside 依次装 ctl→墨水屏→抽屉。"""
    src = _src(FAX, "")
    build = src.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    code = build.split('"""', 2)[-1]
    rooty = re.findall(r"root\.addWidget\((\w+)", code)
    assert 'feeder, zv = _zone("' in build and "送稿口 DOC FEEDER" in build, "(a) 输入区须存在（① 送稿口）"
    assert code.index("root.addWidget(feeder)") < code.index("split = QSplitter(Qt.Orientation.Horizontal)"), \
        "(a) 送稿口装配位次须在分屏之前＝输入在上"
    assert rooty == ["feeder", "split"], "(a) root 只许两格＝上送稿口＋下分屏（实测 %s）" % rooty
    assert "QSplitter" in code and "Qt.Orientation.Horizontal" in code, "(b) 主分屏须 QSplitter＋水平方向"
    assert code.count("split.addWidget(") >= 2, "(b) splitter 须至少挂两个子件（左纸卷＋右列）"
    assert "split.setChildrenCollapsible(False)" in code and "split.setSizes([760, 640])" in code, \
        "(b) 分屏须防拖没＋左右初值"
    assert "split.addWidget(tray)" in code and "split.addWidget(aside)" in code, "(c) 左＝纸卷 A·右＝aside 竖列"
    for n, wg in (("ctl", "av.addWidget(ctl)"), ("drawer", "av.addWidget(dr)"), ("eink", "psplit.addWidget(ez)")):
        assert wg in code, "(c) 右列容器缺按需件：" + n
    assert code.index("av.addWidget(ctl)") < code.index("av.addWidget(dr)"), "(c) 按需次序须 ctl→抽屉"
    assert "ez.hide()" not in code and "av.addWidget(ez)" not in code, \
        "(c) C 常驻＝永不 hide／不回落按需层（批41 收尾）"
    assert "av.addWidget(psplit, 1)" in code, "(c) 右列最上＝分屏两件（D 预览／E 终端）"
    for h in ("ctl.hide()", "dr.hide()"):
        assert h in code, "按需层须装配即 hide（C 除外）：" + h
    assert build.count("_zone(") == 4, "常驻功能区仍＝A/B/D/E 四区（aside 不走 _zone·实测 %d）" % build.count("_zone(")


def test_fax_selftest_gates_split_layout():
    """镜像件 selftest 须把版式补齐当硬判据：ok["split_layout"] 取证＋split_layout_ok 并入放行式。"""
    src = _src(FAX, "")
    for need in ('ok["split_layout"] = {', '"top_input":', '"horizontal_splitter":', '"right_column":',
                 '"fw_keyface":', 'ok["split_layout_ok"] = all(',
                 'and ok["split_layout_ok"] and ok["assembly_no_process_face"]'):
        assert need in src, "镜像件 selftest 缺版式判据：" + need[:46]
    ret = src.split("return 0 if", 1)[1]
    assert 'ok["split_layout_ok"]' in ret and "else 1" in ret, "split_layout_ok 未进放行式（rc 不受它约束）"


# ---------------- 批41 收尾三处偏差（表 010-235956-984）镜像件侧 ----------------
def test_b41close_fax_roll_math():
    """走纸队列纯算式（与 CUT 同族）：六态含卡纸·成环·行程数值·渲染真源仍＝line_html。"""
    fax = _local("shell_qt_fax")
    assert [s0[0] for s0 in fax.ROLL_STEPS] == ["idle", "feed", "print", "advance", "tear", "jam"]
    st, seen = "idle", []
    for _ in range(5):
        st = fax.roll_next(st, at_end=(len(seen) >= 3)); seen.append(st)
    assert seen == ["feed", "print", "advance", "tear", "idle"], "走纸须成环：咬纸→打印→进给→撕纸→待机"
    assert fax.roll_next("advance") == "print" and fax.roll_next("advance", at_end=True) == "tear"
    assert fax.roll_next("idle", jam=True) == "jam" and fax.roll_next("jam") == "jam"
    assert fax.roll_next("jam", cleared=True) == "print", "清纸＝续打同一行（恢复）"
    assert fax.roll_next("bogus") == "feed" and fax.roll_next("print") == "advance"
    assert fax.roll_progress("idle") == 0.0 and fax.roll_progress("tear") == 1.0
    assert 0 < fax.roll_progress("print") < 1 and fax.roll_progress("jam") == 0.0
    assert fax.roll_tone("jam") == "stop" and fax.roll_tone("advance") == "go"
    assert fax.roll_should_jam(2) is False and fax.roll_should_jam(3) is True
    m = fax.roll_mark(4, "print")
    assert "第 4 条" in m and "<div" in m and "<b>" not in m
    assert "animation" not in m and "transition" not in m
    assert "line_html" in inspect.getsource(fax.roll_mark), "走纸印记不得复制第二份渲染真源"


def test_b41close_fax_qss_and_resident():
    """样式表＝走纸六态＋常驻墨水屏（实色无动效）＋墨水小标；门禁须齐并进 rc 放行式。"""
    fax = _local("shell_qt_fax")
    q = fax.qss(fax.css_vars())
    for st in ("print", "advance", "tear", "jam"):
        assert 'QFrame#mouth[st="%s"]' % st in q and 'QFrame#tear[st="%s"]' % st in q, "走纸态样式缺失：" + st
    assert 'QFrame#einkzone[resident="1"]' in q and "QLabel#einkStat{" in q
    assert "QLabel#rollTag[st=" in q and "QLabel#rollTag{" in q
    assert "${" not in q and "@keyframes" not in q, "墨水屏面须实色无动效"
    src = _src(FAX, "")
    ret = src.split("return 0 if", 1)[1]
    for g in ("roll_cycle", "roll_mark", "roll_tone", "roll_progress", "roll_should_jam",
              "qss_roll", "qss_eink_resident", "eink_resident_right", "fw_roll_parts"):
        assert 'ok["%s"]' % g in ret, "镜像件放行式缺收尾判据：" + g
    build = src.split("def build(win, ent):")[1].split("# ---------------- t6 裁纸刀")[0]
    code = build.split('"""', 2)[-1]
    assert "psplit.addWidget(ez)" in code
    assert code.index("psplit.addWidget(ez)") < code.index("psplit.addWidget(pvz)")
    assert "ez.hide()" not in code and "av.addWidget(ez)" not in code, "C 常驻＝永不 hide／不回落按需层"


def test_b41close_fax_eink_api_no_token():
    """墨水屏数据面只取 /api/info ＋ /api/tasks（scrub 后无 token/指纹），三段仍只三段。"""
    fax = _local("shell_qt_fax")
    assert list(fax.EINK_SECTIONS) == ["会话信息", "任务总览", "后台任务"] and len(fax.EINK_SECTIONS) == 3
    info = fax.scrub({"session": "abc12345", "token": "SECRET", "fingerprint": "fp",
                      "gateway": {"enabled": True, "model": "m"}, "solo": {"enabled": True}})
    tasks = fax.scrub({"tid": "task-9", "done": 1, "total": 3, "unfinished": 2, "eta": "2m",
                       "intent": "收尾示例", "rows": [{"id": "t1", "goal": "g", "status": "running"}],
                       "token": "SECRET"})
    h = fax.eink_html(info, tasks, [("t7", "走纸示例话语", 3.0)])
    assert fax.leaked(h) == "", "墨水屏 HTML 不得残留密钥面字段"
    assert "SECRET" not in h
    assert "task-9" in h and "走纸示例话语" in h and all(x in h for x in fax.EINK_SECTIONS)
    assert h.count("border:1px solid #b9bfba") == 3, "e-ink 三段框须恰三个（不增段）"
    assert not any(bad in h for bad in ("animation", "transition", "gradient", "@keyframes"))
    for bad in ("HTTPServer", "sock" + "etserver", "serve_forever", "check_token", "requests", "urllib"):
        assert bad not in _src(FAX, ""), "镜像件不得触碰服务端/密钥面：" + bad

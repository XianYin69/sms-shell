#!/usr/bin/env python3
"""install_overlay.py — SMS-shell → SMS-core 覆盖安装（批34 双仓口径的落地件）：
把本仓壳层文件（skill/scripts/shell_*.py＋shell.py＋web_page.html＋bin/*＋根入口三件）
复制进 SMS-core 工作区（core .gitignore 隔离，不追踪），＝运行时混合体。
默认预览，--write 才落盘；--src/--dst 可改路径。
批34 边界根治：目标核仓不再硬编码本机绝对路径，改按 env SMS_CORE →
<SMS_HOME>/config 的 sms_skill → 相邻 ../SMS-core 三级找回（与 sms.py 的
_core_scripts 同口径），换机器/换目录后覆盖安装仍然可用。"""
import io, os, sys, json, shutil, re

HERE = os.path.dirname(os.path.abspath(__file__))


def _ok(p):
    """核仓判据：存在 skill/scripts/resolve_home.py（sms.py 同源判据）。"""
    return bool(p) and os.path.isfile(os.path.join(p, "skill", "scripts", "resolve_home.py"))


def find_core():
    """核仓定位三级找回：env → 配置 sms_skill → 相邻 SMS-core；找不到返回空串。"""
    c = os.environ.get("SMS_CORE") or ""
    if _ok(c):
        return c
    hm = os.environ.get("SMS_HOME") or ""
    if not hm:
        home = os.path.expanduser("~")
        loc = os.environ.get("LOCALAPPDATA") or (
            os.path.join(home, "Library", "Caches") if sys.platform == "darwin"
            else os.path.join(home, ".cache"))
        for cand in (os.path.join(loc, "SMS"), os.path.join(home, "SMS")):
            if os.path.isfile(os.path.join(cand, "config", "config.json")):
                hm = cand
                break
    if hm:
        try:
            with io.open(os.path.join(hm, "config", "config.json"), encoding="utf-8-sig") as f:
                c = json.load(f).get("sms_skill") or ""
        except Exception:
            c = ""
        if _ok(c):
            return c
    for cand in ("SMS-core", "sms-core", "SMS", "smsystem-suit", "skill_manage_system"):
        p = os.path.normpath(os.path.join(HERE, "..", cand))
        if _ok(p):
            return p
    return ""


args = sys.argv[1:]
write = "--write" in args


def _opt(name, dft):
    for a in args:
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return dft


src = _opt("--src", HERE)
dst = _opt("--dst", find_core())
if not _ok(dst):
    print(json.dumps({"error": "未找到 SMS-core（设 env SMS_CORE、或 config sms_skill、或相邻目录 SMS-core）",
                      "tried": [os.environ.get("SMS_CORE", ""), dst]}, ensure_ascii=False))
    sys.exit(2)


def shell_files(base):
    """本仓壳层清单：bin/* ＋ 根入口三件 ＋ skill/scripts/shell_*.{py,ps1} ＋ shell.py ＋ web_page.html。"""
    out = []
    for dp, dn, fn in os.walk(base):
        rel = os.path.relpath(dp, base).replace("\\", "/")
        top = rel.split("/")[0] if rel != "." else ""
        if top in {".git", "__pycache__", ".pytest_cache", "tmp", ".kilo", "node_modules"}:
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in {".git", "__pycache__", ".pytest_cache", "tmp",
                                           ".kilo", "node_modules"}]
        for f in fn:
            p = (rel + "/" + f).lstrip("./")
            # 壳层自有件＝核仓不追踪者；core 独有件（sys_shells/web_shell 等）绝不列此，
            # 否则覆盖安装会把「核」再抄回核仓＝双仓边界二次混淆。
            if (p.startswith("bin/") or p in ("sms.py", "sms", "sms.cmd")
                    or re.match(r"skill/scripts/shell[^/]*\.(py|ps1)$", p)  # 批38：stale 侧原 \\.（两反斜杠）永不命中，归一为 \.
                    or re.match(r"tests/test_shell_qt[^/]*\.py$", p)  # 批38：图形壳传真机镜像回归随壳层件同族进出
                    or p == "skill/scripts/web_page.html"):
                out.append(p)
    return out


rels = shell_files(src)
acts = []
for rel in rels:
    s, d = os.path.join(src, rel), os.path.join(dst, rel)
    if not os.path.isfile(s):
        continue
    same = (os.path.isfile(d) and os.path.getsize(d) == os.path.getsize(s)
            and open(d, "rb").read() == open(s, "rb").read())
    acts.append([rel, "unchanged" if same else ("overlay" if write else "would overlay")])
    if write and not same:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
# 批37 双入口更名：目标里已不存在的壳层件（如旧 bin/sms-shell{,.cmd,.py}）随覆盖安装清除，
# 否则更名后混合体仍留旧入口（core 侧 bin 不被 git 跟踪，手动 cp 旹留）。
_srcset = set(p.replace("/", os.sep) for p in rels)
stale = []
for dp, dn, fn in os.walk(dst):
    dn[:] = [d for d in dn if d not in {".git", "__pycache__", ".pytest_cache", "tmp", ".kilo", "node_modules"}]
    rel_d = os.path.relpath(dp, dst).replace("\\", "/")
    for x in fn:
        r2 = os.path.relpath(os.path.join(dp, x), dst)
        rl = r2.replace(os.sep, "/").replace("\\", "/")  # 批38：Windows 反斜杠归一（否则 tests\\x.py 永不命中）
        if r2.replace("/", os.sep) in _srcset:
            continue
        top = rl.split("/")[0] if rel_d == "." else rel_d.split("/")[0]
        if (top == "bin" or top in ("sms.py", "sms", "sms.cmd")
                or re.match(r"^(skill/scripts/)?shell[^/]*\.(py|ps1)$", rl)  # 批38：stale 侧原 \\.（两反斜杠）永不命中，归一为 \.
                or re.match(r"^tests/test_shell_qt[^/]*\.py$", rl)  # 批38：图形壳传真机镜像回归随壳层件同族进出
                or rl == "skill/scripts/web_page.html"):
            stale.append(r2)
for rel in stale:
    if write:
        try:
            os.remove(os.path.join(dst, rel)); acts.append([rel, "prune"])
        except Exception as e:
            acts.append([rel, "prune-fail " + str(e)[:60]])
    else:
        acts.append([rel, "would prune"])
print(json.dumps({"src": src, "dst": dst, "write": write, "files": len(rels), "pruned": len(stale),
                  "changed": sum(1 for a in acts if a[1] != "unchanged"),
                  "detail": acts}, ensure_ascii=False, indent=1))

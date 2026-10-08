#!/usr/bin/env python3
"""install_overlay.py — SMS-shell → SMS-core 覆盖安装（批34 双仓口径的落地件）：
把本仓壳层文件（skill/scripts/shell_*.py＋shell.py＋web_page.html＋bin/*＋根入口三件）
复制进 SMS-core 工作区（core .gitignore 隔离，不追踪），＝运行时混合体。
默认预览，--write 才落盘；--src/--dst 可改路径。"""
import os, sys, json, shutil, re

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.environ.get("SMS_CORE") or r"C:\UserSpace\EthanYan\Developin\SMS-core"
args = sys.argv[1:]
write = "--write" in args
def _opt(name, dft):
    for a in args:
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return dft
src = _opt("--src", HERE); dst = _opt("--dst", CORE)
def shell_files(base):
    out = []
    for dp, dn, fn in os.walk(base):
        rel = os.path.relpath(dp, base).replace("\\", "/")
        top = rel.split("/")[0] if rel != "." else ""
        if top in {".git", "__pycache__", ".pytest_cache", "tmp", ".kilo", "node_modules"}:
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in {".git", "__pycache__", ".pytest_cache", "tmp", ".kilo", "node_modules"}]
        for f in fn:
            p = (rel + "/" + f).lstrip("./")
            if p.startswith("bin/") or p in ("sms.py", "sms", "sms.cmd") or re.match(r"skill/scripts/shell_[^/]*\.(py|ps1)$", p) or p in ("skill/scripts/shell.py", "skill/scripts/web_page.html"):
                out.append(p)
    return out
rels = shell_files(src)
acts = []
for rel in rels:
    s, d = os.path.join(src, rel), os.path.join(dst, rel)
    same = os.path.isfile(d) and os.path.getsize(d) == os.path.getsize(s) and open(d, "rb").read() == open(s, "rb").read()
    acts.append([rel, "unchanged" if same else ("overlay" if write else "would overlay")])
    if write and not same:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
print(json.dumps({"src": src, "dst": dst, "write": write, "files": len(rels),
                  "changed": sum(1 for a in acts if a[1] not in ("unchanged",))}, ensure_ascii=False, indent=1))

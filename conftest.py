"""pytest root: make the package importable without installation.

Also auto-locates the SMS core scripts dir (SMS_CORE_SCRIPTS) so shell-side
tests that audit core modules (no_window_audit etc.) run on this machine
without exporting paths by hand: the dev checkout next to this repo is the
SMS-core folder.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _find_core_scripts() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in [os.environ.get("SMS_CORE_SCRIPTS"), os.environ.get("SMS_CORE"),
                 os.path.join(os.path.dirname(here), "SMS-core", "skill", "scripts"),
                 os.path.join(os.path.dirname(here), "sms-core", "skill", "scripts")]:
        if cand and os.path.isfile(os.path.join(cand, "no_window_audit.py")):
            return cand
    pat = os.path.join(os.path.dirname(here), "SMS-core*", "skill", "scripts")
    hits = glob.glob(pat)
    return os.path.dirname(hits[0]) if hits else ""


_core = _find_core_scripts()
if _core:
    sys.path.insert(0, _core)
    os.environ["SMS_CORE_SCRIPTS"] = _core
    if os.environ.get("SMS_CORE") not in ("", None):
        pass
    else:
        core_root = os.path.dirname(os.path.dirname(_core))
        os.environ["SMS_CORE"] = core_root
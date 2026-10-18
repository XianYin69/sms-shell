@echo off
rem sms-shell-gui launcher (GUI entry, Windows, ASCII only): python sms-shell-gui.py preferred (PyQt6 shell_qt.py + shell_qt_fax.py fax-console mirror, batch41 chassis = feeder on top + left/right QSplitter below (paper-roll A on the left, preview D with self-drawn line numbers over terminal E on the right, both panes split/fold, right splitter holds three resident non-collapsible cells (childrenCollapsible=False) C e-ink (Ctrl+I only focuses and never hides) over D preview over E terminal, control panel/drawer on demand via Ctrl+M, bottom status strip removed, hints relocated to the e-ink mini-label eink_stat plus the six-state paper-feed queue idle/feed/print/advance/tear/jam; batch45 preview lookup on a bare name walks de-duplicated candidate dirs (workspace root -> SMS_TMP -> cwd; shell_qt.py _pv_candidates L961 / previewOpen L972, all-miss = explicit error + built-in fallback, never silent); batch46 lamp parity drives the QQ lamp in-process via web_shell /api/qq (pollQQ L1392 / pollAll L1417), gate led_driven_n = led_built_n = led_lamps = 7 (gate L1851); Ctrl+V cycles five views roll/feeder/e-ink/preview/terminal; zero top bar kept from batch40: native menu bar and brand strip removed in favour of the Ctrl+K command palette and the right-click body menu), no token gate on GUI (preview data in-process via /api/files /api/file /api/detail, terminal = QProcess on the same shell_core.handle route, reaped on closeEvent so no orphan); batch40 drops the native menuBar/brand strip and keeps the legacy shortcuts at QAction level; batch39 three views = paper-cutter CUT blade / CRT green-on-black feeder / E-INK 3-section panel, no new port and no bare child process; PySide6 shell_gui.py fallback inside, no Qt -> sms-shell-tui); first arg api -> locate.py; python missing -> ps1 native DOS TUI via sms_shell.ps1 (GUI needs python, so console shell is the only python-less path). Deploy = copy all bin files to target path.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if /I "%~1"=="api" goto py
where /q python.exe
if errorlevel 1 goto ps1
python -B "%~dp0sms-shell-gui.py" %*
exit /b %ERRORLEVEL%
:ps1
where /q powershell.exe
if errorlevel 1 goto py
if "%~1"=="" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0sms_shell.ps1"
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0sms_shell.ps1' @args" %*
)
exit /b %ERRORLEVEL%
:py
python -B "%~dp0locate.py" %*

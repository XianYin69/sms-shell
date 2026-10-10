@echo off
rem sms-shell-gui launcher (GUI entry, Windows, ASCII only): python sms-shell-gui.py preferred (PyQt6 shell_qt.py + shell_qt_fax.py fax-console mirror, zero-topbar three-zone chassis (paper-roll / crt feeder / e-ink permanent; control panel and drawer on demand via Ctrl+M; native menu bar and brand strip removed in favour of the Ctrl+K command palette and the right-click body menu), no token gate on GUI; batch40 drops the native menuBar/brand strip and keeps the legacy shortcuts at QAction level; batch39 three views = paper-cutter CUT blade / CRT green-on-black feeder / E-INK 3-section panel, all in-process, no new port or process; PySide6 shell_gui.py fallback inside, no Qt -> sms-shell-tui); first arg api -> locate.py; python missing -> ps1 native DOS TUI via sms_shell.ps1 (GUI needs python, so console shell is the only python-less path). Deploy = copy all bin files to target path.
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

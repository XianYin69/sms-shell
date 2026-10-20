@echo off
REM ============================================================
REM  SMS dev-test environment launcher (WSL2 Ubuntu-24.04)
REM  Created by skill sms-dev-test-pack - do not edit by hand
REM  Env: /root/sms/{home,suite,repos}, branch tech-preview,
REM       venv py3.12, pip tuna mirror, sshd:22, wayland (no X11, no Docker)
REM ============================================================
setlocal
set "SMS_DISTRO=Ubuntu-24.04"

wsl -l -v 2>NUL | findstr /I /R "\<%SMS_DISTRO%\>" >NUL
if errorlevel 1 (
  echo [FAIL] WSL distro %SMS_DISTRO% not found. Install WSL2 Ubuntu-24.04 first.
  pause
  exit /b 1
)

echo Entering SMS dev-test env: wsl -d %SMS_DISTRO%
wsl -d %SMS_DISTRO% --cd /root -- bash -lc "if [ -f /root/sms/sms-env.sh ]; then . /root/sms/sms-env.sh; echo '[OK] sms-env.sh loaded'; else echo '[WARN] /root/sms/sms-env.sh missing - plain shell'; fi; echo 'branch:' $(git -C /root/sms/suite rev-parse --abbrev-ref HEAD 2>/dev/null); echo 'repos:' $(ls /root/sms/repos 2>/dev/null | tr '\n' ' '); exec bash"
echo.
echo [EXIT] SMS dev-test env closed.
pause
endlocal
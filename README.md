# sms-shell — SMS 界面壳

skill_manage_system 的壳侧：30 个 `shell_*.py` ＋ `bin/` 启动器（sms-shell / .cmd / .ps1 / locate.py）＋ 网页壳前端 `web_page.html`。
壳只依赖核心（shell→core 单向 50 条边），核心不反向依赖壳。

覆盖 TUI（Textual 与原生 DOS 两态）·GUI·控制台·网页壳·接续/生命周期/顶栏/抽屉等；启动器经
`locate.py` 就近定位技能目录，无硬编码路径。

- 依赖：sms-core（必须先装）
- 边界契约：见 `SEPARATION.md`
- 安装：把 `scripts/*` 与 `bin/*` 覆盖到 `<SMS_HOME>/skill/scripts` 与 `<SMS_HOME>/bin`（合体发行＝skill_manage_system）

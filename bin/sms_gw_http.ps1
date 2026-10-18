# sms_gw_http.ps1 — 网关 HTTP 层（零 python·统一 DSM 直连 smsocket）：DSM 信封 POST /v1/dsm/chat（Content-Type application/dsm+json）；
# 入参 $body 为 OpenAI 形状（model 忽略·别名取 Cfg 'llm_gateway.model'），消息按 ROLE 表 position 化（[rid,text]），
# x.sms.inline_schema 内联 system（零次 schema 登记往返·require_registered_schema=false 时服务端直接物化），
# out 缺省 delta → application/x-ndjson 逐帧信封（reason.summary 思考回放 / 按序拼接 answer / 收口帧只认 stop），llm_gateway.dsm.out='json' 时回整包响应信封。DSM 是唯一出站通道：404/415/连接失败＝smsocket 未就绪或 DSM 未启用，
# 显式抛错——绝不静默回退原生 OpenAI /chat/completions 或 agent CLI（统一 DSM 直连 smsocket 改造）。
# 依赖 sms_state.ps1 的 Cfg/CfgGet，由 sms_shell.ps1 统一点源加载
function Get-GwBase {
  [string](Cfg 'llm_gateway').base_url
}
function Get-GwKey {
  $c = Cfg 'llm_gateway'
  $key = [string]$c.api_key; if ($c.api_key_env) { $ev = [string](Get-Item ('env:' + $c.api_key_env) -ErrorAction SilentlyContinue).Value; if ($ev) { $key = $ev } }  # 空 env 不覆盖配置密钥（批34 防 401）
  $key
}
function Test-SmSocket {
  try {
    $r = [Net.HttpWebRequest]::Create((Get-GwBase).TrimEnd('/') + '/healthz'); $r.Method = 'GET'; $r.Timeout = 4000; $r.ReadWriteTimeout = 4000
    $null = $r.GetResponse(); return $true
  } catch { return $false }
}
function New-GwEnv($body, $outMode) {
  $c = Cfg 'llm_gateway'
  $ROLE = @{ system = 0; user = 1; assistant = 2; tool = 3 }
  $d = @(); $sys = ''
  foreach ($m in @($body.messages)) {
    $r = [string]$m.role; $cid = 1
    if ($ROLE.ContainsKey($r)) { $cid = $ROLE[$r] }
    $content = $m.content
    if ($content -is [System.Collections.IList] -and -not ($content -is [string])) {
      # 多模态分段 content（text + image_url）：text 段拼原文，image 段占位（DSM d.text 只承载字符串）
      $parts = @()
      foreach ($seg in @($content)) {
        if ($seg.PSObject.Properties.Name -contains 'text' -and $seg.text) { $parts += [string]$seg.text }
        elseif ($seg.PSObject.Properties.Name -contains 'image_url') { $parts += '〔附图 ' + [string]$seg.image_url.url + '〕' }
      }
      $content = $parts -join "`n"
    }
    $text = [string]$content
    if ($r -eq 'system' -and -not $sys) { $sys = $text } else { $d += ,@($cid, $text) }
  }
  $env = @{
    v = 1
    sch = 'sha1:000000000000'
    d = $d
    out = $outMode
    x = @{
      'sms.model' = [string]$c.model
      'sms.inline_schema' = @{ system = $sys; tools = @() }
      'mem_off' = $true
    }
  }
  $mt = [string]$body.max_tokens
  if ($mt) { $env.budget = @{ max_out = [int]$mt } }
  if ($null -ne $body.temperature) { $env.x['temperature'] = $body.temperature }
  if ($null -ne $body.top_p) { $env.x['top_p'] = $body.top_p }
  if ($null -ne $body.reasoning_effort) { $env.budget = $env.budget + @{ reason = [string]$body.reasoning_effort } }
  $env
}
function Stream-Gateway($body, $sink) {
  # 统一 DSM 直连：smsocket 未监听 → 显式抛错（调用方 catch 后报错，不回退 agent CLI）
  if (-not (Test-SmSocket)) { throw 'smsocket 不可达（先 :smsocket 启动 smsocket 再试）——统一 DSM 直连模式不回退原生通道' }
  # 默认 delta（逐帧 ndjson·等价旧 SSE 逐字流式体验）；llm_gateway.dsm.out 显式配 'json' 才走整包
  $outMode = 'delta'
  try { if ([string](CfgGet 'llm_gateway.dsm.out' 'delta') -eq 'json') { $outMode = 'json' } } catch {}
  $env = New-GwEnv $body $outMode
  $tm = 120; try { $tm = [int](CfgGet 'llm_gateway.timeout' 120) } catch {}; if ($tm -le 0) { $tm = 120 }
  $req = [Net.HttpWebRequest]::Create((Get-GwBase).TrimEnd('/') + '/v1/dsm/chat')
  $req.Method = 'POST'; $req.ContentType = 'application/dsm+json'; $req.Timeout = 1000 * $tm; $req.ReadWriteTimeout = 1000 * $tm
  $req.ServicePoint.Expect100Continue = $false
  $key = Get-GwKey
  if ($key) { $req.Headers.Add('Authorization', 'Bearer ' + $key) }
  $b = [Text.Encoding]::UTF8.GetBytes(($env | ConvertTo-Json -Depth 12 -Compress)); $req.ContentLength = $b.Length
  $qs = $req.GetRequestStream(); $qs.Write($b, 0, $b.Length); $qs.Close()
  try { $resp = $req.GetResponse() } catch [System.Net.WebException] {
    if ($_.Exception.Response) {
      $code = [int]$_.Exception.Response.StatusCode
      $dr = ''; try { $dr = (New-Object IO.StreamReader -ArgumentList $_.Exception.Response.GetResponseStream(), ([Text.Encoding]::UTF8)).ReadToString() } catch {}
      throw ('DSM /v1/dsm/chat 回 ' + $code + '（smsocket 未就绪/DSM 未启用/信封被拒）' + $(if ($dr) { '：' + $dr.Substring(0, [Math]::Min(200, $dr.Length)) } else { '' }))
    }
    throw ('DSM /v1/dsm/chat 连接失败：' + $_.Exception.Message)
  }
  $full = ''
  $ct = [string]$resp.ContentType
  $rd = New-Object IO.StreamReader -ArgumentList $resp.GetResponseStream(), ([Text.Encoding]::UTF8)
  if ($outMode -eq 'delta' -and $ct -like '*x-ndjson*') {
    # out=delta：逐行 ndjson 信封；帧 {v,seq,answer,stop} 可带 reason.summary；收口帧只带 stop/usage（正文已逐帧吐过，末帧绝不重复拼接）
    while ($null -ne ($ln = $rd.ReadLine())) {
      $ln = $ln.Trim(); if (-not $ln) { continue }
      $j = $null; try { $j = $ln | ConvertFrom-Json } catch { continue }
      if ($null -eq $j -or $j.PSObject.Properties.Name -notcontains 'seq') { continue }
      if ($j.reason -and $j.reason.summary) { & $sink ('◌ ' + [string]$j.reason.summary) }
      if ($j.answer -is [System.String] -and $j.answer) { $full += [string]$j.answer; & $sink ([string]$j.answer) }
      if ($null -ne $j.stop -and $j.stop -ne '') { break }
    }
  } else {
    # out=json：单条响应信封整包（answer 全文 + reason.summary 思考回放）
    $t = $rd.ReadToEnd(); $j = $null; try { $j = $t | ConvertFrom-Json } catch {}
    if ($j -and $j.reason -and $j.reason.summary) { & $sink ('◌ ' + [string]$j.reason.summary) }
    if ($j -and $j.answer -is [System.String] -and $j.answer) { $full = [string]$j.answer; & $sink $full }
  }
  $rd.Close(); $resp.Close()
  if ($full) { Write-Host '' }
  $full
}

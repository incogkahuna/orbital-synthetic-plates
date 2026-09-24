# Minimal Unreal MCP caller (for sessions where the `unreal` MCP tools aren't loaded).
# usage: . .\ue_mcp.ps1 ; UeMcp 'list_toolsets' @{} ; UeTool 'EditorToolset' 'some_tool' @{arg=1}
$script:UeUrl = 'http://127.0.0.1:8000/mcp'
function UeMcp([string]$method, $params) {
  $h = @{ Accept = 'application/json, text/event-stream' }
  if (-not $script:UeSid) {
    $init = Invoke-WebRequest $script:UeUrl -Method Post -ContentType 'application/json' -Headers $h -UseBasicParsing `
      -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"ps","version":"0"}}}'
    $script:UeSid = $init.Headers['Mcp-Session-Id']
  }
  if ($script:UeSid) { $h['Mcp-Session-Id'] = $script:UeSid }
  $body = @{ jsonrpc = '2.0'; id = [int](Get-Random); method = $method; params = $params } | ConvertTo-Json -Depth 20 -Compress
  $r = Invoke-RestMethod $script:UeUrl -Method Post -ContentType 'application/json' -Headers $h -Body $body
  if ($r.error) { throw ($r.error | ConvertTo-Json -Depth 5) }
  $r.result
}
function UeTool([string]$toolset, [string]$tool, $arguments) {
  $a = @{ tool_name = $tool; arguments = $arguments }
  if ($toolset) { $a.toolset_name = $toolset }
  $res = UeMcp 'tools/call' @{ name = 'call_tool'; arguments = $a }
  ($res.content | ForEach-Object { $_.text }) -join "`n"
}

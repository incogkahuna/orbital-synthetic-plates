# Overnight 2026-09-25: van-fixed v15 depth -> Wan (anchor, no feed-forward: cannot collapse) -> LTX-2.3 + 3DREAL-light
# (coherent photoreal re-render, removes the Wan seams) -> Magnific Topaz 2K for the first camera.
param([string[]]$Cams = @('C5','C7'), [int]$Seconds = 60, [string]$Geo = 'v15', [string]$Era = '1980s', [switch]$SkipWan)
$Cams = @($Cams | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$Root = Split-Path $PSScriptRoot -Parent; $vpy = 'C:\ComfyUI\.venv\Scripts\python.exe'
function log($m) { Write-Output "$(Get-Date -f 'MM-dd HH:mm:ss') $m" }
function WaitComfy { do { Start-Sleep 15; try { $q = Invoke-RestMethod http://127.0.0.1:8188/queue } catch { $q = $null } } while (-not $q -or $q.queue_running.Count -gt 0 -or $q.queue_pending.Count -gt 0) }
$frames = [int]($Seconds * 24) + 1
$first = $true
foreach ($c in $Cams) {
  $wan = "$Root\deliverables\${Era}_${c}_cesium_${Geo}_${Seconds}s_nokeep.mp4"
  if (-not $SkipWan -or -not (Test-Path $wan)) {
    WaitComfy
    $env:PLATES_BF16 = '1'; $env:PLATES_ANCHOR = '1'; $env:PLATES_NOKEEP = '1'; $env:PLATES_RESET_EVERY = ''
    $env:PLATES_COLORMATCH = ''; $env:PLATES_SKYLOCK = ''; $env:PLATES_VARIANT = '_nokeep'
    log "wan start $c ${Seconds}s $Geo"
    & $vpy "$Root\scripts\run_era.py" $Era $Seconds 49 8 $c 0 $Geo 2>&1 | Select-Object -Last 2 | ForEach-Object { log "  $_" }
  }
  if (-not (Test-Path $wan)) { log "NO WAN OUTPUT for $c - skipping"; continue }
  WaitComfy
  log "3dreal start $c $frames frames"
  $out = & $vpy "$Root\scripts\ltx_3dreal.py" $wan --lora light --frames $frames --context 121 --tag "${Seconds}s" 2>&1
  $out | Select-Object -Last 3 | ForEach-Object { log "  $_" }
  $done = ($out | Select-String 'DONE in' | Select-Object -Last 1)
  if (-not $done) {
    log "3dreal full-length failed for $c - falling back to two halves"
    $half = [int](($frames - 1) / 2 / 8) * 8 + 1
    foreach ($st in 0, ($half - 1)) {
      WaitComfy
      & $vpy "$Root\scripts\ltx_3dreal.py" $wan --lora light --frames $half --start $st --context 121 --tag "half$st" 2>&1 | Select-Object -Last 2 | ForEach-Object { log "  $_" }
    }
    continue
  }
  $mp4 = ($done.Line -split '-> ')[-1].Trim()
  if ($first -and (Test-Path $mp4)) {
    $first = $false
    log "magnific topaz 2k $c"
    & $vpy "$Root\scripts\magnific_upscale.py" $mp4 "$Root\deliverables\magnific\2026-09-26_overnight" topaz --resolution 2k --model starlight_precise_2_5 2>&1 | Select-Object -Last 2 | ForEach-Object { log "  $_" }
  }
}
log "OVERNIGHT DONE"

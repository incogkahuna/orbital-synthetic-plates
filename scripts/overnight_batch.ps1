# Overnight batch: one Unreal depth render (dressed world, real cars, era, N seconds, several cameras), then a
# windowed Wan run per camera. Never runs Unreal and Comfy at the same time (waits for Comfy to go idle first).
# usage: overnight_batch.ps1 -Tag v14 -Era 1980s -Seconds 60 -Cams C5,C1,C3 [-SkipDepth] [-Variant _v2stab]
param([string]$Tag = 'v14', [string]$Era = '1980s', [int]$Seconds = 60, [string[]]$Cams = @('C5','C1','C3'),
      [switch]$SkipDepth, [switch]$DepthOnly, [string]$Variant = '_v2stab', [string]$SkyLock = '2')
$Cams = @($Cams | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$Root = Split-Path $PSScriptRoot -Parent; $Sv = "$Root\unreal\Saved"; $vpy = 'C:\ComfyUI\.venv\Scripts\python.exe'
function log($m) { Write-Output "$(Get-Date -f 'MM-dd HH:mm:ss') $m" }
function WaitComfy { do { Start-Sleep 15; try { $q = Invoke-RestMethod http://127.0.0.1:8188/queue } catch { $q = $null } } while (-not $q -or $q.queue_running.Count -gt 0 -or $q.queue_pending.Count -gt 0) }

if (-not $SkipDepth) {
  WaitComfy
  Invoke-RestMethod http://127.0.0.1:8188/free -Method Post -ContentType 'application/json' -Body '{"unload_models":true,"free_memory":true}' | Out-Null
  @{ era = $Era; dress = $true; duration_s = $Seconds + 2; jobs = @($Cams | ForEach-Object { "SEQ_PlateRing_$_" }) } |
    ConvertTo-Json -Compress | Set-Content -Encoding ascii -Path "$Sv\run_options.json"
  Remove-Item "$Sv\PlateRenders\Cesium" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item "$Sv\cesium_c1_status.txt" -ErrorAction SilentlyContinue
  New-Item -ItemType File -Force "$Sv\run_cesium_c1.flag" | Out-Null
  log "unreal depth: $Era ${Seconds}s cams $($Cams -join ',')"
  Start-Process "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" -ArgumentList "`"$Root\unreal\OrbitalPlates.uproject`" /Game/OrbitalPlates/Cesium/PlatesCesium"
  $st = "$Sv\cesium_c1_status.txt"; $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 120) {
    Start-Sleep 20
    if ((Test-Path $st) -and (Select-String -Path $st -Pattern 'render finished|ERROR' -Quiet)) { Start-Sleep 25; break }
    if (((Get-Date) - $t0).TotalMinutes -gt 3 -and -not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { log "editor gone early"; break }
  }
  Get-Process UnrealEditor, CrashReportClientEditor -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Get-Content $st -ErrorAction SilentlyContinue | Select-String 'render finished|ERROR|passing lane|wires' | ForEach-Object { log "status: $_" }
  Select-String -Path "$Sv\Logs\OrbitalPlates.log" -Pattern 'car library|traffic:|passing lane' -ErrorAction SilentlyContinue | Select-Object -Last 3 | ForEach-Object { log "ue: $($_.Line)" }
  $procs = foreach ($c in $Cams) { Start-Process $vpy -ArgumentList "`"$Root\scripts\exr_to_png.py`" `"$Sv\PlateRenders\Cesium\SEQ_PlateRing_$c`" `"$Root\renders\Cesium_${c}_${Tag}_png`" 832 480" -NoNewWindow -PassThru }
  $procs | Wait-Process
  foreach ($c in $Cams) {
    $n = (Get-ChildItem "$Root\renders\Cesium_${c}_${Tag}_png" -Filter 'depth_*.png' -ErrorAction SilentlyContinue).Count
    log "depth $c : $n frames"
    ffmpeg -y -loglevel error -framerate 24000/1001 -i "$Root\renders\Cesium_${c}_${Tag}_png\depth_%06d.png" -c:v libx264 -pix_fmt yuv420p -crf 14 "$Root\renders\depth_${c}_${Tag}.mp4"
  }
}

if ($DepthOnly) { log 'DEPTH ONLY DONE'; exit 0 }
$env:PLATES_BF16 = '1'; $env:PLATES_SKYLOCK = $SkyLock; $env:PLATES_COLORMATCH = '1'; $env:PLATES_VARIANT = $Variant
foreach ($c in $Cams) {
  $need = [int]($Seconds * 24) + 1
  $n = (Get-ChildItem "$Root\renders\Cesium_${c}_${Tag}_png" -Filter 'depth_*.png' -ErrorAction SilentlyContinue).Count
  if ($n -lt $need) { log "SKIP $c : only $n depth frames (need $need)"; continue }
  WaitComfy
  log "plate start: $Era $c ${Seconds}s $Tag skylock=$SkyLock colormatch=1"
  & $vpy "$Root\scripts\run_era.py" $Era $Seconds 49 8 $c 0 $Tag 2>&1 | Select-Object -Last 2 | ForEach-Object { log "  $_" }
  log "plate end: $c"
}
log "BATCH DONE"

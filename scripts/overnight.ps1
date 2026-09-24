# Overnight long-form plates: runs run_era.py jobs one after another; a failed job is logged and skipped.
# usage: powershell -ExecutionPolicy Bypass -File scripts\overnight.ps1 [-Seconds 20] [-Geo v8] [-Bf16]
# Same length for every camera and era (Danny: one length across the board). Each job: era, camera, geometry tag
# (depth folder renders\Cesium_<cam>_<geo>_png). Rear first, then the side profiles.
param([int]$Seconds = 20, [string]$Geo = 'v8', [switch]$Bf16)
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
if ($Bf16) { $env:PLATES_BF16 = '1' }
$R = Split-Path $PSScriptRoot -Parent
$vpy = if ($env:COMFY_PYTHON) { $env:COMFY_PYTHON } else { 'C:\ComfyUI\.venv\Scripts\python.exe' }
$log = "$R\renders\overnight_$(Get-Date -f MMdd_HHmm).log"
$jobs = foreach ($cam in 'C5', 'C3', 'C7') { foreach ($era in '1955', '1980s') { ,@($era, $Seconds, $cam, $Geo) } }
foreach ($j in $jobs) {
  $t0 = Get-Date
  "$(Get-Date -f HH:mm:ss) START $($j -join ' ')" | Tee-Object -FilePath $log -Append
  & $vpy "$R\scripts\run_era.py" $j[0] $j[1] 49 8 $j[2] 0 $j[3] 2>&1 | Select-Object -Last 3 | Tee-Object -FilePath $log -Append
  "$(Get-Date -f HH:mm:ss) END   $($j -join ' ') exit=$LASTEXITCODE in $([int]((Get-Date) - $t0).TotalMinutes) min" | Tee-Object -FilePath $log -Append
}
"$(Get-Date -f HH:mm:ss) ALL DONE" | Tee-Object -FilePath $log -Append

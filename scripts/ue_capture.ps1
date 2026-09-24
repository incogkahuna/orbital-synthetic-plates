# usage: ue_capture.ps1 <x> <y> <z> <pitch> <yaw> <outName> [waitSec]
# Moves the editor viewport camera (so Cesium streams tiles for that view), waits, captures, saves an 800px copy.
param([double]$x,[double]$y,[double]$z,[double]$pitch,[double]$yaw,[string]$name,[int]$wait=25)
. "$PSScriptRoot\ue_mcp.ps1"
$t = @{ location=@{x=$x;y=$y;z=$z}; rotation=@{pitch=$pitch;yaw=$yaw;roll=0}; scale=@{x=1;y=1;z=1} }
UeTool 'EditorToolset.EditorAppToolset' 'SetCameraTransform' @{transform=$t} | Out-Null
Start-Sleep $wait
$a = @{gridSpacing=0;gridExtent=0;gridHeight=0;maxLabelDistance=0;classFilter=@{refPath=''};maxLabels=0}
$j = (UeTool 'EditorToolset.EditorAppToolset' 'CaptureViewport' @{captureTransform=$t;annotations=$a;bShowUI=$false}) | ConvertFrom-Json
$dir = "$env:USERPROFILE\Documents\OrbitalPlates\renders\cesium"; New-Item -ItemType Directory -Force $dir | Out-Null
$full = "$dir\$name.png"; [IO.File]::WriteAllBytes($full, [Convert]::FromBase64String($j.returnValue.image.data))
Add-Type -AssemblyName System.Drawing
$i = [Drawing.Image]::FromFile($full); $b = New-Object Drawing.Bitmap $i, 800, ([int](800*$i.Height/$i.Width)); $i.Dispose()
$b.Save("$dir\${name}_small.png"); $b.Dispose(); "$dir\${name}_small.png"

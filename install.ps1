$ErrorActionPreference = "Stop"
$repo = "https://github.com/nadeemmhdm/cloud-os.git"
$dir = Join-Path $env:ProgramData "CloudOs"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
if (Test-Path $dir) { git -C $dir pull --ff-only } else { git clone $repo $dir }
py -m pip install --upgrade $dir
cloud-os setup
cloud-os install-service
Write-Host "Cloud Os installed. It will start automatically after Windows boots."

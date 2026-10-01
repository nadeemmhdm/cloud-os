$ErrorActionPreference = "Stop"
$Repo = "https://github.com/nadeemmhdm/cloud-os.git"
$Dir = Join-Path $env:ProgramData "CloudOs"

function Step($m) { Write-Host "[Cloud OS] $m" -ForegroundColor Cyan }
function Fail($code,$m,$fix="") {
  Write-Host "[ERROR $code] $m" -ForegroundColor Red
  if ($fix) { Write-Host "Fix: $fix" -ForegroundColor Yellow }
  exit 1
}
function Has($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

Step "Checking administrator permission"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Fail "I001" "Administrator permission is required." "Open PowerShell as Administrator and run the install command again." }

Step "Checking Internet access"
try { Invoke-WebRequest -UseBasicParsing -Uri "https://github.com" -Method Head -TimeoutSec 15 | Out-Null } catch { Fail "I002" "GitHub is not reachable." "Check Internet/DNS/proxy settings and retry." }

if (-not (Has "winget")) { Fail "I003" "Windows Package Manager (winget) is required for automatic prerequisite installation." "Install/update App Installer from Microsoft, then retry." }

if (-not (Has "git")) {
  Step "Git is missing; installing Git"
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  $env:Path += ";$env:ProgramFiles\Git\cmd"
  if (-not (Has "git")) { Fail "I004" "Git installation completed but git is not available in PATH." "Restart PowerShell and run the installer again." }
} else { Step "Git found" }

$Python = $null
foreach ($candidate in @("py","python")) {
  if (Has $candidate) {
    try {
      $v = & $candidate -c "import sys; print(int(sys.version_info >= (3,10)))" 2>$null
      if ($v -eq "1") { $Python = $candidate; break }
    } catch {}
  }
}
if (-not $Python) {
  Step "Python 3.10+ is missing; installing Python 3.12"
  winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
  if (Has "py") { $Python="py" } elseif (Has "python") { $Python="python" } else { Fail "I005" "Python was installed but is not visible in this terminal." "Restart PowerShell and run the installer again." }
} else { Step "Compatible Python found" }

Step "Checking pip"
& $Python -m ensurepip --upgrade | Out-Null
& $Python -m pip --version | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "I006" "pip is unavailable." "Repair the Python installation and retry." }

Step "Downloading Cloud OS"
if (Test-Path (Join-Path $Dir ".git")) {
  git -C $Dir fetch origin main
  git -C $Dir checkout main
  git -C $Dir reset --hard origin/main
} elseif (Test-Path $Dir) {
  Fail "I007" "$Dir exists but is not a Cloud OS Git checkout." "Rename/remove that directory and retry."
} else {
  git clone --depth 1 $Repo $Dir
}
if ($LASTEXITCODE -ne 0) { Fail "I008" "Cloud OS download failed." "Check GitHub access and retry." }

Step "Installing Cloud OS and Python dependencies"
& $Python -m pip install --upgrade $Dir
if ($LASTEXITCODE -ne 0) { Fail "I009" "Python package installation failed." "Run '$Python -m pip install --upgrade $Dir' to see package details." }

Step "Running first-time setup"
& $Python -m cloud_os.cli setup
if ($LASTEXITCODE -ne 0) { Fail "I010" "Cloud OS setup failed." "Run '$Python -m cloud_os.cli doctor'." }

Step "Configuring automatic startup for the current Windows account"
$PythonExe = & $Python -c "import sys; print(sys.executable)"
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "-m cloud_os.cli start"
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
Register-ScheduledTask -TaskName "CloudOs" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Start Cloud OS automatically" -Force | Out-Null
Start-ScheduledTask -TaskName "CloudOs"
Write-Host "[OK] Cloud OS startup task registered." -ForegroundColor Green

Step "Verifying installation"
& $Python -m cloud_os.cli doctor
if ($LASTEXITCODE -ne 0) { Fail "I011" "Cloud OS installed, but verification reported an error." "Run 'cloud-os doctor'." }

Write-Host ""
Write-Host "[SUCCESS] Cloud OS installation completed." -ForegroundColor Green
Write-Host "Commands: cloud-os start | cloud-os status | cloud-os doctor | cloud-os update-check | cloud-os update"

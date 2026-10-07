$ErrorActionPreference = "Stop"
$Repo = "https://github.com/nadeemmhdm/cloud-os.git"
$Dir = Join-Path $env:ProgramData "CloudOs"
function Step($m){Write-Host "[Cloud OS] $m" -ForegroundColor Cyan}; function Fail($c,$m,$f=""){Write-Host "[ERROR $c] $m" -ForegroundColor Red;if($f){Write-Host "Fix: $f" -ForegroundColor Yellow};exit 1}; function Has($n){return [bool](Get-Command $n -ErrorAction SilentlyContinue)}
Step "Checking administrator permission";$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);if(-not $admin){Fail "I001" "Administrator permission is required."}
if(-not(Has "winget")){Fail "I003" "Windows Package Manager is required."}
if(-not(Has "git")){winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements;$env:Path += ";$env:ProgramFiles\Git\cmd"}
$Python=$null;foreach($candidate in @("py","python")){if(Has $candidate){try{$v=& $candidate -c "import sys; print(int(sys.version_info >= (3,10)))" 2>$null;if($v -eq "1"){$Python=$candidate;break}}catch{}}};if(-not $Python){winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements;if(Has "py"){$Python="py"}elseif(Has "python"){$Python="python"}else{Fail "I005" "Python is not visible; restart PowerShell and retry."}}
& $Python -m ensurepip --upgrade|Out-Null
Step "Downloading Cloud OS";if(Test-Path(Join-Path $Dir ".git")){git -C $Dir fetch origin main;git -C $Dir checkout main;git -C $Dir reset --hard origin/main}elseif(Test-Path $Dir){Fail "I007" "$Dir is not a Cloud OS checkout."}else{git clone --depth 1 $Repo $Dir}
Step "Installing Cloud OS";& $Python -m pip install --upgrade $Dir;if($LASTEXITCODE -ne 0){Fail "I009" "Package installation failed."}
Step "Running setup";& $Python -m cloud_os.cli setup;if($LASTEXITCODE -ne 0){Fail "I010" "Setup failed."}
# AtStartup is used instead of AtLogOn so the cloud is online before desktop sign-in.
# S4U deliberately avoids storing the Windows account password. Cloud OS itself remains non-elevated.
Step "Configuring Windows boot autostart"
$PythonExe=& $Python -c "import sys; print(sys.executable)";$HomeDir=Join-Path $env:USERPROFILE ".cloud-os";$Runner=Join-Path $Dir "start-cloud-os.ps1"
$runnerText='$env:CLOUD_OS_HOME="'+$HomeDir+'"' + "`r`n& '"+$PythonExe+"' -m cloud_os.cli start`r`n"
Set-Content -Path $Runner -Value $runnerText -Encoding UTF8
$Action=New-ScheduledTaskAction -Execute "powershell.exe" -Argument ('-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$Runner+'"')
$Trigger=New-ScheduledTaskTrigger -AtStartup
$Principal=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType S4U -RunLevel Limited
$Settings=New-ScheduledTaskSettingsSet -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "CloudOs" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Cloud OS boot service - starts web server, SSH and configured Cloudflare connector" -Force|Out-Null
Start-ScheduledTask -TaskName "CloudOs";Write-Host "[OK] Cloud OS will start automatically at Windows boot." -ForegroundColor Green
Step "Verifying installation";& $Python -m cloud_os.cli doctor
Write-Host "[SUCCESS] Cloud OS installation completed." -ForegroundColor Green

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/nadeemmhdm/cloud-os.git"
$Dir = Join-Path $env:ProgramData "CloudOs"
function Step($m){Write-Host "[Cloud OS] $m" -ForegroundColor Cyan}; function Fail($c,$m,$f=""){Write-Host "[ERROR $c] $m" -ForegroundColor Red;if($f){Write-Host "Fix: $f" -ForegroundColor Yellow};exit 1}; function Has($n){return [bool](Get-Command $n -ErrorAction SilentlyContinue)}
function Grant-CloudOsSourceAccess($Path){
 if(-not(Test-Path $Path)){return}
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
 Step "Repairing Cloud OS source permissions for $identity"
 & icacls.exe $Path /grant "$($identity):(OI)(CI)M" /T /C /Q | Out-Null
 if($LASTEXITCODE -ne 0){
  # Legacy installs may have been created with an ACL/owner which even an elevated
  # administrator cannot edit directly. Take ownership first, then grant only the
  # installing account Modify access so future non-elevated background updates work.
  Step "Existing source ACL is locked; taking ownership of the Cloud OS checkout"
  & takeown.exe /F $Path /R /D Y | Out-Null
  if($LASTEXITCODE -ne 0){Fail "I008" "Could not take ownership of $Path." "Open PowerShell with Run as Administrator and rerun the installer."}
  & icacls.exe $Path /inheritance:e /T /C /Q | Out-Null
  & icacls.exe $Path /grant:r "$($identity):(OI)(CI)M" /T /C /Q | Out-Null
  if($LASTEXITCODE -ne 0){Fail "I008" "Could not grant the Cloud OS runtime account modify access to $Path after taking ownership." "Open PowerShell with Run as Administrator and rerun the installer."}
 }
 $probe=Join-Path $Path ".cloud-os-write-test-$PID"
 try{"ok" | Set-Content -LiteralPath $probe -Encoding ascii -Force;Remove-Item -LiteralPath $probe -Force}catch{Fail "I008" "Cloud OS source checkout is still not writable for $identity." "Open PowerShell with Run as Administrator and rerun the installer."}
}
Step "Checking administrator permission";$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);if(-not $admin){Fail "I001" "Administrator permission is required." "Close this window, open PowerShell with Run as Administrator, and run the installer again."}
if(-not(Has "winget")){Fail "I003" "Windows Package Manager is required."}
if(-not(Has "git")){winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements;$env:Path += ";$env:ProgramFiles\Git\cmd"}
# Resolve a real python.exe path. Do not store the py launcher in $Python because
# PowerShell invocation of a launcher plus module arguments is unreliable here.
$Python=$null
$Candidates=@(
 (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
 (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
 (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe")
)
foreach($candidate in $Candidates){if(Test-Path $candidate){try{$v=& $candidate -c "import sys; print(int(sys.version_info >= (3,10)))" 2>$null;if($v -eq "1"){$Python=$candidate;break}}catch{}}}
if(-not $Python -and (Has "python")){try{$resolved=& python -c "import sys; print(sys.executable)" 2>$null;if($resolved -and (Test-Path $resolved)){$Python=$resolved.Trim()}}catch{}}
if(-not $Python -and (Has "py")){try{$resolved=& py -3 -c "import sys; print(sys.executable)" 2>$null;if($resolved -and (Test-Path $resolved)){$Python=$resolved.Trim()}}catch{}}
if(-not $Python){winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements;$candidate=Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe";if(Test-Path $candidate){$Python=$candidate}else{Fail "I005" "Python executable is not visible; restart PowerShell and retry."}}
Step "Using Python: $Python"
# pip can leave stale temporary '~ip*' directories after an interrupted/self-update.
try{$site=& $Python -c "import site; print(site.getusersitepackages())" 2>$null;if($site -and (Test-Path $site)){Get-ChildItem $site -Force -ErrorAction SilentlyContinue | Where-Object {$_.Name -like '~ip*'} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue}}catch{}
& $Python -m ensurepip --upgrade|Out-Null
# ProgramData is not writable by a normal user by default. Cloud OS runs its scheduled
# task as the installing account, so that account must be able to update the checkout.
if(Test-Path $Dir){Grant-CloudOsSourceAccess $Dir}
# Remove only a stale Git index lock before changing refs. A live git process still owns
# its lock and git will fail safely instead of being forced through.
$indexLock=Join-Path $Dir ".git\index.lock";if(Test-Path $indexLock){$gitRunning=Get-Process git -ErrorAction SilentlyContinue;if(-not $gitRunning){Remove-Item $indexLock -Force -ErrorAction SilentlyContinue}}
Step "Downloading Cloud OS";if(Test-Path(Join-Path $Dir ".git")){git -C $Dir fetch --prune origin main;if($LASTEXITCODE -ne 0){Fail "I008" "Git fetch failed after permission repair." "Rerun this installer from an Administrator PowerShell."};git -C $Dir checkout main;if($LASTEXITCODE -ne 0){Fail "I008" "Git checkout failed after permission repair."};git -C $Dir reset --hard origin/main;if($LASTEXITCODE -ne 0){Fail "I008" "Git reset failed after permission repair."}}elseif(Test-Path $Dir){Fail "I007" "$Dir is not a Cloud OS checkout."}else{git clone --depth 1 $Repo $Dir;if($LASTEXITCODE -ne 0){Fail "I006" "Could not clone Cloud OS."}}
Grant-CloudOsSourceAccess $Dir
Step "Installing Cloud OS";& $Python -m pip install --upgrade --no-deps --disable-pip-version-check $Dir;if($LASTEXITCODE -ne 0){Fail "I009" "Package installation failed."}
Step "Running setup";& $Python -m cloud_os.cli setup;if($LASTEXITCODE -ne 0){Fail "I010" "Setup failed." "Run: `"$Python`" -m cloud_os.cli setup"}
Step "Configuring boot-time autostart";& $Python -m cloud_os.cli autostart;if($LASTEXITCODE -ne 0){Fail "I011" "Could not configure Windows boot autostart." "Run PowerShell as Administrator, then: `"$Python`" -m cloud_os.cli autostart"}
Step "Verifying installation";& $Python -m cloud_os.cli doctor;if($LASTEXITCODE -ne 0){Fail "I012" "Cloud OS diagnostics failed." "Run: `"$Python`" -m cloud_os.cli doctor"}
Write-Host "[SUCCESS] Cloud OS installation completed. Cloud OS and configured integrations start automatically at Windows boot." -ForegroundColor Green

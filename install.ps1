$ErrorActionPreference = "Stop"
$Repo = "https://github.com/nadeemmhdm/cloud-os.git"
$Dir = Join-Path $env:ProgramData "CloudOs"
function Step($m){Write-Host "[Cloud OS] $m" -ForegroundColor Cyan}; function Fail($c,$m,$f=""){Write-Host "[ERROR $c] $m" -ForegroundColor Red;if($f){Write-Host "Fix: $f" -ForegroundColor Yellow};exit 1}; function Has($n){return [bool](Get-Command $n -ErrorAction SilentlyContinue)}
Step "Checking administrator permission";$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);if(-not $admin){Fail "I001" "Administrator permission is required."}
if(-not(Has "winget")){Fail "I003" "Windows Package Manager is required."}
if(-not(Has "git")){winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements;$env:Path += ";$env:ProgramFiles\Git\cmd"}
$Python=$null;foreach($candidate in @("py","python")){if(Has $candidate){try{$v=& $candidate -c "import sys; print(int(sys.version_info >= (3,10)))" 2>$null;if($v -eq "1"){$Python=$candidate;break}}catch{}}};if(-not $Python){winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements;if(Has "py"){$Python="py"}elseif(Has "python"){$Python="python"}else{Fail "I005" "Python is not visible; restart PowerShell and retry."}}
# pip can leave stale temporary '~ip*' directories after an interrupted/self-update.
# They are harmless but cause repeated "Ignoring invalid distribution ~ip" warnings.
try{$site=& $Python -c "import site; print(site.getusersitepackages())" 2>$null;if($site -and (Test-Path $site)){Get-ChildItem $site -Force -ErrorAction SilentlyContinue | Where-Object {$_.Name -like '~ip*'} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue}}catch{}
& $Python -m ensurepip --upgrade|Out-Null
Step "Downloading Cloud OS";if(Test-Path(Join-Path $Dir ".git")){git -C $Dir fetch origin main;git -C $Dir checkout main;git -C $Dir reset --hard origin/main}elseif(Test-Path $Dir){Fail "I007" "$Dir is not a Cloud OS checkout."}else{git clone --depth 1 $Repo $Dir}
Step "Installing Cloud OS";& $Python -m pip install --upgrade $Dir;if($LASTEXITCODE -ne 0){Fail "I009" "Package installation failed."}
Step "Running setup";& $Python -m cloud_os.cli setup;if($LASTEXITCODE -ne 0){Fail "I010" "Setup failed."}
Step "Configuring boot-time autostart";& $Python -m cloud_os.cli autostart;if($LASTEXITCODE -ne 0){Fail "I011" "Could not configure Windows boot autostart." "Run PowerShell as Administrator, then: cloud-os autostart"}
Step "Verifying installation";& $Python -m cloud_os.cli doctor
Write-Host "[SUCCESS] Cloud OS installation completed. Cloud OS and configured integrations start automatically at Windows boot." -ForegroundColor Green

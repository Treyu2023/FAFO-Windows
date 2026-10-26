# Installs the FAFO Windows toolbox launcher only.
# Tools are added later from inside the launcher, after a confirmation.
#   irm https://raw.githubusercontent.com/Treyu2023/FAFO-Windows/main/Install.ps1 | iex

$ErrorActionPreference = 'Stop'
$dest = 'C:\_git\FAFO-Windows'
New-Item -ItemType Directory -Force -Path 'C:\_git' | Out-Null
$git = Get-Command git -ErrorAction SilentlyContinue
if ((Test-Path (Join-Path $dest '.git')) -and $git) {
    & $git.Source -C $dest pull --ff-only
} elseif (-not (Test-Path (Join-Path $dest 'launcher\Start Toolbox.bat'))) {
    if (-not $git) { throw 'Git is required to download FAFO Windows.' }
    & $git.Source clone 'https://github.com/Treyu2023/FAFO-Windows.git' $dest
}
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $desktop 'FAFO Toolbox.lnk'))
$link.TargetPath = Join-Path $dest 'launcher\Start Toolbox.bat'
$link.WorkingDirectory = Join-Path $dest 'launcher'
$link.Description = 'FAFO Toolbox. Add or remove Windows tools after a confirmation.'
$link.Save()
Write-Host "FAFO Toolbox is at $dest"
Write-Host "Desktop shortcut: FAFO Toolbox"

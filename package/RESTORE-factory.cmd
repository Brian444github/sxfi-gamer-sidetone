@echo off
setlocal
set "SXFI_UPDATER=%~dp0SXFI_GAMER_2.07.02_FACTORY.exe"
echo Creative SXFI GAMER EF0880 only. Enter RGB-button recovery before continuing.
echo Opening the updater does not start flashing. Read INSTALL-en.md or INSTALL-ru.md.
powershell.exe -NoProfile -NonInteractive -Command "try { $ErrorActionPreference = 'Stop'; $p = $env:SXFI_UPDATER; if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne '1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496') { throw 'SHA-256 mismatch. Stop and download the official repository release again.' }; Write-Host 'SHA-256 verified. In the updater, click Upgrade once and wait for success.'; Start-Process -FilePath $p -ArgumentList '/F' -WorkingDirectory (Split-Path -Path $p -Parent) -Wait } catch { Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
  echo The launcher could not verify or open the updater. No automatic retry was performed.
  pause
  exit /b 1
)
endlocal

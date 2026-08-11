@echo off
setlocal
cd /d "%~dp0\.."

set "ISCC="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC for /f "delims=" %%I in ('dir /b /s "%LOCALAPPDATA%\Microsoft\WinGet\Packages\JRSoftware.InnoSetup*_*\ISCC.exe" 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC for /f "delims=" %%I in ('dir /b /s "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" 2^>nul') do if not defined ISCC set "ISCC=%%I"

if not defined ISCC (
  echo Inno Setup nao encontrado.
  echo.
  echo O winget pode dizer que esta instalado, mas o ISCC.exe nao ficou em um caminho conhecido.
  echo.
  echo Teste no CMD:
  echo where ISCC.exe
  echo.
  echo Instale pelo PowerShell/CMD com:
  echo winget install --id JRSoftware.InnoSetup -e
  echo.
  echo Ou abra o Inno Setup uma vez pelo menu iniciar e tente novamente.
  echo.
  echo Depois execute este BAT novamente.
  pause
  exit /b 1
)

echo Inno Setup encontrado em:
echo "%ISCC%"
echo.

"%ISCC%" "instalador\Acervo-de-Imagens.iss"
if errorlevel 1 (
  echo.
  echo ERRO: falha ao gerar instalador.
  pause
  exit /b 1
)

echo.
echo Instalador gerado em:
echo %cd%\executavel\Instalador-Acervo-de-Imagens-v2.0.10.exe
echo.
pause

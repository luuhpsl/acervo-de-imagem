@echo off
setlocal

cd /d "%~dp0"

python -m PyInstaller --noconfirm --clean CatalogoAcervo.spec

echo.
echo EXE gerado em: dist\CatalogoAcervo.exe
pause

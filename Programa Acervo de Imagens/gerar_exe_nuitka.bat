@echo off
setlocal

cd /d "%~dp0"

echo ============================================================
echo Gerador do executavel - Acervo de Imagens
echo Build via Nuitka
echo ============================================================
echo.

set "PYTHONUTF8=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

if not exist ".env.local" (
    if exist ".env.local.example" (
        copy ".env.local.example" ".env.local" >nul
        echo Arquivo .env.local criado a partir do exemplo.
    )
)

echo Verificando Nuitka...
python -c "import nuitka" >nul 2>nul
if errorlevel 1 (
    echo Nuitka nao encontrado. Instalando dependencias de build...
    python -m pip install --upgrade nuitka ordered-set zstandard
    if errorlevel 1 (
        echo.
        echo ERRO: nao foi possivel instalar o Nuitka.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando build. Isso pode demorar alguns minutos...
echo.

python -m nuitka ^
    --standalone ^
    --remove-output ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico="Acervo.ico" ^
    --enable-plugin=tk-inter ^
    --include-package=flask ^
    --include-package=requests ^
    --include-package=openai ^
    --include-package=PIL ^
    --include-package=imagehash ^
    --include-package=openpyxl ^
    --include-data-dir="Icons - Programa=Icons - Programa" ^
    --include-data-dir="Font=Font" ^
    --include-data-file="Acervo.ico=acervo.ico" ^
    --include-data-file="catalogo_logic.py=catalogo_logic.py" ^
    --include-data-file="auth_server.py=auth_server.py" ^
    --include-data-file="env_config.py=env_config.py" ^
    --include-data-file="index.html=index.html" ^
    --include-data-file="firestore.rules=firestore.rules" ^
    --include-data-file="storage.rules=storage.rules" ^
    --include-data-file=".env.local=.env.local" ^
    --output-dir="executavel\nuitka" ^
    --output-filename="Acervo-de-Imagens.exe" ^
    "main.py"

if errorlevel 1 (
    echo.
    echo ERRO: o build pelo Nuitka falhou.
    pause
    exit /b 1
)

echo.
echo Build finalizado com sucesso.
echo Executavel gerado em:
echo %cd%\executavel\nuitka\main.dist\Acervo-de-Imagens.exe
echo.
pause

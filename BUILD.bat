@echo off
setlocal EnableDelayedExpansion
title WinPE Studio — BUILD
color 0B
cd /d "%~dp0"

echo ============================================================
echo   WinPE Studio — BUILD COMPLETO
echo   Gera: dist\WinPE_Studio\ (pronto para distribuir)
echo ============================================================
echo.

:: ── Verificar Admin ──────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Execute como Administrador!
    pause & exit /b 1
)

:: ── Verificar Python ─────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause & exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] %%V

:: ── Instalar/atualizar dependencias ──────────────────────────────────
echo.
echo [1/5] Instalando dependencias...
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet
echo [OK] Dependencias OK.

:: ── Limpar build anterior ─────────────────────────────────────────────
echo.
echo [2/5] Limpando build anterior...
if exist "dist\WinPE_Studio" rmdir /s /q "dist\WinPE_Studio"
if exist "build\WinPE_Studio" rmdir /s /q "build\WinPE_Studio"
echo [OK] Limpo.

:: ── Executar PyInstaller ──────────────────────────────────────────────
echo.
echo [3/5] Compilando com PyInstaller (pode demorar 3-5 min)...
python -m PyInstaller winpe_studio.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] PyInstaller falhou! Verifique os erros acima.
    pause & exit /b 1
)
echo [OK] Compilacao concluida.

:: ── Copiar arquivos extras para dist ─────────────────────────────────
echo.
echo [4/5] Copiando arquivos extras...

:: Scripts BAT de suporte
copy /y "GEMINI_HOST.bat"        "dist\WinPE_Studio\" >nul
copy /y "KIRO_SMB.bat"           "dist\WinPE_Studio\" >nul
copy /y "KIRO_CONECTOR.bat"      "dist\WinPE_Studio\" >nul
copy /y "KIRO_CONECTOR_MAIN.bat" "dist\WinPE_Studio\" >nul
copy /y "start.bat"              "dist\WinPE_Studio\" >nul

:: README
if exist "README.md" copy /y "README.md" "dist\WinPE_Studio\" >nul

:: Criar pasta de workspace vazia
if not exist "dist\WinPE_Studio\WinPE_Studio_Workspace" (
    mkdir "dist\WinPE_Studio\WinPE_Studio_Workspace"
)

:: Criar INICIAR.bat na raiz do pacote (duplo clique para abrir)
(
echo @echo off
echo cd /d "%%~dp0"
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     powershell -NoProfile -Command "Start-Process -FilePath '%%~f0' -Verb RunAs -WorkingDirectory '%%~dp0'"
echo     exit /b
echo ^)
echo start "" "%%~dp0WinPE_Studio.exe"
) > "dist\WinPE_Studio\INICIAR.bat"

echo [OK] Arquivos extras copiados.

:: ── Verificar resultado ───────────────────────────────────────────────
echo.
echo [5/5] Verificando pacote final...
echo.
echo Conteudo de dist\WinPE_Studio\:
dir "dist\WinPE_Studio\" /w
echo.

:: Tamanho total
for /f "tokens=3" %%S in ('dir "dist\WinPE_Studio\" /s /-c ^| findstr "arquivo(s)"') do (
    set "TOTAL_BYTES=%%S"
)

echo ============================================================
echo   BUILD CONCLUIDO!
echo.
echo   Pasta: %~dp0dist\WinPE_Studio\
echo   Exe  : dist\WinPE_Studio\WinPE_Studio.exe
echo.
echo   Para instalar em outro servidor:
echo   1. Copie a pasta dist\WinPE_Studio\ para o servidor
echo   2. Clique duas vezes em INICIAR.bat
echo   3. Aceite o UAC (precisa de Admin)
echo ============================================================
echo.
pause

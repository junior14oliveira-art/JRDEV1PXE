@echo off
:: =====================================================================
:: KIRO CONECTOR - Clique duas vezes aqui no Explorer++
:: Abre janela CMD que NUNCA fecha sozinha
:: =====================================================================

set "MYDIR=%~dp0"
set "MAIN=%MYDIR%KIRO_CONECTOR_MAIN.bat"

:: Fallback: tenta C:\
if not exist "%MAIN%" set "MAIN=C:\KIRO_CONECTOR_MAIN.bat"

:: Fallback: tenta X:\ (WinPE)
if not exist "%MAIN%" set "MAIN=X:\KIRO_CONECTOR_MAIN.bat"

if not exist "%MAIN%" (
    :: Ultimo recurso: abre CMD e mostra erro
    if exist "X:\Windows\System32\cmd.exe" (
        start "KIRO CONECTOR" "X:\Windows\System32\cmd.exe" /k "echo ERRO: KIRO_CONECTOR_MAIN.bat nao encontrado & echo Coloque os dois arquivos na mesma pasta & echo. & echo Pressione qualquer tecla... & pause"
    ) else (
        start "KIRO CONECTOR" cmd /k "echo ERRO: KIRO_CONECTOR_MAIN.bat nao encontrado & echo Coloque os dois arquivos na mesma pasta & echo. & pause"
    )
    exit /b 1
)

:: Abre janela CMD persistente com /k (nao fecha ao terminar)
if exist "X:\Windows\System32\cmd.exe" (
    start "KIRO CONECTOR" "X:\Windows\System32\cmd.exe" /k "%MAIN%"
) else (
    start "KIRO CONECTOR" cmd /k "%MAIN%"
)

@echo off
set "ADK_PE=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment"
set "OSCDIMG=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe"
set "DEST=E:\Manual_PE"

echo [1/4] Limpando e criando pastas...
if exist "%DEST%" rd /s /q "%DEST%"
mkdir "%DEST%\media\sources"

echo [2/4] Copiando arquivos do sistema (WinPE)...
xcopy /herky "%ADK_PE%\amd64\Media" "%DEST%\media\" >nul
copy "%ADK_PE%\amd64\en-us\winpe.wim" "%DEST%\media\sources\boot.wim" >nul

echo [3/4] Configurando boot...
:: Garantir que os arquivos de boot estao no lugar certo para o oscdimg
if not exist "%DEST%\media\boot\etfsboot.com" (
    echo [!] Aviso: Tentando localizar arquivos de boot alternativos...
)

echo [4/4] Gerando ISO Final...
"%OSCDIMG%" -m -o -u2 -udfver102 -bootdata:2#p0,e,b"%DEST%\media\boot\etfsboot.com"#pEF,e,b"%DEST%\media\efisys.bin" "%DEST%\media" E:\WinPE_Original_MANUAL.iso

if %ERRORLEVEL% EQU 0 (
    echo =========================================
    echo SUCESSO! ISO criada em E:\WinPE_Original_MANUAL.iso
    echo =========================================
) else (
    echo [!] Erro na geracao da ISO. Tentando modo simplificado...
    "%OSCDIMG%" -m -n "E:\Manual_PE\media" E:\WinPE_Original_MANUAL.iso
)

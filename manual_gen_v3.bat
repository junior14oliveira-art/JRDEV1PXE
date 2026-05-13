@echo off
set "ADK_BASE=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit"
set "ADK_PE=%ADK_BASE%\Windows Preinstallation Environment"
set "OSCDIMG_PATH=%ADK_BASE%\Deployment Tools\amd64\Oscdimg"
set "PATH=%PATH%;%OSCDIMG_PATH%"
set "DEST=E:\WinPE_Temp"

echo [1/3] Criando pastas...
if exist "%DEST%" rd /s /q "%DEST%"
mkdir "%DEST%\media\sources"

echo [2/3] Copiando arquivos base...
xcopy /herky "%ADK_PE%\amd64\Media" "%DEST%\media\" >nul
copy "%ADK_PE%\amd64\en-us\winpe.wim" "%DEST%\media\sources\boot.wim" >nul

echo [3/3] Gerando ISO...
call "%ADK_PE%\MakeWinPEMedia.cmd" /ISO "%DEST%" E:\WinPE_Original_Manual.iso

echo PRONTO! ISO criada em E:\WinPE_Original_Manual.iso

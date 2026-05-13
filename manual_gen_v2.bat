@echo off
set "ADK_PE=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment"
set "ADK_TOOLS=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools"
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

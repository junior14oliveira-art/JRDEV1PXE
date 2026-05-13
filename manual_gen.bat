@echo off
set "ADK_PATH=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment"
pushd "%ADK_PATH%"
echo [1/2] Criando arquivos base...
call copype amd64 E:\WinPE_Temp
echo [2/2] Gerando ISO...
call MakeWinPEMedia /ISO E:\WinPE_Temp E:\WinPE_Original_Manual.iso
popd
echo Concluido!

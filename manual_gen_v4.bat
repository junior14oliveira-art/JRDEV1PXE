@echo off
set "OSCDIMG=C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe"
echo Criando ISO final...
"%OSCDIMG%" -m -o -u2 -udfver102 -bootdata:2#p0,e,b"E:\WinPE_Temp\media\boot\etfsboot.com"#pEF,e,b"E:\WinPE_Temp\media\efisys.bin" "E:\WinPE_Temp\media" E:\WinPE_Original_Manual.iso
echo Concluido!

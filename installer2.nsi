; ============================================================
; WinPE Studio Pro — Instalador NSIS v2
; Gera: WinPE_Studio_Setup2.exe
; ============================================================

Unicode True

!define PRODUCT_NAME      "WinPE Studio Pro"
!define PRODUCT_VERSION   "2.1.0"
!define PRODUCT_PUBLISHER "JRDev"
!define PRODUCT_EXE       "WinPE_Studio.exe"
!define INSTALL_DIR       "$PROGRAMFILES64\WinPE Studio"
!define UNINSTALL_KEY     "Software\Microsoft\Windows\CurrentVersion\Uninstall\WinPEStudio"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "WinPE_Studio_Setup2.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
SetCompressorDictSize 64

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\win.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\win.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir WinPE Studio agora"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "PortugueseBR"

; ── Secao principal ───────────────────────────────────────
Section "WinPE Studio Pro" SecMain
    SectionIn RO

    ; ── Copia TUDO do dist/WinPE_Studio para $INSTDIR ────
    ; Isso inclui: exe, todas as DLLs, PySide6, drivers, etc.
    SetOutPath "$INSTDIR"
    SetOverwrite on
    File /r "dist\WinPE_Studio\*.*"

    ; ── Scripts BAT de suporte ────────────────────────────
    File "GEMINI_HOST.bat"
    File "KIRO_SMB.bat"
    File "KIRO_CONECTOR.bat"
    File "KIRO_CONECTOR_MAIN.bat"

    ; ── Criar pastas de trabalho ──────────────────────────
    CreateDirectory "$INSTDIR\WinPE_Studio_Workspace"
    CreateDirectory "$INSTDIR\IMAGENS\IMG"
    CreateDirectory "$INSTDIR\logs"

    ; ── Configurar Firewall ───────────────────────────────
    DetailPrint "Configurando Firewall para PXE..."
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="WinPE Studio DHCP"'
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="WinPE Studio DHCP" dir=in action=allow protocol=UDP localport=67 profile=any'
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="WinPE Studio TFTP" dir=in action=allow protocol=UDP localport=69 profile=any'
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="WinPE Studio HTTP" dir=in action=allow protocol=TCP localport=8080 profile=any'
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="WinPE Studio SMB"  dir=in action=allow protocol=TCP localport=445 profile=any'

    ; ── Criar usuario ACESSO/REDE ─────────────────────────
    DetailPrint "Criando usuario de rede ACESSO..."
    nsExec::ExecToLog 'net user ACESSO REDE /add /expires:never /passwordchg:no'
    nsExec::ExecToLog 'net user ACESSO REDE'
    nsExec::ExecToLog 'net localgroup Administrators ACESSO /add'
    nsExec::ExecToLog 'net localgroup Administradores ACESSO /add'

    ; ── Registros LSA ─────────────────────────────────────
    WriteRegDWORD HKLM "SYSTEM\CurrentControlSet\Control\Lsa" "forceguest" 0
    WriteRegDWORD HKLM "SYSTEM\CurrentControlSet\Control\Lsa" "LimitBlankPasswordUse" 0
    WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" "LocalAccountTokenFilterPolicy" 1

    ; ── Compartilhamento SMB ──────────────────────────────
    DetailPrint "Configurando compartilhamento IMG..."
    nsExec::ExecToLog 'net share IMG /delete'
    nsExec::ExecToLog 'net share IMG="$INSTDIR\IMAGENS\IMG" /grant:ACESSO,FULL /unlimited'
    nsExec::ExecToLog 'net share IMG /grant:Everyone,FULL'
    nsExec::ExecToLog 'icacls "$INSTDIR\IMAGENS\IMG" /grant *S-1-1-0:(OI)(CI)F /T /C /Q'

    ; ── Atalhos ───────────────────────────────────────────
    CreateDirectory "$SMPROGRAMS\WinPE Studio"
    CreateShortcut "$SMPROGRAMS\WinPE Studio\WinPE Studio Pro.lnk" "$INSTDIR\${PRODUCT_EXE}"
    CreateShortcut "$SMPROGRAMS\WinPE Studio\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\WinPE Studio Pro.lnk" "$INSTDIR\${PRODUCT_EXE}"

    ; ── Registro desinstalacao ────────────────────────────
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayName"      "${PRODUCT_NAME}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayVersion"   "${PRODUCT_VERSION}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "Publisher"        "${PRODUCT_PUBLISHER}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "InstallLocation"  "$INSTDIR"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "UninstallString"  "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify"         1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair"         1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize"    3000000

    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

; ── Desinstalador ─────────────────────────────────────────
Section "Uninstall"
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="WinPE Studio DHCP"'
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="WinPE Studio TFTP"'
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="WinPE Studio HTTP"'
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="WinPE Studio SMB"'
    nsExec::ExecToLog 'net share IMG /delete'

    RMDir /r "$INSTDIR\PySide6"
    RMDir /r "$INSTDIR\win32"
    RMDir /r "$INSTDIR\Pythonwin"
    RMDir /r "$INSTDIR\app"
    RMDir /r "$INSTDIR\_internal"
    RMDir /r "$INSTDIR\pywin32_system32"
    RMDir /r "$INSTDIR\shiboken6"

    Delete "$INSTDIR\${PRODUCT_EXE}"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\*.dll"
    Delete "$INSTDIR\*.pyd"
    Delete "$INSTDIR\*.bat"
    Delete "$INSTDIR\*.zip"
    Delete "$INSTDIR\README.md"

    Delete "$DESKTOP\WinPE Studio Pro.lnk"
    Delete "$SMPROGRAMS\WinPE Studio\WinPE Studio Pro.lnk"
    Delete "$SMPROGRAMS\WinPE Studio\Desinstalar.lnk"
    RMDir  "$SMPROGRAMS\WinPE Studio"

    DeleteRegKey HKLM "${UNINSTALL_KEY}"

    MessageBox MB_OK "WinPE Studio desinstalado.$\n$\nPastas preservadas:$\n$INSTDIR\WinPE_Studio_Workspace$\n$INSTDIR\IMAGENS"
    RMDir "$INSTDIR"
SectionEnd

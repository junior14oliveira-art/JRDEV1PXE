; ============================================================
; JRDEV1 PXE — Instalador Profissional
; Gera: JRDEV1FINAL.EXE
; ============================================================

Unicode True

!define APP_NAME      "JRDEV1 PXE"
!define APP_VERSION   "2.1.0"
!define APP_PUBLISHER "JRDEV1 Software"
!define APP_URL       "https://www.instagram.com/jrdev1"
!define APP_EXE       "JRDEV1_PXE.exe"
!define INSTALL_DIR   "$PROGRAMFILES64\JRDEV1 PXE"
!define REG_KEY       "Software\Microsoft\Windows\CurrentVersion\Uninstall\JRDEV1PXE"

; Compressão máxima
SetCompressor /SOLID lzma
SetCompressorDictSize 64

Name "${APP_NAME} v${APP_VERSION}"
OutFile "E:\JRDEV1FINAL.EXE"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${REG_KEY}" "InstallLocation"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

; ── Includes ─────────────────────────────────────────────────────────────
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; ── Interface ─────────────────────────────────────────────────────────────
!define MUI_ABORTWARNING
!define MUI_ICON   "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Cores azul marinho JRDEV1
!define MUI_BGCOLOR          "0D1B3E"
!define MUI_TEXTCOLOR        "E8EDF5"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis3-metro.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\nsis3-metro.bmp"

; ── Páginas de instalação ─────────────────────────────────────────────────
!define MUI_WELCOMEPAGE_TITLE "Bem-vindo ao ${APP_NAME}"
!define MUI_WELCOMEPAGE_TEXT "Este assistente irá instalar o ${APP_NAME} v${APP_VERSION} no seu computador.$\r$\n$\r$\nSolução profissional para boot PXE, clonagem e customização de imagens WinPE em redes corporativas.$\r$\n$\r$\nClique em Avançar para continuar."

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_TITLE "Instalação Concluída!"
!define MUI_FINISHPAGE_TEXT "${APP_NAME} foi instalado com sucesso.$\r$\n$\r$\nClique em Concluir para fechar o assistente."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Iniciar ${APP_NAME} agora"
!define MUI_FINISHPAGE_LINK "Instagram: @jrdev1"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"
!insertmacro MUI_PAGE_FINISH

; ── Páginas de desinstalação ──────────────────────────────────────────────
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── Idioma ────────────────────────────────────────────────────────────────
!insertmacro MUI_LANGUAGE "PortugueseBR"

; ── Informações do instalador ─────────────────────────────────────────────
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey /LANG=0 "ProductName"      "${APP_NAME}"
VIAddVersionKey /LANG=0 "ProductVersion"   "${APP_VERSION}"
VIAddVersionKey /LANG=0 "CompanyName"      "${APP_PUBLISHER}"
VIAddVersionKey /LANG=0 "LegalCopyright"   "© 2024-2026 JRDEV1"
VIAddVersionKey /LANG=0 "FileDescription"  "${APP_NAME} Installer"
VIAddVersionKey /LANG=0 "FileVersion"      "${APP_VERSION}"

; ════════════════════════════════════════════════════════════════════════
;  INSTALAÇÃO
; ════════════════════════════════════════════════════════════════════════
Section "Programa Principal" SecMain
    SectionIn RO  ; obrigatório

    SetOutPath "$INSTDIR"
    SetOverwrite on

    ; Copia toda a pasta dist/JRDEV1_PXE/
    File /r "dist\JRDEV1_PXE\*.*"

    ; Cria atalho no Desktop COM flag "Executar como Administrador" (UAC)
    ; O CreateShortcut padrao do NSIS nao suporta UAC — usamos PowerShell
    nsExec::ExecToLog 'powershell -NoProfile -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut(\"$DESKTOP\JRDEV1 PXE.lnk\"); $s.TargetPath=\"$INSTDIR\${APP_EXE}\"; $s.WorkingDirectory=\"$INSTDIR\"; $s.Description=\"JRDEV1 PXE — WinPE Studio Pro\"; $s.Save(); $bytes=[System.IO.File]::ReadAllBytes(\"$DESKTOP\JRDEV1 PXE.lnk\"); $bytes[21]=$bytes[21] -bor 0x20; [System.IO.File]::WriteAllBytes(\"$DESKTOP\JRDEV1 PXE.lnk\", $bytes)"'

    ; Cria atalho no Menu Iniciar COM flag UAC
    CreateDirectory "$SMPROGRAMS\JRDEV1 PXE"
    nsExec::ExecToLog 'powershell -NoProfile -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut(\"$SMPROGRAMS\JRDEV1 PXE\JRDEV1 PXE.lnk\"); $s.TargetPath=\"$INSTDIR\${APP_EXE}\"; $s.WorkingDirectory=\"$INSTDIR\"; $s.Description=\"JRDEV1 PXE — WinPE Studio Pro\"; $s.Save(); $bytes=[System.IO.File]::ReadAllBytes(\"$SMPROGRAMS\JRDEV1 PXE\JRDEV1 PXE.lnk\"); $bytes[21]=$bytes[21] -bor 0x20; [System.IO.File]::WriteAllBytes(\"$SMPROGRAMS\JRDEV1 PXE\JRDEV1 PXE.lnk\", $bytes)"'
    CreateShortcut "$SMPROGRAMS\JRDEV1 PXE\Desinstalar.lnk" \
        "$INSTDIR\Uninstall.exe"

    ; Registra no Painel de Controle (Adicionar/Remover Programas)
    WriteRegStr   HKLM "${REG_KEY}" "DisplayName"      "${APP_NAME} v${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"   "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "Publisher"        "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${REG_KEY}" "URLInfoAbout"     "${APP_URL}"
    WriteRegStr   HKLM "${REG_KEY}" "InstallLocation"  "$INSTDIR"
    WriteRegStr   HKLM "${REG_KEY}" "UninstallString"  "$INSTDIR\Uninstall.exe"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayIcon"      "$INSTDIR\${APP_EXE}"
    WriteRegDWORD HKLM "${REG_KEY}" "NoModify"         1
    WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"         1

    ; Estima tamanho instalado
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${REG_KEY}" "EstimatedSize" "$0"

    ; Cria desinstalador
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Abre regra de firewall para o programa
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="JRDEV1 PXE"'
    nsExec::ExecToLog 'netsh advfirewall firewall add rule name="JRDEV1 PXE" dir=in action=allow program="$INSTDIR\${APP_EXE}" enable=yes profile=any'

SectionEnd

; ════════════════════════════════════════════════════════════════════════
;  DESINSTALAÇÃO
; ════════════════════════════════════════════════════════════════════════
Section "Uninstall"

    ; Remove regra de firewall
    nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="JRDEV1 PXE"'

    ; Remove arquivos
    RMDir /r "$INSTDIR"

    ; Remove atalhos
    Delete "$DESKTOP\JRDEV1 PXE.lnk"
    RMDir /r "$SMPROGRAMS\JRDEV1 PXE"

    ; Remove registro
    DeleteRegKey HKLM "${REG_KEY}"

    ; Remove dados do programa (licença) — pergunta antes
    MessageBox MB_YESNO "Deseja remover também os dados de licença?" IDNO skip_data
        RMDir /r "C:\ProgramData\WinPEStudio"
    skip_data:

SectionEnd

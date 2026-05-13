import subprocess
import os

def create_desktop_shortcut():
    # Caminhos absolutos
    target = r"E:\PXEGEMINI\WinPE_Studio\start_winpe_studio.bat"
    work_dir = r"E:\PXEGEMINI\WinPE_Studio"
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    shortcut_path = os.path.join(desktop, "WinPE Studio Pro.lnk")
    
    # PowerShell Script limpo e robusto
    # Nota: Removi a manipulação de bytes que pode corromper o arquivo em algumas máquinas
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target}"
    $Shortcut.WorkingDirectory = "{work_dir}"
    $Shortcut.IconLocation = "shell32.dll,12"
    $Shortcut.Description = "WinPE Studio Pro - Editor de ISO"
    $Shortcut.Save()
    """
    
    try:
        # Remove se já existir
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            
        subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True)
        print(f"Atalho recriado com sucesso em: {shortcut_path}")
    except Exception as e:
        print(f"Erro ao criar atalho: {e}")

if __name__ == "__main__":
    create_desktop_shortcut()

"""Serviço para operações DISM: montar/desmontar WIM e adicionar drivers."""
import subprocess
from pathlib import Path
from typing import Callable
from loguru import logger


class DismError(Exception):
    """Erro específico de operações DISM."""


def _run_dism(args: list[str], log_cb: Callable[[str], None] | None = None) -> bool:
    """
    Executa o DISM com os argumentos fornecidos.
    Faz streaming da saída linha a linha para log_cb se fornecido.
    Retorna True em caso de sucesso.
    """
    cmd = ["dism"] + args
    logger.info(f"Executando: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:  # type: ignore[union-attr]
            line = line.rstrip()
            if line:
                logger.debug(f"[DISM] {line}")
                if log_cb:
                    log_cb(line)
        proc.wait()
        if proc.returncode != 0:
            logger.error(f"DISM retornou código {proc.returncode}")
            return False
        return True
    except FileNotFoundError:
        raise DismError("DISM não encontrado. Verifique o Windows ADK/instalação.")
    except Exception as e:
        logger.exception(f"Erro inesperado ao executar DISM: {e}")
        return False


class DismService:
    """
    Encapsula operações DISM para o WinPE Studio.
    Todas as operações são síncronas — use DismWorker para executar em thread.
    """

    def mount_wim(
        self,
        wim_path: str | Path,
        mount_dir: str | Path,
        index: int = 1,
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """Monta um arquivo WIM em um diretório."""
        import subprocess
        wim_path = Path(wim_path)
        mount_dir = Path(mount_dir)
        mount_dir.mkdir(parents=True, exist_ok=True)

        if not wim_path.exists():
            raise DismError(f"Arquivo WIM não encontrado: {wim_path}")

        # --- FIX: Limpeza da pasta Mount antes de montar (Erro 0xc1420114) ---
        if mount_dir.exists() and any(mount_dir.iterdir()):
            logger.warning("Pasta Mount não está vazia. Tentando limpeza automática...")

            # 1) Descarte via DISM (silencioso)
            subprocess.run(
                f'dism /Unmount-Wim /MountDir:"{mount_dir}" /Discard',
                shell=True, capture_output=True, timeout=30
            )
            # 2) Cleanup-Wim para remover mounts órfãos
            subprocess.run('dism /Cleanup-Wim', shell=True, capture_output=True, timeout=60)

            # 3) rd /s /q: mais confiável que shutil.rmtree no Windows
            subprocess.run(f'rd /s /q "{mount_dir}"', shell=True, capture_output=True, timeout=30)

            # 4) Recriar pasta vazia
            mount_dir.mkdir(parents=True, exist_ok=True)

            # 5) Verificar se ficou limpa — se não, criar pasta alternativa com timestamp
            if any(mount_dir.iterdir()):
                from datetime import datetime
                stamp = datetime.now().strftime("%H%M%S")
                alt_dir = mount_dir.parent / f"Mount_{stamp}"
                alt_dir.mkdir(parents=True, exist_ok=True)
                logger.warning(
                    f"Pasta original travada (handle do SO). "
                    f"Usando pasta alternativa: {alt_dir}"
                )
                mount_dir = alt_dir
            else:
                logger.success("Pasta Mount limpa com sucesso.")
        # -----------------------------------------------------------------------

        return _run_dism(
            [
                f"/Mount-Wim",
                f"/WimFile:{wim_path}",
                f"/index:{index}",
                f"/MountDir:{mount_dir}",
            ],
            log_cb=log_cb,
        ), str(mount_dir)   # Retorna também o diretório real usado

    def unmount_wim(
        self,
        mount_dir: str | Path,
        commit: bool = True,
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """Desmonta um arquivo WIM."""
        mount_dir = Path(mount_dir)
        
        if log_cb:
            log_cb(f"Preparando para desmontar: {mount_dir}")

        # Tenta fechar o explorer.exe se ele estiver prendendo a pasta
        # (Isso ajuda muito a evitar o erro 0xc1420117)
        import subprocess
        if log_cb:
            log_cb("⚠️ Tentando liberar arquivos travados pelo Explorer...")
        subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
        # O Explorer reinicia sozinho no Windows, mas vamos garantir
        subprocess.run("start explorer.exe", shell=True, capture_output=True)

        args = [
            f"/Unmount-Wim",
            f"/MountDir:{mount_dir}",
        ]
        if commit:
            args.append("/Commit")
        else:
            args.append("/Discard")

        success = _run_dism(args, log_cb=log_cb)
        
        # Tratamento de erro 0xc142011d (Montagem parcial/suja)
        if not success:
            if log_cb:
                log_cb("❌ Erro na desmontagem. Tentando limpeza de emergência (Cleanup-Wim)...")
            subprocess.run("dism /Cleanup-Wim", shell=True, capture_output=True)
            # Tenta desmontar novamente com Discard se o Commit falhou e travou
            if commit:
                 if log_cb:
                     log_cb("⚠️ Tentando desmontar sem salvar para liberar a pasta...")
                 _run_dism([f"/Unmount-Wim", f"/MountDir:{mount_dir}", "/Discard"], log_cb=log_cb)

        return success

    def add_drivers(
        self,
        mount_dir: str | Path,
        driver_path: str | Path,
        recurse: bool = True,
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """Adiciona drivers (pasta .inf) ao WIM montado."""
        args = [
            f"/Image:{mount_dir}",
            f"/Add-Driver",
            f"/Driver:{driver_path}",
            "/ForceUnsigned",
        ]
        if recurse:
            args.append("/Recurse")
        return _run_dism(args, log_cb=log_cb)

    def add_package(
        self,
        mount_dir: str | Path,
        package_path: str | Path,
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """Adiciona um pacote (.cab ou .msu) ao WIM montado."""
        args = [
            f"/Image:{mount_dir}",
            f"/Add-Package",
            f"/PackagePath:{package_path}",
        ]
        return _run_dism(args, log_cb=log_cb)

    def get_wim_info(self, wim_path: str | Path) -> dict:
        """Retorna informações básicas sobre um arquivo WIM."""
        result: dict = {"indexes": [], "raw": ""}
        cmd = ["dism", f"/Get-WimInfo", f"/WimFile:{wim_path}"]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=30
            )
            result["raw"] = proc.stdout
            # Parse básico de índices
            for line in proc.stdout.splitlines():
                if line.strip().startswith("Index :"):
                    result["indexes"].append(line.split(":")[-1].strip())
            return result
        except Exception as e:
            logger.error(f"Erro ao obter info do WIM: {e}")
            return result

    def cleanup_mounts(self, log_cb: Callable[[str], None] | None = None) -> bool:
        """Limpa montagens WIM corrompidas/pendentes."""
        return _run_dism(["/Cleanup-Wim"], log_cb=log_cb)

    def set_wallpaper(self, mount_dir: str | Path, image_path: str | Path) -> bool:
        """Substitui o papel de parede padrão do WinPE (winpe.jpg/bmp)."""
        import shutil
        import subprocess
        mount_dir = Path(mount_dir)
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"Imagem de fundo não encontrada: {image_path}")
            return False
            
        # Lista de possíveis caminhos de wallpaper (WinPE padrão e Strelec)
        targets = [
            mount_dir / "Windows" / "System32" / "winpe.jpg",
            mount_dir / "Windows" / "System32" / "winpe.bmp",
            mount_dir / "Windows" / "Web" / "Wallpaper" / "Windows" / "img0.jpg", # Win10+ standard
            # Caminhos comuns em WinPEs customizados (Strelec, etc)
            mount_dir / "SSTR" / "ST_USER.JPG",
            mount_dir / "SSTR" / "M_USER.JPG",
        ]
        
        success = False
        try:
            for target in targets:
                # Se o diretório pai não existe, pula este alvo
                if not target.parent.exists():
                    continue
                
                # Toma posse e dá permissão se o arquivo já existir
                if target.exists():
                    subprocess.run(['takeown', '/f', str(target), '/a'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['icacls', str(target), '/grant', '*S-1-5-32-544:F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['attrib', '-r', '-h', '-s', str(target)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    try:
                        target.unlink()
                    except:
                        pass
                
                # Copia a nova imagem (mantendo a extensão original do alvo se necessário, ou apenas forçando)
                # O ideal é converter se a extensão for diferente, mas por enquanto vamos apenas copiar
                shutil.copy(str(image_path), str(target))
                logger.info(f"Papel de parede atualizado em: {target}")
                success = True
            
            return success
        except Exception as e:
            logger.error(f"Erro ao trocar wallpaper: {e}")
            return False

    def inject_autostart_program(self, mount_dir: str | Path, exe_path: str | Path) -> bool:
        """Copia um executável para o WinPE e adiciona ao startnet.cmd para inicialização automática."""
        import shutil
        import subprocess
        mount_dir = Path(mount_dir)
        exe_path = Path(exe_path)
        
        if not exe_path.exists():
            logger.error(f"Executável não encontrado: {exe_path}")
            return False
            
        sys32_dir = mount_dir / "Windows" / "System32"
        startnet_path = sys32_dir / "startnet.cmd"
        
        if not sys32_dir.exists():
            logger.error("Pasta System32 não encontrada no WIM.")
            return False
            
        try:
            # Destino do executável
            dest_exe = sys32_dir / exe_path.name
            
            # Se o arquivo já existe (ex: explorer.exe), precisamos tomar posse antes de sobrescrever
            if dest_exe.exists():
                subprocess.run(['takeown', '/f', str(dest_exe), '/a'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['icacls', str(dest_exe), '/grant', '*S-1-5-32-544:F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['attrib', '-r', '-h', '-s', str(dest_exe)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    dest_exe.unlink()
                except:
                    pass

            # Copia o novo executável
            shutil.copy(str(exe_path), str(dest_exe))
            logger.info(f"Executável injetado em: {dest_exe}")
            
            # Adiciona ao startnet.cmd se existir
            if startnet_path.exists():
                # Toma posse e dá permissão no startnet.cmd (arquivo de sistema)
                subprocess.run(['takeown', '/f', str(startnet_path), '/a'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['icacls', str(startnet_path), '/grant', '*S-1-5-32-544:F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['attrib', '-r', '-h', '-s', str(startnet_path)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Lê o conteúdo atual para evitar duplicidade
                content = ""
                try:
                    with open(startnet_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except:
                    pass
                
                command = f"start \"\" \"X:\\Windows\\System32\\{exe_path.name}\""
                if command not in content:
                    with open(startnet_path, "a", encoding="utf-8", errors="ignore") as f:
                        f.write(f"\n{command}\n")
                    logger.info(f"Comando de auto-start adicionado ao startnet.cmd para {exe_path.name}")
                else:
                    logger.info(f"Comando de auto-start já existe no startnet.cmd")
            else:
                logger.warning("startnet.cmd não encontrado. O programa foi copiado, mas não iniciará automaticamente.")
                
            return True
        except Exception as e:
            logger.error(f"Erro ao injetar programa de auto-start: {e}")
            return False

    def inject_httpdisk(self, mount_dir: str | Path, http_url: str, log_cb: Callable[[str], None] | None = None) -> bool:
        """Injeta o driver e o executável do HTTPDisk no WinPE e configura a montagem automática."""
        import shutil
        import subprocess
        mount_dir = Path(mount_dir)
        
        if log_cb:
            log_cb("💉 Iniciando injeção do suporte a ISO via Rede (HTTPDisk)...")
            
        try:
            # Caminhos dos binários no disco E: (baseado na análise prévia)
            boot_tools = Path(r"E:\PXEGEMINI\boot")
            sys_file = boot_tools / "httpdisk.sys"
            exe_file = boot_tools / "httpdisk.exe"
            
            if not sys_file.exists() or not exe_file.exists():
                if log_cb:
                    log_cb("❌ Erro: Binários do HTTPDisk (httpdisk.sys/exe) não encontrados em E:\\PXEGEMINI\\boot")
                return False

            sys32_dir = mount_dir / "Windows" / "System32"
            drivers_dir = sys32_dir / "drivers"
            startnet_path = sys32_dir / "startnet.cmd"

            # 1. Copiar arquivos para a imagem montada
            shutil.copy2(str(sys_file), str(drivers_dir / "httpdisk.sys"))
            shutil.copy2(str(exe_file), str(sys32_dir / "httpdisk.exe"))
            if log_cb:
                log_cb("✅ Driver e Executável copiados para o WinPE.")

            # 2. Configurar auto-montagem no startnet.cmd
            if startnet_path.exists():
                # Toma posse e dá permissão
                subprocess.run(['takeown', '/f', str(startnet_path), '/a'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['icacls', str(startnet_path), '/grant', '*S-1-5-32-544:F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Comando para registrar serviço e montar ISO
                # Nota: Usamos sc create e sc start. O comando de montagem aponta para o servidor HTTP
                http_commands = (
                    f"\r\n:: --- CONFIGURACAO HTTPDISK --- \r\n"
                    f"echo [HTTP] Registrando driver de disco virtual...\r\n"
                    f"sc create HttpDisk binpath= system32\\drivers\\httpdisk.sys type= kernel start= demand\r\n"
                    f"sc start HttpDisk\r\n"
                    f"echo [HTTP] Montando ISO em Y: de {http_url} ...\r\n"
                    f"httpdisk.exe /mount 0 {http_url} /size 0 Y:\r\n"
                    f":: ---------------------------- \r\n"
                )
                
                with open(startnet_path, "a", encoding="utf-8", errors="ignore") as f:
                    f.write(http_commands)
                
                if log_cb:
                    log_cb(f"✅ Comando de montagem injetado para: {http_url}")
            
            return True
        except Exception as e:
            if log_cb:
                log_cb(f"❌ Erro ao injetar HTTPDisk: {e}")
            return False

    def patch_scripts_for_pe(self, mount_dir: str | Path, log_cb: Callable[[str], None] | None = None) -> int:
        """
        Analisa e edita arquivos .bat/.cmd para funcionarem no disco X: do WinPE.
        Retorna o número de arquivos modificados.
        """
        import re
        mount_dir = Path(mount_dir)
        count = 0
        
        if log_cb:
            log_cb(f"🔍 Analisando scripts em: {mount_dir}")

        # Padrão para encontrar letras de disco fixas (C:, D:, E:, F:, G:) seguidas de \
        # Evita trocar X: (que já é o disco do PE)
        pattern = re.compile(r'([C-G]):\\', re.IGNORECASE)

        for script in mount_dir.rglob("*"):
            if script.suffix.lower() in [".bat", ".cmd"]:
                try:
                    # Tenta ler o conteúdo (BATs costumam ser latin1 ou utf8)
                    try:
                        content = script.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        content = script.read_text(encoding="latin1")
                    
                    # Verifica se há referências a discos fixos
                    if pattern.search(content):
                        # Substitui C:\, D:\, etc. por %SystemDrive%\ (que é X:\ no PE)
                        new_content = pattern.sub(r'%SystemDrive%\\', content)
                        
                        script.write_text(new_content, encoding="utf-8")
                        count += 1
                        if log_cb:
                            log_cb(f"✅ Script corrigido: {script.name}")
                except Exception as e:
                    if log_cb:
                        log_cb(f"⚠ Erro ao processar {script.name}: {e}")
        
        if log_cb:
            log_cb(f"📊 Total de scripts corrigidos para Disco X: {count}")
        return count

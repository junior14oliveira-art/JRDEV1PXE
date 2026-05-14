"""Servico para extracao e criacao de ISOs de Windows PE."""
import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import Callable
from loguru import logger


class IsoError(Exception):
    """Erro especifico de operacoes ISO."""


# Caminhos padrão onde o 7-Zip costuma ser instalado no Windows
_7ZIP_CANDIDATES = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
    r"D:\Program Files\7-Zip\7z.exe",
    r"E:\Program Files\7-Zip\7z.exe",
]


def _find_7zip() -> str:
    """Retorna o caminho do 7z.exe, buscando no PATH e em caminhos conhecidos."""
    # 1. Tenta via PATH
    found = shutil.which("7z")
    if found:
        return found
    # 2. Tenta caminhos de instalacao padrao
    for candidate in _7ZIP_CANDIDATES:
        if Path(candidate).exists():
            logger.info(f"7-Zip encontrado em: {candidate}")
            return candidate
    return "7z"  # fallback (vai falhar com mensagem clara)


class IsoService:
    """
    Lida com extracao de ISOs (via 7-Zip),
    deteccao da estrutura do WinPE e criacao de nova ISO com oscdimg.
    """

    def __init__(self, seven_zip_path: str = ""):
        # Se nao especificado, detecta automaticamente
        self.seven_zip = seven_zip_path or _find_7zip()

    # ------------------------------------------------------------------ #
    #  Extração                                                            #
    # ------------------------------------------------------------------ #

    def extract_iso(
        self,
        iso_path: str | Path,
        output_dir: str | Path,
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """
        Extrai uma ISO para output_dir usando 7-Zip.
        Fallback: copia a ISO diretamente se 7z não estiver disponível.
        """
        iso_path = Path(iso_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not iso_path.exists():
            raise IsoError(f"ISO não encontrada: {iso_path}")

        # --- FIX: Limpeza forçada antes de extrair (Evita Erro 2 do 7-Zip) ---
        if output_dir.exists():
            logger.warning(f"Diretório de destino {output_dir} já existe. Tentando liberar arquivos...")
            try:
                # Se houver um boot.wim lá, tenta garantir que ele não esteja montado
                boot_wim = output_dir / "sources" / "boot.wim"
                if boot_wim.exists():
                    # Comando rápido para limpar qualquer mount órfão que possa estar prendendo o WIM
                    subprocess.run("dism /Cleanup-Wim", shell=True, capture_output=True, timeout=30)
                
                # Tenta deletar o conteúdo atual para limpar espaço e locks
                import shutil
                shutil.rmtree(str(output_dir), ignore_errors=True)
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Não foi possível limpar a pasta antes da extração: {e}")
        # --------------------------------------------------------------------

        logger.info(f"Extraindo ISO: {iso_path} -> {output_dir}")
        try:
            cmd = [self.seven_zip, "x", str(iso_path), f"-o{output_dir}", "-y"]
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
                    logger.debug(f"[7z] {line}")
                    if log_cb:
                        log_cb(line)
            proc.wait()
            if proc.returncode not in (0, 1):
                raise IsoError(f"7-Zip retornou código {proc.returncode}")
            logger.info("Extração concluída.")
            return True
        except FileNotFoundError:
            raise IsoError(
                "7-Zip nao encontrado. Instale em:\n"
                "https://www.7-zip.org/download.html\n\n"
                "Caminhos testados:\n"
                + "\n".join(f"  - {c}" for c in _7ZIP_CANDIDATES)
            )

    def detect_winpe_structure(self, extracted_dir: str | Path) -> dict:
        """
        Detecta a estrutura do WinPE extraído.
        Retorna um dict com os caminhos encontrados.
        """
        base = Path(extracted_dir)
        result = {
            "boot_wim": None,
            "install_wim": None,
            "sources_dir": None,
            "boot_dir": None,
            "efi_dir": None,
            "architecture": "unknown",
        }

        # sources/boot.wim
        candidates = [
            base / "sources" / "boot.wim",
            base / "Boot" / "boot.wim",
        ]
        for c in candidates:
            if c.exists():
                result["boot_wim"] = str(c)
                break

        # sources/install.wim
        install = base / "sources" / "install.wim"
        if install.exists():
            result["install_wim"] = str(install)

        # sources dir
        sources = base / "sources"
        if sources.is_dir():
            result["sources_dir"] = str(sources)

        # boot dir
        boot = base / "boot"
        if boot.is_dir():
            result["boot_dir"] = str(boot)

        # BCD — necessario para boot PXE via wimboot
        for bcd_candidate in [
            base / "Boot" / "BCD",
            base / "boot" / "BCD",
            base / "EFI" / "Microsoft" / "Boot" / "BCD",
        ]:
            if bcd_candidate.exists():
                result["bcd"] = str(bcd_candidate)
                break

        # boot.sdi — necessario para boot PXE via wimboot
        for sdi_candidate in [
            base / "Boot" / "boot.sdi",
            base / "boot" / "boot.sdi",
        ]:
            if sdi_candidate.exists():
                result["boot_sdi"] = str(sdi_candidate)
                break

        # EFI dir
        efi = base / "EFI"
        if efi.is_dir():
            result["efi_dir"] = str(efi)

        # Arquitetura
        amd64 = base / "sources" / "boot.wim"
        if (base / "bootmgr.exe").exists() or (base / "bootmgr").exists():
            result["architecture"] = "x64"

        logger.info(f"Estrutura WinPE detectada: {result}")
        return result

    # ------------------------------------------------------------------ #
    #  Criação de ISO                                                      #
    # ------------------------------------------------------------------ #

    def build_iso(
        self,
        source_dir: str | Path,
        output_iso: str | Path,
        oscdimg_path: str = "oscdimg",
        volume_label: str = "WINPE_STUDIO",
        log_cb: Callable[[str], None] | None = None,
    ) -> bool:
        """
        Cria uma ISO bootável usando oscdimg.
        Requer o Windows ADK instalado.
        """
        source_dir = Path(source_dir)
        output_iso = Path(output_iso)
        output_iso.parent.mkdir(parents=True, exist_ok=True)

        if not source_dir.is_dir():
            raise IsoError(f"Diretório fonte não encontrado: {source_dir}")

        # ── FIX: Remover pastas Mount_* antes de gerar ISO ──────────────
        # Pastas de montagem DISM dentro do workspace causam erro 5 no oscdimg
        # (acesso negado a arquivos de sistema como RtBackup dentro do mount)
        for mount_folder in source_dir.glob("Mount_*"):
            if mount_folder.is_dir():
                if log_cb:
                    log_cb(f"⚠️  Pasta de montagem detectada: {mount_folder.name} — removendo antes de gerar ISO...")
                logger.warning(f"Removendo pasta de montagem órfã: {mount_folder}")
                try:
                    # Tenta desmontar via DISM primeiro (caso ainda esteja montada)
                    subprocess.run(
                        ["dism", "/Unmount-Wim", f"/MountDir:{mount_folder}", "/Discard"],
                        capture_output=True, timeout=60
                    )
                    subprocess.run(
                        ["dism", "/Cleanup-Wim"],
                        capture_output=True, timeout=60
                    )
                    import shutil as _shutil
                    _shutil.rmtree(str(mount_folder), ignore_errors=True)
                    if log_cb:
                        log_cb(f"✅  Pasta {mount_folder.name} removida.")
                except Exception as e:
                    logger.warning(f"Não foi possível remover {mount_folder}: {e}")
                    if log_cb:
                        log_cb(f"⚠️  Não foi possível remover {mount_folder.name}: {e}")
        # ────────────────────────────────────────────────────────────────

        etfsboot = source_dir / "boot" / "etfsboot.com"
        efisys = source_dir / "efi" / "microsoft" / "boot" / "efisys.bin"

        # Tenta encontrar caminhos alternativos na ISO se o padrão falhar
        if not etfsboot.exists():
            found = list(source_dir.rglob("etfsboot.com"))
            if found:
                etfsboot = found[0]

        if not efisys.exists():
            found = list(source_dir.rglob("efisys.bin"))
            if found:
                efisys = found[0]

        # FALLBACK PARA OS ARQUIVOS OFICIAIS DO ADK
        oscdimg_dir = Path(oscdimg_path).parent
        if not etfsboot.exists():
            adk_etfsboot = oscdimg_dir / "etfsboot.com"
            if adk_etfsboot.exists():
                etfsboot = adk_etfsboot
                logger.info(f"Usando etfsboot.com oficial do ADK: {etfsboot}")

        if not efisys.exists():
            adk_efisys = oscdimg_dir / "efisys.bin"
            if adk_efisys.exists():
                efisys = adk_efisys
                logger.info(f"Usando efisys.bin oficial do ADK: {efisys}")

        # --- FIX CRÍTICO: Copiar arquivos de boot para pasta temporária na RAIZ ---
        # Oscdimg tem bugs conhecidos ao lidar com caminhos longos ou espaços
        temp_boot_dir = Path("E:/WinPE_Temp_Boot")
        temp_boot_dir.mkdir(parents=True, exist_ok=True)
        
        final_etfs = temp_boot_dir / "etfsboot.com"
        final_efi = temp_boot_dir / "efisys.bin"
        
        if etfsboot.exists():
            shutil.copy(str(etfsboot), str(final_etfs))
            etfsboot = final_etfs
        if efisys.exists():
            shutil.copy(str(efisys), str(final_efi))
            efisys = final_efi
        # --- FIX: Boot Direto (Sem "Press any key") ---
        # Se o arquivo bootfix.bin existir, a ISO pede para apertar uma tecla.
        # Removendo ele, o boot se torna automático.
        bootfix = source_dir / "boot" / "bootfix.bin"
        if bootfix.exists():
            try:
                bootfix.unlink()
                logger.info("bootfix.bin removido para habilitar Boot Direto.")
            except Exception as e:
                logger.warning(f"Não foi possível remover bootfix.bin: {e}")
        # ----------------------------------------------

        # Comando base com flags de compatibilidade moderna
        cmd = [
            oscdimg_path,
            "-m",      # Ignora limite de tamanho padrão
            "-o",      # Otimiza armazenamento (arquivos duplicados)
            "-u2",     # Formato UDF
            "-udfver102",
            "-h",      # Inclui arquivos ocultos
            f"-l{volume_label}",
        ]

        # Logica correta de boot (UEFI + BIOS)
        has_bios = etfsboot.exists()
        has_uefi = efisys.exists()

        if has_bios and has_uefi:
            # Dual boot: BIOS (p0) + UEFI (pEF)
            # Sem aspas internas, o subprocess do Python cuidará do escape se necessário
            boot_data = f"-bootdata:2#p0,e,b{etfsboot}#pEF,e,b{efisys}"
            cmd.append(boot_data)
        elif has_bios:
            cmd.append(f"-b{etfsboot}")
            logger.warning("efisys.bin nao encontrado. ISO sera apenas BIOS.")
        elif has_uefi:
            cmd.extend(["-pEF", f"-b{efisys}"])
            logger.warning("etfsboot.com nao encontrado. ISO sera apenas UEFI.")
        else:
            logger.warning("Nenhum arquivo de boot encontrado! A ISO nao sera bootavel.")

        cmd += [str(source_dir), str(output_iso)]

        logger.info(f"Construindo ISO (v2.0): {' '.join(cmd)}")
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
                    logger.debug(f"[oscdimg] {line}")
                    if log_cb:
                        log_cb(line)
            proc.wait()
            if proc.returncode != 0:
                raise IsoError(f"oscdimg retornou código {proc.returncode}")
            logger.success(f"ISO criada com sucesso: {output_iso}")
            return True
        except FileNotFoundError:
            raise IsoError(
                f"oscdimg não encontrado em '{oscdimg_path}'. "
                "Instale o Windows ADK (Deployment Tools)."
            )

    def get_iso_info(self, iso_path: str | Path) -> dict:
        """Retorna informações básicas sobre a ISO (tamanho, nome)."""
        p = Path(iso_path)
        if not p.exists():
            return {}
        size_bytes = p.stat().st_size
        return {
            "name": p.name,
            "size_mb": round(size_bytes / (1024 ** 2), 1),
            "size_gb": round(size_bytes / (1024 ** 3), 2),
            "path": str(p),
        }

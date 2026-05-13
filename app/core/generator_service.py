"""Serviço para gerar um WinPE limpo usando o Windows ADK instalado."""
import subprocess
import os
from pathlib import Path
from typing import Callable
from loguru import logger

class GeneratorService:
    """Usa as ferramentas do Windows ADK para criar uma ISO de WinPE do zero."""

    def generate_vanilla_pe(
        self, 
        dest_iso: str | Path, 
        arch: str = "amd64",
        log_cb: Callable[[str], None] | None = None
    ) -> bool:
        """Cria uma ISO de WinPE limpa usando copype e makewinpemedia."""
        dest_iso = Path(dest_iso)
        temp_dir = Path("E:/WinPE_Temp_Build")
        
        # 1. Limpar pasta temporária se existir
        if temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

        # 2. Localizar as ferramentas do ADK
        # Tenta o caminho padrão primeiro
        adk_base = Path(r"C:\Program Files (x86)\Windows Kits")
        copype_bat = None
        
        # Busca recursiva para ser mais resiliente a versões (10, 11, etc)
        for p in adk_base.rglob("copype.cmd"):
            copype_bat = p
            break
            
        if not copype_bat:
            logger.error("copype.cmd não encontrado. O WinPE Add-on do ADK está instalado?")
            if log_cb: log_cb("ERRO: copype.cmd não encontrado. Você PRECISA instalar o 'Windows PE Add-on' do ADK.")
            return False

        adk_root = copype_bat.parent.parent # Geralmente ...\Windows Preinstallation Environment

        try:
            # Passo A: copype
            if log_cb: log_cb(f"Criando estrutura de arquivos WinPE ({arch})...")
            cmd_copy = [str(copype_bat), arch, str(temp_dir)]
            subprocess.run(cmd_copy, check=True, capture_output=True, text=True)
            
            # Passo B: makewinpemedia
            if log_cb: log_cb("Gerando imagem ISO...")
            
            make_media_bat = None
            for p in adk_base.rglob("makewinpemedia.cmd"):
                make_media_bat = p
                break
                
            if not make_media_bat:
                if log_cb: log_cb("ERRO: makewinpemedia.cmd não encontrado.")
                return False
            
            cmd_make = [str(make_media_bat), "/ISO", str(temp_dir), str(dest_iso)]
            subprocess.run(cmd_make, check=True, capture_output=True, text=True)
            
            if log_cb: log_cb(f"WinPE Original gerado com sucesso em: {dest_iso}")
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar WinPE: {e}")
            if log_cb: log_cb(f"ERRO: {e}")
            return False
        finally:
            # Opcional: limpar temp_dir
            pass

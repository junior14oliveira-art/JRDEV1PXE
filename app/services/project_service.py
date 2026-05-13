import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger

class WinPEConfig(BaseModel):
    """Modelo de dados para a configuração do projeto WinPE."""
    project_name: str
    base_iso_path: Optional[str] = None
    output_iso_name: str = "WinPE_Custom.iso"
    wallpaper_path: Optional[str] = None
    theme: str = "dark"
    added_apps: List[str] = Field(default_factory=list)
    drivers_paths: List[str] = Field(default_factory=list)

class ProjectService:
    """
    Serviço responsável por gerenciar projetos do WinPE Studio.
    Lida com a criação, carregamento e salvamento de metadados do projeto.
    """
    def __init__(self, workspace_path: str = "projects"):
        self.workspace = Path(workspace_path)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_project: Optional[WinPEConfig] = None
        self.current_project_path: Optional[Path] = None

    def create_project(self, name: str) -> bool:
        """Cria um novo projeto WinPE vazio."""
        project_dir = self.workspace / name
        if project_dir.exists():
            logger.warning(f"O projeto '{name}' já existe.")
            return False

        project_dir.mkdir()
        config = WinPEConfig(project_name=name)
        config_path = project_dir / "project.json"
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=4)
        
        logger.info(f"Projeto '{name}' criado com sucesso em {project_dir}")
        self.current_project = config
        self.current_project_path = project_dir
        return True

    def load_project(self, name: str) -> bool:
        """Carrega um projeto existente."""
        project_dir = self.workspace / name
        config_path = project_dir / "project.json"
        
        if not config_path.exists():
            logger.error(f"Configuração do projeto '{name}' não encontrada.")
            return False

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.current_project = WinPEConfig(**data)
                self.current_project_path = project_dir
                logger.info(f"Projeto '{name}' carregado.")
                return True
        except Exception as e:
            logger.exception(f"Erro ao carregar o projeto '{name}': {e}")
            return False

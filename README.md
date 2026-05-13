# WinPE Studio

WinPE Studio é um software desktop profissional para criação, personalização e empacotamento de imagens Windows PE (WinPE). Inspirado em soluções de mercado como Strelec, Hiren's Boot e Win10XPE, o WinPE Studio oferece uma interface moderna e intuitiva para gerenciar arquivos, programas portáteis, drivers e configurações do Windows PE antes de gerar a ISO final bootável.

## Arquitetura do Projeto

A arquitetura do WinPE Studio foi desenvolvida seguindo princípios de Clean Architecture, MVC/MVVM e modularidade.

```
WinPE_Studio/
├── app/
│   ├── main.py                # Ponto de entrada (QApplication)
│   ├── core/                  # Configurações globais e infraestrutura (Logger, Config)
│   ├── ui/                    # Interface de usuário (PySide6)
│   │   ├── main_window.py     # Janela principal
│   │   ├── styles.py          # Arquivo de estilos (QSS) do tema
│   │   ├── components/        # Componentes reutilizáveis (Sidebar, Cards)
│   │   └── views/             # Telas específicas (Dashboard, Editor, Builder)
│   ├── services/              # Lógica de negócios (IsoService, ProjectService, BuildService)
│   ├── models/                # Modelos de dados (Pydantic, SQLAlchemy)
│   ├── controllers/           # Intermediários entre UI e Services
│   ├── utils/                 # Funções auxiliares (File IO, WIM manipulation)
│   ├── workers/               # Threads assíncronas (QThread) para não travar a UI
│   ├── assets/                # Imagens, ícones e fontes
│   └── plugins/               # Sistema de plugins para scripts e ferramentas extras
├── tests/                     # Testes unitários (pytest)
├── pyproject.toml             # Gerenciamento de dependências (Poetry)
└── README.md                  # Documentação do projeto
```

## Requisitos
- Python 3.12+
- Poetry (ou UV)
- PySide6 para a interface gráfica
- Windows ADK instalado para ferramentas como `dism` e `oscdimg`.

## Inicializando o Projeto
```bash
# Instalar dependências
poetry install

# Executar aplicação
poetry run python -m app.main
```

## Heurísticas de Usabilidade (Nielsen) Aplicadas:
1. **Visibilidade do status do sistema**: Barras de progresso e console de logs em tempo real durante a extração e o build.
2. **Compatibilidade com o mundo real**: Uso de terminologias conhecidas por técnicos e analistas (ISO, WIM, Drivers, Registro).
3. **Controle e liberdade do usuário**: Capacidade de desfazer ações, criar novos projetos isolados e modificar sem alterar a imagem base diretamente.
4. **Consistência e padrões**: Interface em padrão Dark Theme corporativo similar a IDEs modernas.

## Componentes Técnicos
- **Loguru**: Para logs estruturados detalhados que auxiliam o debug e fornecem feedback ao usuário.
- **Pydantic**: Para validação e persistência dos dados do projeto (salvos em `project.json`).
- **QThread (Workers)**: Operações longas como extração de WIM e empacotamento de ISO rodam em threads separadas.

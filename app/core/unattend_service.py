"""
Serviço para gerar autounattend.xml — instalação automática do Windows.
O arquivo gerado é injetado na ISO e faz o Windows instalar sem nenhuma
interação do usuário: formata o disco, instala, cria usuário e reinicia.
"""
from pathlib import Path
from typing import Optional
from loguru import logger


class UnattendConfig:
    """Configurações para a instalação automática."""
    def __init__(self):
        self.username: str = "usuario"
        self.password: str = ""                    # vazio = sem senha
        self.computer_name: str = "*"              # * = gerado automaticamente
        self.timezone: str = "E. South America Standard Time"  # Brasília
        self.language: str = "pt-BR"
        self.disk_index: int = 0                   # disco 0 = primeiro disco
        self.partition_style: str = "GPT"          # GPT (UEFI) ou MBR (BIOS)
        self.windows_edition: str = "Professional" # edição do Windows
        self.skip_oobe: bool = True                # pula configuração inicial
        self.auto_logon: bool = True               # login automático na 1ª vez
        self.auto_logon_count: int = 1


def generate_autounattend(config: UnattendConfig, output_path: str | Path) -> bool:
    """
    Gera o arquivo autounattend.xml com as configurações fornecidas.
    Retorna True se gerou com sucesso.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Senha em base64 para o autologon (formato exigido pelo Windows)
    import base64
    password_b64 = base64.b64encode(
        (config.password + "Password").encode("utf-16-le")
    ).decode("ascii") if config.password else ""

    # Particionamento GPT (UEFI) ou MBR (BIOS Legacy)
    if config.partition_style == "GPT":
        partition_xml = _gpt_partitions(config.disk_index)
    else:
        partition_xml = _mbr_partitions(config.disk_index)

    # AutoLogon — só inclui se tiver senha ou se for sem senha
    if config.auto_logon:
        autologon_xml = f"""
        <AutoLogon>
            <Password>
                <Value>{config.password}</Value>
                <PlainText>true</PlainText>
            </Password>
            <Enabled>true</Enabled>
            <LogonCount>{config.auto_logon_count}</LogonCount>
            <Username>{config.username}</Username>
        </AutoLogon>"""
    else:
        autologon_xml = ""

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">

  <!-- ═══════════════════════════════════════════════════════════════
       FASE 1: windowsPE — Particionamento e seleção da edição
       ═══════════════════════════════════════════════════════════════ -->
  <settings pass="windowsPE">

    <!-- Idioma do instalador -->
    <component name="Microsoft-Windows-International-Core-WinPE"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS"
               xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <SetupUILanguage>
        <UILanguage>pt-BR</UILanguage>
      </SetupUILanguage>
      <InputLocale>pt-BR</InputLocale>
      <SystemLocale>pt-BR</SystemLocale>
      <UILanguage>pt-BR</UILanguage>
      <UserLocale>pt-BR</UserLocale>
    </component>

    <!-- Configuração do disco e particionamento -->
    <component name="Microsoft-Windows-Setup"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS"
               xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">

      <DiskConfiguration>
        <WillShowUI>Never</WillShowUI>
        <Disk wcm:action="add">
          <DiskID>{config.disk_index}</DiskID>
          <WillWipeDisk>true</WillWipeDisk>
          {partition_xml}
        </Disk>
      </DiskConfiguration>

      <ImageInstall>
        <OSImage>
          <WillShowUI>Never</WillShowUI>
          <InstallFrom>
            <MetaData wcm:action="add">
              <Key>/IMAGE/EDITIONID</Key>
              <Value>{config.windows_edition}</Value>
            </MetaData>
          </InstallFrom>
          <InstallTo>
            <DiskID>{config.disk_index}</DiskID>
            <PartitionID>{"3" if config.partition_style == "GPT" else "2"}</PartitionID>
          </InstallTo>
        </OSImage>
      </ImageInstall>

      <UserData>
        <AcceptEula>true</AcceptEula>
        <FullName>{config.username}</FullName>
        <Organization>JRDEV1</Organization>
        <ProductKey>
          <WillShowUI>Never</WillShowUI>
        </ProductKey>
      </UserData>

    </component>
  </settings>

  <!-- ═══════════════════════════════════════════════════════════════
       FASE 2: specialize — Nome do computador e configurações
       ═══════════════════════════════════════════════════════════════ -->
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS"
               xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>{config.computer_name}</ComputerName>
      <TimeZone>{config.timezone}</TimeZone>
    </component>

    <component name="Microsoft-Windows-International-Core"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS">
      <InputLocale>pt-BR</InputLocale>
      <SystemLocale>pt-BR</SystemLocale>
      <UILanguage>pt-BR</UILanguage>
      <UserLocale>pt-BR</UserLocale>
    </component>

    <!-- Desativa Windows Update durante instalação -->
    <component name="Microsoft-Windows-Security-SPP-UX"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS">
      <SkipAutoActivation>true</SkipAutoActivation>
    </component>

  </settings>

  <!-- ═══════════════════════════════════════════════════════════════
       FASE 3: oobeSystem — Usuário, senha e configuração inicial
       ═══════════════════════════════════════════════════════════════ -->
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-Shell-Setup"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS"
               xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">

      <!-- Pula toda a configuração inicial (OOBE) -->
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideLocalAccountScreen>true</HideLocalAccountScreen>
        <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
        <SkipMachineOOBE>true</SkipMachineOOBE>
        <SkipUserOOBE>true</SkipUserOOBE>
      </OOBE>

      <!-- Conta de usuário local -->
      <UserAccounts>
        <LocalAccounts>
          <LocalAccount wcm:action="add">
            <Password>
              <Value>{config.password}</Value>
              <PlainText>true</PlainText>
            </Password>
            <Description>Conta principal</Description>
            <DisplayName>{config.username}</DisplayName>
            <Group>Administrators</Group>
            <Name>{config.username}</Name>
          </LocalAccount>
        </LocalAccounts>
      </UserAccounts>
      {autologon_xml}

    </component>

    <!-- Desativa perguntas de privacidade -->
    <component name="Microsoft-Windows-International-Core"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS">
      <InputLocale>pt-BR</InputLocale>
      <SystemLocale>pt-BR</SystemLocale>
      <UILanguage>pt-BR</UILanguage>
      <UserLocale>pt-BR</UserLocale>
    </component>

  </settings>

</unattend>
"""

    try:
        output_path.write_text(xml, encoding="utf-8")
        logger.info(f"autounattend.xml gerado: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao gerar autounattend.xml: {e}")
        return False


def inject_autounattend(iso_work_dir: str | Path, config: UnattendConfig) -> tuple[bool, str]:
    """
    Injeta o autounattend.xml na raiz da pasta de trabalho da ISO.
    O arquivo deve estar na RAIZ da ISO para o Windows Setup encontrá-lo.
    """
    work_dir = Path(iso_work_dir)
    if not work_dir.is_dir():
        return False, f"Pasta não encontrada: {work_dir}"

    output = work_dir / "autounattend.xml"
    ok = generate_autounattend(config, output)
    if ok:
        return True, str(output)
    return False, "Falha ao gerar autounattend.xml"


# ── Particionamento GPT (UEFI) ────────────────────────────────────────────── #
def _gpt_partitions(disk_id: int) -> str:
    """
    Layout GPT padrão para UEFI:
    - Partição 1: EFI System (100 MB)
    - Partição 2: Microsoft Reserved (16 MB)
    - Partição 3: Windows (resto do disco)
    """
    return """
          <CreatePartitions>
            <!-- EFI System Partition -->
            <CreatePartition wcm:action="add">
              <Order>1</Order>
              <Type>EFI</Type>
              <Size>100</Size>
            </CreatePartition>
            <!-- Microsoft Reserved Partition -->
            <CreatePartition wcm:action="add">
              <Order>2</Order>
              <Type>MSR</Type>
              <Size>16</Size>
            </CreatePartition>
            <!-- Windows (ocupa o resto do disco) -->
            <CreatePartition wcm:action="add">
              <Order>3</Order>
              <Type>Primary</Type>
              <Extend>true</Extend>
            </CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add">
              <Order>1</Order>
              <PartitionID>1</PartitionID>
              <Label>System</Label>
              <Format>FAT32</Format>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>2</Order>
              <PartitionID>2</PartitionID>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>3</Order>
              <PartitionID>3</PartitionID>
              <Label>Windows</Label>
              <Letter>C</Letter>
              <Format>NTFS</Format>
            </ModifyPartition>
          </ModifyPartitions>"""


# ── Particionamento MBR (BIOS Legacy) ────────────────────────────────────── #
def _mbr_partitions(disk_id: int) -> str:
    """
    Layout MBR para BIOS Legacy:
    - Partição 1: System (350 MB, ativa)
    - Partição 2: Windows (resto do disco)
    """
    return """
          <CreatePartitions>
            <!-- System/Boot -->
            <CreatePartition wcm:action="add">
              <Order>1</Order>
              <Type>Primary</Type>
              <Size>350</Size>
            </CreatePartition>
            <!-- Windows -->
            <CreatePartition wcm:action="add">
              <Order>2</Order>
              <Type>Primary</Type>
              <Extend>true</Extend>
            </CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add">
              <Order>1</Order>
              <PartitionID>1</PartitionID>
              <Label>System</Label>
              <Format>NTFS</Format>
              <Active>true</Active>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>2</Order>
              <PartitionID>2</PartitionID>
              <Label>Windows</Label>
              <Letter>C</Letter>
              <Format>NTFS</Format>
            </ModifyPartition>
          </ModifyPartitions>"""

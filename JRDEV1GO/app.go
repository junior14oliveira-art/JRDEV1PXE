package main

import (
	"context"
	"jrdev1pxe/internal/license"
	"jrdev1pxe/internal/pxe"
	"jrdev1pxe/internal/system"
)

// App struct — exposto ao frontend via Wails
type App struct {
	ctx        context.Context
	pxeServer  *pxe.Server
	licService *license.Service
	sysInfo    *system.Info
}

func NewApp() *App {
	return &App{
		licService: license.NewService(),
		sysInfo:    system.NewInfo(),
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) shutdown(ctx context.Context) {
	if a.pxeServer != nil {
		a.pxeServer.Stop()
	}
}

// ── Licença ──────────────────────────────────────────────────────────────

func (a *App) CheckLicense() license.Status {
	return a.licService.Check()
}

func (a *App) ActivateLicense(key string) license.ActivateResult {
	return a.licService.Activate(key)
}

func (a *App) GetLicenseInfo() license.Info {
	return a.licService.GetInfo()
}

// ── Sistema ───────────────────────────────────────────────────────────────

func (a *App) GetSystemInfo() system.SystemInfo {
	return a.sysInfo.Get()
}

func (a *App) GetNetworkInterfaces() []system.NetworkInterface {
	return a.sysInfo.GetNetworkInterfaces()
}

// ── PXE Server ────────────────────────────────────────────────────────────

func (a *App) StartPXE(ifaceIP, mask, workDir string) pxe.StartResult {
	if a.pxeServer != nil {
		a.pxeServer.Stop()
	}
	a.pxeServer = pxe.NewServer(ifaceIP, mask, workDir)
	return a.pxeServer.Start()
}

func (a *App) StopPXE() {
	if a.pxeServer != nil {
		a.pxeServer.Stop()
		a.pxeServer = nil
	}
}

func (a *App) GetPXELogs() []string {
	if a.pxeServer == nil {
		return []string{}
	}
	return a.pxeServer.GetLogs()
}

func (a *App) IsPXERunning() bool {
	return a.pxeServer != nil && a.pxeServer.IsRunning()
}

// ── ISO / DISM ────────────────────────────────────────────────────────────

func (a *App) ExtractISO(isoPath, workDir string) system.CommandResult {
	return a.sysInfo.ExtractISO(isoPath, workDir)
}

func (a *App) BuildISO(sourceDir, outputISO, label string) system.CommandResult {
	return a.sysInfo.BuildISO(sourceDir, outputISO, label)
}

func (a *App) MountWIM(wimPath, mountDir string) system.CommandResult {
	return a.sysInfo.MountWIM(wimPath, mountDir)
}

func (a *App) UnmountWIM(mountDir string, commit bool) system.CommandResult {
	return a.sysInfo.UnmountWIM(mountDir, commit)
}

func (a *App) InjectDrivers(mountDir, driverDir string) system.CommandResult {
	return a.sysInfo.InjectDrivers(mountDir, driverDir)
}

func (a *App) GetWorkspaceDir() string {
	return `E:\WinPE_Studio_Workspace`
}

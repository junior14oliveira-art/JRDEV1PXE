package system

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"unsafe"
)

// ── Tipos ─────────────────────────────────────────────────────────────────

type CommandResult struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error"`
}

type NetworkInterface struct {
	Name string `json:"name"`
	IP   string `json:"ip"`
	Mask string `json:"mask"`
}

type SystemInfo struct {
	OS          string `json:"os"`
	Arch        string `json:"arch"`
	DISMFound   bool   `json:"dism_found"`
	DISMPath    string `json:"dism_path"`
	SevenZip    string `json:"seven_zip"`
	Oscdimg     string `json:"oscdimg"`
	FreeSpaceGB float64 `json:"free_space_gb"`
	TotalRAMGB  float64 `json:"total_ram_gb"`
}

// ── Info ──────────────────────────────────────────────────────────────────

type Info struct{}

func NewInfo() *Info { return &Info{} }

func (i *Info) Get() SystemInfo {
	info := SystemInfo{
		OS:   runtime.GOOS,
		Arch: runtime.GOARCH,
	}

	// DISM
	dism, err := exec.LookPath("dism")
	if err == nil {
		info.DISMFound = true
		info.DISMPath = dism
	} else {
		winDism := `C:\Windows\System32\dism.exe`
		if _, err := os.Stat(winDism); err == nil {
			info.DISMFound = true
			info.DISMPath = winDism
		}
	}

	// 7-Zip
	for _, p := range []string{
		`C:\Program Files\7-Zip\7z.exe`,
		`C:\Program Files (x86)\7-Zip\7z.exe`,
	} {
		if _, err := os.Stat(p); err == nil {
			info.SevenZip = p
			break
		}
	}

	// oscdimg
	for _, p := range []string{
		`C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe`,
		`C:\Program Files\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe`,
	} {
		if _, err := os.Stat(p); err == nil {
			info.Oscdimg = p
			break
		}
	}

	// Espaço livre em E:
	info.FreeSpaceGB = getFreeSpaceGB("E:\\")

	return info
}

func getFreeSpaceGB(path string) float64 {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	getDiskFreeSpaceEx := kernel32.NewProc("GetDiskFreeSpaceExW")
	var freeBytesAvailable, totalBytes, totalFreeBytes uint64
	p, _ := syscall.UTF16PtrFromString(path)
	getDiskFreeSpaceEx.Call(
		uintptr(unsafe.Pointer(p)),
		uintptr(unsafe.Pointer(&freeBytesAvailable)),
		uintptr(unsafe.Pointer(&totalBytes)),
		uintptr(unsafe.Pointer(&totalFreeBytes)),
	)
	return float64(freeBytesAvailable) / (1024 * 1024 * 1024)
}

func (i *Info) GetNetworkInterfaces() []NetworkInterface {
	var result []NetworkInterface

	out, err := exec.Command("powershell", "-NoProfile", "-Command",
		"Get-NetAdapter | ForEach-Object { "+
			"$a = $_; "+
			"Get-NetIPAddress -InterfaceIndex $a.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | "+
			"Where-Object { $_.IPAddress -notlike '169.254.*' } | "+
			"Select-Object @{N='Name';E={$a.Name}}, @{N='MediaType';E={$a.MediaType}}, IPAddress, PrefixLength "+
			"} | ConvertTo-Json").Output()
	if err != nil {
		return result
	}

	// Parse simples linha a linha
	lines := strings.Split(string(out), "\n")
	var name, ip, mediaType string
	var prefix int
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.Contains(line, `"Name"`) {
			name = extractJSONString(line)
		} else if strings.Contains(line, `"MediaType"`) {
			mediaType = strings.ToLower(extractJSONString(line))
		} else if strings.Contains(line, `"IPAddress"`) {
			ip = extractJSONString(line)
		} else if strings.Contains(line, `"PrefixLength"`) {
			fmt.Sscanf(extractJSONString(line), "%d", &prefix)
		} else if line == "}" || line == "}," {
			if ip != "" && !strings.Contains(mediaType, "802.11") {
				mask := prefixToMask(prefix)
				result = append(result, NetworkInterface{Name: name, IP: ip, Mask: mask})
			}
			name, ip, mediaType = "", "", ""
			prefix = 24
		}
	}
	return result
}

func extractJSONString(line string) string {
	parts := strings.SplitN(line, ":", 2)
	if len(parts) < 2 {
		return ""
	}
	v := strings.TrimSpace(parts[1])
	v = strings.Trim(v, `",`)
	return v
}

func prefixToMask(prefix int) string {
	if prefix <= 0 || prefix > 32 {
		return "255.255.255.0"
	}
	mask := uint32(0xFFFFFFFF) << (32 - prefix)
	return fmt.Sprintf("%d.%d.%d.%d",
		(mask>>24)&0xFF, (mask>>16)&0xFF, (mask>>8)&0xFF, mask&0xFF)
}

// ── ISO / DISM ────────────────────────────────────────────────────────────

func (i *Info) ExtractISO(isoPath, workDir string) CommandResult {
	sevenZip := i.Get().SevenZip
	if sevenZip == "" {
		return CommandResult{false, "", "7-Zip nao encontrado"}
	}
	os.MkdirAll(workDir, 0755)
	out, err := exec.Command(sevenZip, "x", isoPath, "-o"+workDir, "-y").CombinedOutput()
	if err != nil {
		return CommandResult{false, string(out), err.Error()}
	}
	return CommandResult{true, string(out), ""}
}

func (i *Info) BuildISO(sourceDir, outputISO, label string) CommandResult {
	oscdimg := i.Get().Oscdimg
	if oscdimg == "" {
		return CommandResult{false, "", "oscdimg nao encontrado (instale o Windows ADK)"}
	}

	etfsboot := filepath.Join(sourceDir, "boot", "etfsboot.com")
	efisys := filepath.Join(sourceDir, "efi", "microsoft", "boot", "efisys.bin")

	bootData := fmt.Sprintf("-bootdata:2#p0,e,b%s#pEF,e,b%s", etfsboot, efisys)
	args := []string{"-m", "-o", "-u2", "-udfver102", "-h", "-l" + label, bootData, sourceDir, outputISO}

	out, err := exec.Command(oscdimg, args...).CombinedOutput()
	if err != nil {
		return CommandResult{false, string(out), err.Error()}
	}
	return CommandResult{true, string(out), ""}
}

func (i *Info) MountWIM(wimPath, mountDir string) CommandResult {
	os.MkdirAll(mountDir, 0755)
	out, err := exec.Command("dism",
		"/Mount-Wim",
		"/WimFile:"+wimPath,
		"/index:1",
		"/MountDir:"+mountDir).CombinedOutput()
	if err != nil {
		return CommandResult{false, string(out), err.Error()}
	}
	return CommandResult{true, string(out), ""}
}

func (i *Info) UnmountWIM(mountDir string, commit bool) CommandResult {
	action := "/Discard"
	if commit {
		action = "/Commit"
	}
	out, err := exec.Command("dism",
		"/Unmount-Wim",
		"/MountDir:"+mountDir,
		action).CombinedOutput()
	if err != nil {
		return CommandResult{false, string(out), err.Error()}
	}
	return CommandResult{true, string(out), ""}
}

func (i *Info) InjectDrivers(mountDir, driverDir string) CommandResult {
	out, err := exec.Command("dism",
		"/Image:"+mountDir,
		"/Add-Driver",
		"/Driver:"+driverDir,
		"/Recurse").CombinedOutput()
	if err != nil {
		return CommandResult{false, string(out), err.Error()}
	}
	return CommandResult{true, string(out), ""}
}

package license

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base32"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Segredo compartilhado — mesmo valor do Python
var secret = []byte("KIRO_WINPE_2024_#@!_MUDE_ANTES_DE_DISTRIBUIR_#@!")

// MACs do desenvolvedor — isentos de licença
var developerMACs = map[string]bool{
	"00155DD3E415": true,
	"00155D4E59DB": true,
	"00D76D52C943": true,
}

// Caminhos do license.dat
var licenseDir = filepath.Join(os.Getenv("PROGRAMDATA"), "WinPEStudio")
var licenseFile = filepath.Join(licenseDir, "license.dat")
var licenseFileOld = filepath.Join(os.Getenv("APPDATA"), "WinPEStudio", "license.dat")

// ── Tipos ─────────────────────────────────────────────────────────────────

type StatusCode string

const (
	StatusValid    StatusCode = "valid"
	StatusExpired  StatusCode = "expired"
	StatusInvalid  StatusCode = "invalid"
	StatusNotFound StatusCode = "not_found"
	StatusWrongMAC StatusCode = "wrong_mac"
)

type Status struct {
	Code      StatusCode `json:"code"`
	Message   string     `json:"message"`
	DaysLeft  int        `json:"days_left"`
	Expiry    string     `json:"expiry"`
	Developer bool       `json:"developer"`
}

type Info struct {
	Key       string `json:"key"`
	MachineID string `json:"machine_id"`
	Expiry    string `json:"expiry"`
	DaysLeft  int    `json:"days_left"`
	Activated string `json:"activated"`
	Developer bool   `json:"developer"`
}

type ActivateResult struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

type licenseData struct {
	Key        string   `json:"key"`
	MachineID  string   `json:"machine_id"`
	MachineIDs []string `json:"machine_ids"`
	Expiry     string   `json:"expiry"`
	Activated  string   `json:"activated"`
}

// ── Service ───────────────────────────────────────────────────────────────

type Service struct{}

func NewService() *Service {
	return &Service{}
}

// ── Hardware ID ───────────────────────────────────────────────────────────

func getMachineID() string {
	// Tenta MAC via PowerShell
	out, err := exec.Command("powershell", "-NoProfile", "-Command",
		"Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} "+
			"| Sort-Object @{E={if($_.MediaType -eq '802.3'){0}else{1}}}, LinkSpeed -Descending "+
			"| Select-Object -First 1 -ExpandProperty MacAddress").Output()
	if err == nil {
		mac := strings.TrimSpace(string(out))
		mac = strings.ReplaceAll(mac, "-", "")
		mac = strings.ReplaceAll(mac, ":", "")
		mac = strings.ToUpper(mac)
		if len(mac) == 12 {
			return mac
		}
	}

	// Fallback: serial do volume C:
	out, err = exec.Command("powershell", "-NoProfile", "-Command",
		"(Get-WmiObject Win32_LogicalDisk -Filter \"DeviceID='C:'\").VolumeSerialNumber").Output()
	if err == nil {
		serial := strings.TrimSpace(strings.ToUpper(string(out)))
		if len(serial) >= 8 {
			for len(serial) < 12 {
				serial += "0"
			}
			return serial[:12]
		}
	}

	return "000000000000"
}

func getAllMachineIDs() []string {
	ids := map[string]bool{}

	// Todos os MACs ativos
	out, err := exec.Command("powershell", "-NoProfile", "-Command",
		"Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -ExpandProperty MacAddress").Output()
	if err == nil {
		for _, line := range strings.Split(string(out), "\n") {
			mac := strings.TrimSpace(line)
			mac = strings.ReplaceAll(mac, "-", "")
			mac = strings.ReplaceAll(mac, ":", "")
			mac = strings.ToUpper(mac)
			if len(mac) == 12 {
				ids[mac] = true
			}
		}
	}

	// Serial do disco
	out, err = exec.Command("powershell", "-NoProfile", "-Command",
		"(Get-WmiObject Win32_LogicalDisk -Filter \"DeviceID='C:'\").VolumeSerialNumber").Output()
	if err == nil {
		serial := strings.TrimSpace(strings.ToUpper(string(out)))
		if len(serial) >= 8 {
			for len(serial) < 12 {
				serial += "0"
			}
			ids[serial[:12]] = true
		}
	}

	ids[getMachineID()] = true

	result := make([]string, 0, len(ids))
	for id := range ids {
		result = append(result, id)
	}
	return result
}

// ── Geração de chave ──────────────────────────────────────────────────────

func GenerateKey(expiry time.Time) string {
	payload := fmt.Sprintf("WINPE|%s", expiry.Format("2006-01-02"))
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(payload))
	sig := mac.Sum(nil)[:10]
	b32 := base32.StdEncoding.EncodeToString(sig)
	b32 = strings.TrimRight(b32, "=")
	return fmt.Sprintf("KIRO-%s-%s-%s-%s", b32[0:4], b32[4:8], b32[8:12], b32[12:16])
}

func verifyKey(key string, expiry time.Time) bool {
	expected := GenerateKey(expiry)
	clean := func(s string) string {
		return strings.ToUpper(strings.ReplaceAll(strings.ReplaceAll(s, "-", ""), " ", ""))
	}
	return hmac.Equal([]byte(clean(key)), []byte(clean(expected)))
}

func extractExpiry(key string) (time.Time, bool) {
	today := time.Now()
	// Testa datas futuras (5 anos)
	for i := 0; i <= 1825; i++ {
		candidate := today.AddDate(0, 0, i)
		if verifyKey(key, candidate) {
			return candidate, true
		}
	}
	// Testa datas passadas (2 anos)
	for i := 1; i <= 730; i++ {
		candidate := today.AddDate(0, 0, -i)
		if verifyKey(key, candidate) {
			return candidate, true
		}
	}
	return time.Time{}, false
}

// ── Migração ──────────────────────────────────────────────────────────────

func migrateLicense() {
	if _, err := os.Stat(licenseFile); err == nil {
		return // já existe no novo caminho
	}
	if _, err := os.Stat(licenseFileOld); err != nil {
		return // não existe no caminho antigo
	}
	os.MkdirAll(licenseDir, 0755)
	data, err := os.ReadFile(licenseFileOld)
	if err == nil {
		os.WriteFile(licenseFile, data, 0644)
	}
}

// ── Check ─────────────────────────────────────────────────────────────────

func (s *Service) Check() Status {
	migrateLicense()

	// Whitelist do desenvolvedor
	mac := getMachineID()
	if developerMACs[mac] {
		return Status{
			Code:      StatusValid,
			Message:   "Modo desenvolvedor",
			DaysLeft:  99999,
			Expiry:    "2099-12-31",
			Developer: true,
		}
	}

	// Lê license.dat
	data, err := os.ReadFile(licenseFile)
	if err != nil {
		return Status{Code: StatusNotFound, Message: "Licenca nao encontrada"}
	}

	var ld licenseData
	if err := json.Unmarshal(data, &ld); err != nil {
		return Status{Code: StatusInvalid, Message: "Licenca corrompida"}
	}

	// Verifica MAC
	currentIDs := map[string]bool{}
	for _, id := range getAllMachineIDs() {
		currentIDs[strings.ToUpper(id)] = true
	}
	savedIDs := map[string]bool{strings.ToUpper(ld.MachineID): true}
	for _, id := range ld.MachineIDs {
		savedIDs[strings.ToUpper(id)] = true
	}
	match := false
	for id := range currentIDs {
		if savedIDs[id] {
			match = true
			break
		}
	}
	if !match {
		return Status{Code: StatusWrongMAC, Message: "Licenca pertence a outro computador"}
	}

	// Verifica assinatura
	expiry, err2 := time.Parse("2006-01-02", ld.Expiry)
	if err2 != nil || !verifyKey(ld.Key, expiry) {
		return Status{Code: StatusInvalid, Message: "Assinatura invalida"}
	}

	// Verifica expiração
	daysLeft := int(time.Until(expiry).Hours() / 24)
	if time.Now().After(expiry) {
		return Status{Code: StatusExpired, Message: "Licenca expirada", DaysLeft: daysLeft, Expiry: ld.Expiry}
	}

	return Status{Code: StatusValid, Message: "Licenca valida", DaysLeft: daysLeft, Expiry: ld.Expiry}
}

// ── Activate ──────────────────────────────────────────────────────────────

func (s *Service) Activate(key string) ActivateResult {
	key = strings.TrimSpace(strings.ToUpper(key))

	expiry, ok := extractExpiry(key)
	if !ok {
		return ActivateResult{false, "Chave invalida. Verifique se digitou corretamente."}
	}
	if time.Now().After(expiry) {
		return ActivateResult{false, fmt.Sprintf("Licenca expirada em %s", expiry.Format("02/01/2006"))}
	}

	machineID := getMachineID()
	allIDs := getAllMachineIDs()
	daysLeft := int(time.Until(expiry).Hours() / 24)

	ld := licenseData{
		Key:        key,
		MachineID:  machineID,
		MachineIDs: allIDs,
		Expiry:     expiry.Format("2006-01-02"),
		Activated:  time.Now().Format(time.RFC3339),
	}

	os.MkdirAll(licenseDir, 0755)
	data, _ := json.MarshalIndent(ld, "", "  ")
	if err := os.WriteFile(licenseFile, data, 0644); err != nil {
		return ActivateResult{false, "Erro ao salvar licenca: " + err.Error()}
	}

	return ActivateResult{true, fmt.Sprintf("Licenca ativada! Valida ate %s (%d dias)", expiry.Format("02/01/2006"), daysLeft)}
}

// ── GetInfo ───────────────────────────────────────────────────────────────

func (s *Service) GetInfo() Info {
	st := s.Check()
	if st.Developer {
		return Info{Key: "DEVELOPER", DaysLeft: 99999, Expiry: "2099-12-31", Activated: "developer", Developer: true}
	}
	data, err := os.ReadFile(licenseFile)
	if err != nil {
		return Info{}
	}
	var ld licenseData
	json.Unmarshal(data, &ld)
	return Info{
		Key:       ld.Key,
		MachineID: ld.MachineID,
		Expiry:    ld.Expiry,
		DaysLeft:  st.DaysLeft,
		Activated: ld.Activated,
	}
}

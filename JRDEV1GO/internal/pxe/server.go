package pxe

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// StartResult retorna ao frontend
type StartResult struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// Server — PXE completo: DHCP + TFTP + HTTP
type Server struct {
	ip      string
	mask    string
	workDir string
	bootDir string

	running bool
	mu      sync.Mutex
	logs    []string
	logMu   sync.Mutex

	leases   map[string]string // MAC -> IP
	leasesMu sync.Mutex

	stopCh chan struct{}
	httpSrv *http.Server
}

func NewServer(ip, mask, workDir string) *Server {
	return &Server{
		ip:      ip,
		mask:    mask,
		workDir: workDir,
		bootDir: filepath.Join(workDir, "..", "boot_files"),
		leases:  make(map[string]string),
		stopCh:  make(chan struct{}),
	}
}

func (s *Server) log(msg string) {
	ts := time.Now().Format("15:04:05")
	line := fmt.Sprintf("[%s] %s", ts, msg)
	s.logMu.Lock()
	s.logs = append(s.logs, line)
	if len(s.logs) > 500 {
		s.logs = s.logs[len(s.logs)-500:]
	}
	s.logMu.Unlock()
}

func (s *Server) GetLogs() []string {
	s.logMu.Lock()
	defer s.logMu.Unlock()
	cp := make([]string, len(s.logs))
	copy(cp, s.logs)
	return cp
}

func (s *Server) IsRunning() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.running
}

// ── Start ─────────────────────────────────────────────────────────────────

func (s *Server) Start() StartResult {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return StartResult{false, "Servidor ja esta rodando"}
	}

	// Prepara pasta de boot
	os.MkdirAll(s.bootDir, 0755)
	s.copyBootFiles()
	s.generateIPXEScript()

	// Inicia servicos
	go s.runHTTP()
	go s.runTFTP()
	go s.runDHCP()

	s.running = true
	s.log(fmt.Sprintf("====== PXE Server Go v1.0 ======"))
	s.log(fmt.Sprintf("[INIT] IP: %s | Mask: %s", s.ip, s.mask))
	s.log("[INIT] HTTP :8080 | TFTP :69 | DHCP :67")
	s.log("[INIT] SERVIDOR PRONTO")

	return StartResult{true, "Servidor PXE iniciado com sucesso"}
}

func (s *Server) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.running {
		return
	}
	close(s.stopCh)
	s.stopCh = make(chan struct{})
	if s.httpSrv != nil {
		s.httpSrv.Close()
	}
	s.running = false
	s.log("[STOP] Servidor encerrado")
}

// ── Boot files ────────────────────────────────────────────────────────────

func (s *Server) copyBootFiles() {
	// Copia boot.wim do projeto
	src := filepath.Join(s.workDir, "sources", "boot.wim")
	dst := filepath.Join(s.bootDir, "boot.wim")
	if _, err := os.Stat(src); err == nil {
		copyFile(src, dst)
		s.log("[BOOT] boot.wim copiado")
	}

	// BCD
	for _, p := range []string{
		filepath.Join(s.workDir, "Boot", "BCD"),
		filepath.Join(s.workDir, "boot", "BCD"),
	} {
		if _, err := os.Stat(p); err == nil {
			copyFile(p, filepath.Join(s.bootDir, "BCD"))
			s.log("[BOOT] BCD copiado")
			break
		}
	}

	// boot.sdi
	for _, p := range []string{
		filepath.Join(s.workDir, "Boot", "boot.sdi"),
		filepath.Join(s.workDir, "boot", "boot.sdi"),
	} {
		if _, err := os.Stat(p); err == nil {
			copyFile(p, filepath.Join(s.bootDir, "boot.sdi"))
			s.log("[BOOT] boot.sdi copiado")
			break
		}
	}
}

func (s *Server) generateIPXEScript() {
	url := fmt.Sprintf("http://%s:8080", s.ip)
	var lines []string
	lines = append(lines, "#!ipxe")
	lines = append(lines, fmt.Sprintf("echo JRDEV1 PXE Server - %s", s.ip))
	lines = append(lines, fmt.Sprintf("set boot-url %s", url))
	if _, err := os.Stat(filepath.Join(s.bootDir, "BCD")); err == nil {
		lines = append(lines, fmt.Sprintf("initrd %s/BCD BCD", url))
	}
	if _, err := os.Stat(filepath.Join(s.bootDir, "boot.sdi")); err == nil {
		lines = append(lines, fmt.Sprintf("initrd %s/boot.sdi boot.sdi", url))
	}
	lines = append(lines, fmt.Sprintf("initrd %s/boot.wim boot.wim", url))
	lines = append(lines, fmt.Sprintf("kernel %s/wimboot", url))
	lines = append(lines, "boot")

	content := strings.Join(lines, "\n") + "\n"
	os.WriteFile(filepath.Join(s.bootDir, "boot.ipxe"), []byte(content), 0644)
	os.WriteFile(filepath.Join(s.bootDir, "autoexec.ipxe"), []byte(content), 0644)
	s.log("[BOOT] Scripts iPXE gerados")
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

// ── HTTP Server ───────────────────────────────────────────────────────────

func (s *Server) runHTTP() {
	mux := http.NewServeMux()
	mux.Handle("/", http.FileServer(http.Dir(s.bootDir)))
	s.httpSrv = &http.Server{Addr: ":8080", Handler: mux}
	s.log("[HTTP] ONLINE em 0.0.0.0:8080")
	if err := s.httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		s.log(fmt.Sprintf("[HTTP] ERRO: %v", err))
	}
}

// ── TFTP Server ───────────────────────────────────────────────────────────

func (s *Server) runTFTP() {
	conn, err := net.ListenPacket("udp", ":69")
	if err != nil {
		s.log(fmt.Sprintf("[TFTP] ERRO bind: %v", err))
		return
	}
	defer conn.Close()
	s.log("[TFTP] ONLINE em 0.0.0.0:69")

	buf := make([]byte, 2048)
	for {
		select {
		case <-s.stopCh:
			return
		default:
		}
		conn.SetReadDeadline(time.Now().Add(time.Second))
		n, addr, err := conn.ReadFrom(buf)
		if err != nil {
			continue
		}
		if n > 2 && buf[1] == 1 { // RRQ
			pkt := make([]byte, n)
			copy(pkt, buf[:n])
			go s.tftpTransfer(addr, pkt)
		}
	}
}

func (s *Server) tftpTransfer(clientAddr net.Addr, rrq []byte) {
	parts := strings.Split(string(rrq[2:]), "\x00")
	if len(parts) == 0 {
		return
	}
	filename := parts[0]
	s.log(fmt.Sprintf("[TFTP] RRQ %s -> %s", clientAddr, filename))

	path := filepath.Join(s.bootDir, filename)
	f, err := os.Open(path)
	if err != nil {
		s.log(fmt.Sprintf("[TFTP] NAO ENCONTRADO: %s", filename))
		return
	}
	defer f.Close()

	// Detecta blksize nas opções
	blksize := 512
	opts := map[string]string{}
	for i := 2; i+1 < len(parts); i += 2 {
		opts[strings.ToLower(parts[i])] = parts[i+1]
	}
	if v, ok := opts["blksize"]; ok {
		fmt.Sscanf(v, "%d", &blksize)
		if blksize > 8192 {
			blksize = 8192
		}
	}

	conn, err := net.Dial("udp", clientAddr.String())
	if err != nil {
		return
	}
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(30 * time.Second))

	// OACK se pediu opções
	if len(opts) > 0 {
		oack := []byte{0, 6}
		if v, ok := opts["blksize"]; ok {
			oack = append(oack, []byte("blksize\x00"+fmt.Sprintf("%d", blksize)+"\x00")...)
			_ = v
		}
		fi, _ := f.Stat()
		if _, ok := opts["tsize"]; ok {
			oack = append(oack, []byte(fmt.Sprintf("tsize\x00%d\x00", fi.Size()))...)
		}
		conn.Write(oack)
		ack := make([]byte, 4)
		conn.Read(ack)
	}

	// Transfere blocos
	block := uint16(1)
	buf := make([]byte, blksize)
	for {
		n, err := f.Read(buf)
		pkt := make([]byte, 4+n)
		pkt[0], pkt[1] = 0, 3
		binary.BigEndian.PutUint16(pkt[2:], block)
		copy(pkt[4:], buf[:n])

		for retry := 0; retry < 5; retry++ {
			conn.Write(pkt)
			ack := make([]byte, 4)
			conn.SetReadDeadline(time.Now().Add(3 * time.Second))
			if _, rerr := conn.Read(ack); rerr == nil {
				break
			}
		}
		block++
		if n < blksize || err == io.EOF {
			break
		}
	}
	s.log(fmt.Sprintf("[TFTP] OK: %s enviado", filename))
}

// ── DHCP Server ───────────────────────────────────────────────────────────

func (s *Server) runDHCP() {
	conn, err := net.ListenPacket("udp4", ":67")
	if err != nil {
		s.log(fmt.Sprintf("[DHCP] ERRO bind :67: %v", err))
		return
	}
	defer conn.Close()
	s.log("[DHCP] ONLINE em 0.0.0.0:67")

	buf := make([]byte, 4096)
	for {
		select {
		case <-s.stopCh:
			return
		default:
		}
		conn.SetReadDeadline(time.Now().Add(time.Second))
		n, addr, err := conn.ReadFrom(buf)
		if err != nil {
			continue
		}
		if n > 240 && buf[0] == 1 {
			pkt := make([]byte, n)
			copy(pkt, buf[:n])
			go s.handleDHCP(conn, pkt, addr)
		}
	}
}

func (s *Server) parseDHCPOptions(data []byte) map[byte][]byte {
	opts := map[byte][]byte{}
	i := 240
	for i < len(data) {
		code := data[i]
		if code == 255 {
			break
		}
		if code == 0 {
			i++
			continue
		}
		if i+1 >= len(data) {
			break
		}
		length := int(data[i+1])
		if i+2+length > len(data) {
			break
		}
		opts[code] = data[i+2 : i+2+length]
		i += 2 + length
	}
	return opts
}

func (s *Server) getIPForMAC(mac []byte) string {
	key := fmt.Sprintf("%x", mac)
	s.leasesMu.Lock()
	defer s.leasesMu.Unlock()
	if ip, ok := s.leases[key]; ok {
		return ip
	}
	base := s.ip[:strings.LastIndex(s.ip, ".")+1]
	offset := (int(mac[4])^int(mac[5])^int(mac[3]))%50 + 200
	used := map[string]bool{}
	for _, v := range s.leases {
		used[v] = true
	}
	candidate := fmt.Sprintf("%s%d", base, offset)
	for used[candidate] {
		offset = (offset-200+1)%50 + 200
		candidate = fmt.Sprintf("%s%d", base, offset)
	}
	s.leases[key] = candidate
	s.log(fmt.Sprintf("[DHCP] Lease: %x -> %s", mac, candidate))
	return candidate
}

func (s *Server) handleDHCP(conn net.PacketConn, data []byte, addr net.Addr) {
	opts := s.parseDHCPOptions(data)
	msgType := byte(1)
	if v, ok := opts[53]; ok && len(v) > 0 {
		msgType = v[0]
	}

	mac := data[28:34]
	xid := data[4:8]
	vendorClass := opts[60]
	isIPXE := len(opts[175]) > 0
	isPXE := len(vendorClass) > 0 && strings.HasPrefix(string(vendorClass), "PXEClient")

	if msgType == 1 { // DISCOVER
		s.log(fmt.Sprintf("[DHCP] DISCOVER de %x (iPXE=%v PXE=%v)", mac, isIPXE, isPXE))
		s.sendDHCPReply(conn, data, mac, xid, 2, isIPXE, isPXE, vendorClass)
	} else if msgType == 3 { // REQUEST
		srvID := opts[54]
		if len(srvID) == 0 || net.IP(srvID).String() == s.ip {
			s.log(fmt.Sprintf("[DHCP] REQUEST de %x", mac))
			s.sendDHCPReply(conn, data, mac, xid, 5, isIPXE, isPXE, vendorClass)
		}
	}
}

func (s *Server) sendDHCPReply(conn net.PacketConn, data, mac, xid []byte, replyType byte, isIPXE, isPXE bool, vendorClass []byte) {
	offeredIP := s.getIPForMAC(mac)
	typeName := map[byte]string{2: "OFFER", 5: "ACK"}[replyType]

	// Detecta HP
	vc := strings.ToLower(string(vendorClass))
	isHP := strings.Contains(vc, "hp") || strings.Contains(vc, "hewlett") || strings.Contains(vc, "compaq")

	// Escolhe arquivo de boot
	bootFile := ""
	if isPXE || isIPXE {
		if isIPXE {
			bootFile = fmt.Sprintf("http://%s:8080/boot.ipxe", s.ip)
		} else if isHP {
			bootFile = "snponly.efi"
			s.log(fmt.Sprintf("[DHCP] HP detectado — snponly.efi"))
		} else {
			bootFile = "ipxe.efi"
		}
	}

	pkt := make([]byte, 240)
	pkt[0] = 2 // BOOTREPLY
	pkt[1] = 1 // Ethernet
	pkt[2] = 6 // MAC len
	copy(pkt[4:8], xid)
	pkt[10], pkt[11] = 0x80, 0x00 // broadcast
	copy(pkt[16:20], net.ParseIP(offeredIP).To4())
	copy(pkt[20:24], net.ParseIP(s.ip).To4())
	copy(pkt[28:34], mac)

	if bootFile != "" {
		sname := []byte(s.ip)
		if len(sname) > 64 {
			sname = sname[:64]
		}
		copy(pkt[44:], sname)
		bf := []byte(bootFile + "\x00")
		if len(bf) > 128 {
			bf = bf[:128]
		}
		copy(pkt[108:], bf)
	}

	// Magic cookie
	pkt[236], pkt[237], pkt[238], pkt[239] = 0x63, 0x82, 0x53, 0x63

	var options []byte
	options = append(options, 53, 1, replyType)
	options = append(options, 54, 4)
	options = append(options, net.ParseIP(s.ip).To4()...)
	options = append(options, 1, 4)
	options = append(options, net.ParseIP(s.mask).To4()...)
	options = append(options, 3, 4)
	options = append(options, net.ParseIP(s.ip).To4()...)
	options = append(options, 51, 4, 0, 0, 0x1C, 0x20) // 7200s
	options = append(options, 6, 4)
	options = append(options, net.ParseIP(s.ip).To4()...)

	if bootFile != "" {
		options = append(options, 60, 9)
		options = append(options, []byte("PXEClient")...)
		tftp := []byte(s.ip + "\x00")
		options = append(options, 66, byte(len(tftp)))
		options = append(options, tftp...)
		bf67 := []byte(bootFile + "\x00")
		options = append(options, 67, byte(len(bf67)))
		options = append(options, bf67...)
	}
	options = append(options, 255)

	pkt = append(pkt, options...)

	bcast, _ := net.ResolveUDPAddr("udp4", "255.255.255.255:68")
	conn.WriteTo(pkt, bcast)
	s.log(fmt.Sprintf("[DHCP] %s -> %s boot=%s", typeName, offeredIP, bootFile))
}

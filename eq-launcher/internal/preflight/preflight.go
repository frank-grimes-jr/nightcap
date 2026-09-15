// Package preflight verifies release configuration and original on-disk patch
// sites. It does not attest to runtime hook activation or authorize Play.
package preflight

import (
	"bytes"
	"crypto/sha256"
	"debug/pe"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"nightcap/eq-launcher/internal/client"
)

const ConfigPath = "nightcap-patches.cfg"
const CatalogPath = "nightcap-patch-sites.json"
const MaxConfigBytes = 4096
const MaxCatalogBytes = 65536

//go:embed catalog.json
var catalogBytes []byte

type Site struct {
	Name     string `json:"name"`
	RVA      uint32 `json:"rva"`
	Original string `json:"original"`
}
type catalog struct {
	RuntimeSchema uint32   `json:"runtime_schema"`
	ProxyVersion  string   `json:"proxy_version"`
	Schema        int      `json:"schema"`
	ClientSize    int64    `json:"client_size"`
	ClientSHA256  string   `json:"client_sha256"`
	ImageBase     uint32   `json:"image_base"`
	Required      []string `json:"required_features"`
	Optional      []string `json:"optional_features"`
	Sites         []Site   `json:"sites"`
}
type Report struct {
	Supported     bool `json:"supported_executable"`
	ConfigValid   bool `json:"configuration_valid"`
	SitesVerified int  `json:"sites_verified"`
	StaticValid   bool `json:"static_preflight_valid"`
	ReadyToPlay   bool `json:"ready_to_play"`
}

// Catalog returns a private copy for release assembly. A release still needs
// trusted manifest signatures and required inventory entries for both files.
func Catalog() []byte { return bytes.Clone(catalogBytes) }
func policy() (catalog, error) {
	var c catalog
	if err := json.Unmarshal(catalogBytes, &c); err != nil {
		return c, err
	}
	if c.Schema != 1 || c.ClientSize != client.SupportedSize || c.ClientSHA256 != client.SupportedSHA256 || len(c.Required) == 0 || len(c.Sites) == 0 {
		return c, fmt.Errorf("invalid compiled patch catalog")
	}
	return c, nil
}

// ValidateConfig requires one explicit boolean for every known feature. A
// required feature cannot be disabled. There are no ignored/duplicate keys,
// implicit defaults, sections, comments, BOMs or permissive numeric conversions.
func ValidateConfig(raw []byte) error {
	c, err := policy()
	if err != nil {
		return err
	}
	if len(raw) == 0 || len(raw) > MaxConfigBytes {
		return fmt.Errorf("patch configuration size invalid")
	}
	allowed := map[string]bool{"schema": true}
	for _, name := range c.Required {
		allowed[name] = true
	}
	for _, name := range c.Optional {
		allowed[name] = false
	}
	seen := map[string]bool{}
	text := strings.ReplaceAll(string(raw), "\r\n", "\n")
	for _, line := range strings.Split(strings.TrimSuffix(text, "\n"), "\n") {
		name, value, ok := strings.Cut(line, "=")
		required, known := allowed[name]
		if !ok || !known || seen[name] || (value != "0" && value != "1") {
			return fmt.Errorf("invalid or duplicate patch configuration key/value")
		}
		if required && value != "1" {
			return fmt.Errorf("required patch configuration disabled: %s", name)
		}
		seen[name] = true
	}
	for name := range allowed {
		if !seen[name] {
			return fmt.Errorf("missing patch configuration: %s", name)
		}
	}
	return nil
}

// CheckOpen reads the exact executable through the caller's existing handle.
// Installer callers retain an exclusive handle for the entire transaction.
func CheckOpen(file interface {
	io.Reader
	io.Seeker
	Stat() (os.FileInfo, error)
}, config, metadata []byte) (Report, error) {
	var report Report
	if err := ValidateConfig(config); err != nil {
		return report, err
	}
	report.ConfigValid = true
	if !bytes.Equal(metadata, catalogBytes) {
		return report, fmt.Errorf("release patch catalog differs from launcher catalog")
	}
	if _, err := file.Seek(0, io.SeekStart); err != nil {
		return report, err
	}
	info, err := file.Stat()
	if err != nil {
		return report, err
	}
	if !info.Mode().IsRegular() || info.Size() != client.SupportedSize {
		return report, fmt.Errorf("unsupported client executable size/type")
	}
	data, err := io.ReadAll(io.LimitReader(file, client.SupportedSize+1))
	if err != nil {
		return report, err
	}
	sum := sha256.Sum256(data)
	if int64(len(data)) != client.SupportedSize || hex.EncodeToString(sum[:]) != client.SupportedSHA256 {
		return report, fmt.Errorf("unsupported client executable SHA-256")
	}
	report.Supported = true
	c, err := policy()
	if err != nil {
		return report, err
	}
	if err = checkSites(data, c); err != nil {
		return report, err
	}
	report.SitesVerified = len(c.Sites)
	report.StaticValid = true
	return report, nil
}
func checkSites(data []byte, c catalog) error {
	executable, err := pe.NewFile(bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("invalid client PE: %w", err)
	}
	defer executable.Close()
	optional, ok := executable.OptionalHeader.(*pe.OptionalHeader32)
	if !ok || executable.Machine != pe.IMAGE_FILE_MACHINE_I386 || optional.ImageBase != c.ImageBase {
		return fmt.Errorf("unexpected client PE architecture/image base")
	}
	for _, site := range c.Sites {
		expected, err := hex.DecodeString(site.Original)
		if err != nil || len(expected) == 0 {
			return fmt.Errorf("invalid compiled signature: %s", site.Name)
		}
		actual, err := siteBytes(data, executable.Sections, site.RVA, uint64(len(expected)))
		if err != nil {
			return fmt.Errorf("patch site %s: %w", site.Name, err)
		}
		if !bytes.Equal(actual, expected) {
			return fmt.Errorf("patch site %s signature mismatch at RVA %#x", site.Name, site.RVA)
		}
	}
	return nil
}

// Map an RVA through PE section headers, rejecting gaps, zero-filled tails,
// ambiguous section mappings, wraparound and truncated raw data.
func siteBytes(data []byte, sections []*pe.Section, rva uint32, size uint64) ([]byte, error) {
	start, end := uint64(rva), uint64(rva)+size
	if size == 0 || end > 1<<32 {
		return nil, fmt.Errorf("invalid RVA range")
	}
	matches := 0
	var result []byte
	for _, section := range sections {
		base := uint64(section.VirtualAddress)
		span := uint64(section.VirtualSize)
		if uint64(section.Size) > span {
			span = uint64(section.Size)
		}
		sectionEnd := base + span
		if start >= sectionEnd || end <= base {
			continue
		}
		// Any partially intersecting mapping is ambiguous, even if another contains it.
		matches++
		if start < base || end > sectionEnd || end-base > uint64(section.Size) {
			return nil, fmt.Errorf("site is not wholly backed by one raw section")
		}
		offset := uint64(section.Offset) + (start - base)
		if offset+size > uint64(len(data)) {
			return nil, fmt.Errorf("truncated raw section")
		}
		result = data[offset : offset+size]
	}
	if matches != 1 {
		return nil, fmt.Errorf("site has %d section mappings", matches)
	}
	return result, nil
}

// RuntimeRequirements is compiled identity, not data accepted from a health file.
type RuntimePolicy struct {
	Schema        uint32
	ProxyVersion  string
	CatalogSHA256 string
	RequiredMask  uint32
}

func RuntimeRequirements() (RuntimePolicy, error) {
	c, err := policy()
	if err != nil {
		return RuntimePolicy{}, err
	}
	if c.RuntimeSchema != 1 || c.ProxyVersion == "" || len(c.Required) >= 32 {
		return RuntimePolicy{}, fmt.Errorf("invalid compiled runtime contract")
	}
	hash := sha256.Sum256(catalogBytes)
	return RuntimePolicy{Schema: c.RuntimeSchema, ProxyVersion: c.ProxyVersion, CatalogSHA256: hex.EncodeToString(hash[:]), RequiredMask: (uint32(1) << len(c.Required)) - 1}, nil
}

package preflight

import (
	"bytes"
	"debug/pe"
	"encoding/binary"
	"os"
	"strings"
	"testing"
)

func configFixture(t *testing.T) []byte {
	t.Helper()
	c, err := policy()
	if err != nil {
		t.Fatal(err)
	}
	var text strings.Builder
	text.WriteString("schema=1\n")
	for _, name := range c.Required {
		text.WriteString(name + "=1\n")
	}
	for _, name := range c.Optional {
		text.WriteString(name + "=0\n")
	}
	return []byte(text.String())
}
func TestConfigurationContract(t *testing.T) {
	good := configFixture(t)
	if err := ValidateConfig(good); err != nil {
		t.Fatal(err)
	}
	if err := ValidateConfig(bytes.ReplaceAll(good, []byte("\n"), []byte("\r\n"))); err != nil {
		t.Fatal(err)
	}
	c, _ := policy()
	for _, name := range c.Required {
		t.Run("disabled "+name, func(t *testing.T) {
			bad := bytes.Replace(good, []byte(name+"=1"), []byte(name+"=0"), 1)
			if err := ValidateConfig(bad); err == nil {
				t.Fatal("disabled required feature accepted")
			}
		})
	}
	for name, bad := range map[string][]byte{
		"empty": nil, "oversized": bytes.Repeat([]byte("x"), MaxConfigBytes+1),
		"missing":    bytes.Replace(good, []byte("equipment=1\n"), nil, 1),
		"duplicate":  append(bytes.Clone(good), []byte("equipment=1\n")...),
		"unknown":    append(bytes.Clone(good), []byte("equipmnt=1\n")...),
		"BOM":        append([]byte{239, 187, 191}, good...),
		"nul":        append(bytes.Clone(good), 0),
		"nonboolean": bytes.Replace(good, []byte("equipment=1"), []byte("equipment=true"), 1),
		"schema":     bytes.Replace(good, []byte("schema=1"), []byte("schema=2"), 1),
		"comment":    append(bytes.Clone(good), []byte("#comment\n")...),
	} {
		t.Run(name, func(t *testing.T) {
			if err := ValidateConfig(bad); err == nil {
				t.Fatal("bad configuration accepted")
			}
		})
	}
}
func TestMetadataAndExecutableRejection(t *testing.T) {
	f, err := os.CreateTemp(t.TempDir(), "exe")
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	for name, metadata := range map[string][]byte{"missing": nil, "whitespace": append(Catalog(), '\n'), "different": []byte(`{"schema":1}`)} {
		t.Run(name, func(t *testing.T) {
			report, err := CheckOpen(f, configFixture(t), metadata)
			if err == nil || report.StaticValid || report.ReadyToPlay {
				t.Fatalf("bad metadata accepted %+v %v", report, err)
			}
		})
	}
	if report, err := CheckOpen(f, configFixture(t), Catalog()); err == nil || report.StaticValid {
		t.Fatalf("wrong executable accepted %+v %v", report, err)
	}
	if err = f.Truncate(8774656); err != nil {
		t.Fatal(err)
	}
	if report, err := CheckOpen(f, configFixture(t), Catalog()); err == nil || report.Supported {
		t.Fatalf("wrong hash accepted %+v %v", report, err)
	}
}
func section(rva, raw, size, virtual uint32) *pe.Section {
	return &pe.Section{SectionHeader: pe.SectionHeader{VirtualAddress: rva, Offset: raw, Size: size, VirtualSize: virtual}}
}
func TestRVAMapping(t *testing.T) {
	data := make([]byte, 512)
	data[102] = 0xaa
	got, err := siteBytes(data, []*pe.Section{section(0x1000, 100, 20, 20)}, 0x1002, 1)
	if err != nil || !bytes.Equal(got, []byte{0xaa}) {
		t.Fatalf("wrong section mapping %x %v", got, err)
	}
	for _, test := range []struct {
		name     string
		sections []*pe.Section
		rva      uint32
		size     uint64
	}{
		{"gap", []*pe.Section{section(0x1000, 100, 20, 20)}, 0x2000, 1},
		{"zero fill", []*pe.Section{section(0x1000, 100, 10, 20)}, 0x100a, 1},
		{"straddle", []*pe.Section{section(0x1000, 100, 20, 20)}, 0x1013, 2},
		{"overlap", []*pe.Section{section(0x1000, 100, 20, 20), section(0x1001, 200, 20, 20)}, 0x1002, 1},
		{"truncated", []*pe.Section{section(0x1000, 510, 20, 20)}, 0x1002, 1},
		{"overflow", []*pe.Section{section(0xffffff00, 100, 512, 512)}, 0xffffffff, 2},
	} {
		t.Run(test.name, func(t *testing.T) {
			if _, err := siteBytes(data, test.sections, test.rva, test.size); err == nil {
				t.Fatal("unsafe section mapping accepted")
			}
		})
	}
}
func syntheticPE() []byte {
	data := make([]byte, 1024)
	binary.LittleEndian.PutUint16(data, 0x5a4d)
	binary.LittleEndian.PutUint32(data[0x3c:], 0x80)
	copy(data[0x80:], "PE\x00\x00")
	binary.LittleEndian.PutUint16(data[0x84:], pe.IMAGE_FILE_MACHINE_I386)
	binary.LittleEndian.PutUint16(data[0x86:], 1)
	binary.LittleEndian.PutUint16(data[0x94:], 224)
	binary.LittleEndian.PutUint16(data[0x98:], 0x10b)
	binary.LittleEndian.PutUint32(data[0x98+28:], 0x400000)
	binary.LittleEndian.PutUint32(data[0x98+92:], 16)
	section := 0x98 + 224
	copy(data[section:], ".text")
	binary.LittleEndian.PutUint32(data[section+8:], 0x100)
	binary.LittleEndian.PutUint32(data[section+12:], 0x1000)
	binary.LittleEndian.PutUint32(data[section+16:], 0x100)
	binary.LittleEndian.PutUint32(data[section+20:], 0x200)
	data[0x202] = 0xaa
	return data
}
func TestPEAndOriginalSignatureChecks(t *testing.T) {
	c := catalog{ImageBase: 0x400000, Sites: []Site{{Name: "fixture", RVA: 0x1002, Original: "aa"}}}
	if err := checkSites(syntheticPE(), c); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"signature", "image base", "architecture", "malformed"} {
		t.Run(mode, func(t *testing.T) {
			data := syntheticPE()
			switch mode {
			case "signature":
				data[0x202] ^= 1
			case "image base":
				data[0x98+28] ^= 1
			case "architecture":
				data[0x84] ^= 1
			case "malformed":
				data[0] = 'x'
			}
			if err := checkSites(data, c); err == nil {
				t.Fatal("modified PE accepted")
			}
		})
	}
}
func TestExactRoF2Preflight(t *testing.T) {
	path := os.Getenv("NIGHTCAP_TEST_EQGAME")
	if path == "" {
		t.Skip("set NIGHTCAP_TEST_EQGAME for read-only exact-client integration")
	}
	f, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	report, err := CheckOpen(f, configFixture(t), Catalog())
	if err != nil || !report.StaticValid || report.SitesVerified != 22 || report.ReadyToPlay {
		t.Fatalf("exact client preflight %+v %v", report, err)
	}
}

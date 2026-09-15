package preflight

import (
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"testing"
)

// A minimal conventional PE32 image with separate RX code and R export data.
func bootstrapFixture(dll bool) []byte {
	b := make([]byte, 0x800)
	copy(b, "MZ")
	put32(b, 0x3c, 0x80)
	copy(b[0x80:], "PE\x00\x00")
	put16(b, 0x84, 0x14c)
	put16(b, 0x86, 2)
	put16(b, 0x94, 224)
	flags := uint16(0x102)
	if dll {
		flags |= 0x2000
	}
	put16(b, 0x96, flags)
	op := 0x98
	put16(b, op, 0x10b)
	put32(b, op+16, 0x1020)
	put32(b, op+28, 0x400000)
	put32(b, op+32, 0x1000)
	put32(b, op+36, 0x200)
	put32(b, op+56, 0x3000)
	put32(b, op+60, 0x200)
	put32(b, op+92, 16)
	if dll {
		put32(b, op+96, 0x2000)
		put32(b, op+100, 0x100)
	}
	text := op + 224
	copy(b[text:], ".text")
	put32(b, text+8, 0x200)
	put32(b, text+12, 0x1000)
	put32(b, text+16, 0x200)
	put32(b, text+20, 0x200)
	put32(b, text+36, 0x60000020)
	data := text + 40
	copy(b[data:], ".rdata")
	put32(b, data+8, 0x400)
	put32(b, data+12, 0x2000)
	put32(b, data+16, 0x400)
	put32(b, data+20, 0x400)
	put32(b, data+36, 0x40000040)
	b[0x220] = 0xe8
	put32(b, 0x410, 1)
	put32(b, 0x414, 1)
	put32(b, 0x418, 1)
	put32(b, 0x41c, 0x2040)
	put32(b, 0x420, 0x2050)
	put32(b, 0x424, 0x2060)
	put32(b, 0x440, 0x1020)
	put32(b, 0x450, 0x2070)
	put16(b, 0x460, 0)
	copy(b[0x470:], initializerExport+"\x00")
	return b
}
func put32(b []byte, at int, n uint32) { binary.LittleEndian.PutUint32(b[at:at+4], n) }
func put16(b []byte, at int, n uint16) { binary.LittleEndian.PutUint16(b[at:at+2], n) }
func TestBootstrapMetadataFixture(t *testing.T) {
	entry, original, err := bootstrapEntry(bootstrapFixture(false))
	if err != nil || entry != 0x1020 || original != 0xe8 {
		t.Fatalf("entry=%x byte=%x: %v", entry, original, err)
	}
	init, size, err := bootstrapInitializer(bootstrapFixture(true))
	if err != nil || init != 0x1020 || size != 0x3000 {
		t.Fatalf("initializer=%x size=%x: %v", init, size, err)
	}
}
func TestBootstrapRejectsMalformedPE(t *testing.T) {
	cases := []struct {
		name   string
		change func([]byte)
	}{
		{"DOS", func(b []byte) { b[0] = 0 }},
		{"PE offset", func(b []byte) { put32(b, 0x3c, 0xffffffff) }},
		{"PE signature", func(b []byte) { b[0x80] = 0 }},
		{"architecture", func(b []byte) { put16(b, 0x84, 0x8664) }},
		{"no sections", func(b []byte) { put16(b, 0x86, 0) }},
		{"too many sections", func(b []byte) { put16(b, 0x86, 0xffff) }},
		{"COFF symbols", func(b []byte) { put32(b, 0x8c, 0xffffffff) }},
		{"COFF symbol count", func(b []byte) { put32(b, 0x90, 0xffffffff) }},
		{"optional header size", func(b []byte) { put16(b, 0x94, 240) }},
		{"not executable", func(b []byte) { put16(b, 0x96, 0x2000) }},
		{"not DLL", func(b []byte) { put16(b, 0x96, 0x102) }},
		{"PE32 plus", func(b []byte) { put16(b, 0x98, 0x20b) }},
		{"directory count", func(b []byte) { put32(b, 0x98+92, 0xffffffff) }},
		{"relocations", func(b []byte) { put32(b, 0x178+24, 1) }},
		{"image bound", func(b []byte) { put32(b, 0x98+56, 0x1000) }},
		{"image size cap", func(b []byte) { put32(b, 0x98+56, 0xffffffff) }},
		{"preferred base overflow", func(b []byte) { put32(b, 0x98+28, 0xffff0000); put32(b, 0x98+56, 0x20000) }},
		{"headers truncated", func(b []byte) { put32(b, 0x98+60, 0x2000) }},
		{"headers overlap", func(b []byte) { put32(b, 0x98+60, 0x100) }},
		{"virtual overlap", func(b []byte) { put32(b, 0x1a0+12, 0x1000) }},
		{"raw overlap", func(b []byte) { put32(b, 0x1a0+20, 0x200) }},
		{"raw truncated", func(b []byte) { put32(b, 0x1a0+16, 0x600) }},
		{"zero file alignment", func(b []byte) { put32(b, 0x98+36, 0) }},
		{"bad file alignment", func(b []byte) { put32(b, 0x98+36, 0x300) }},
		{"low section alignment", func(b []byte) { put32(b, 0x98+32, 0x200) }},
		{"file greater alignment", func(b []byte) { put32(b, 0x98+36, 0x2000) }},
		{"unaligned VA", func(b []byte) { put32(b, 0x178+12, 0x1001) }},
		{"unaligned raw", func(b []byte) { put32(b, 0x178+20, 0x201) }},
		{"unaligned size", func(b []byte) { put32(b, 0x178+16, 0x201) }},
		{"unaligned image", func(b []byte) { put32(b, 0x98+56, 0x3001) }},
		{"unaligned base", func(b []byte) { put32(b, 0x98+28, 0x400001) }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			b := bootstrapFixture(true)
			tc.change(b)
			if _, _, err := bootstrapInitializer(b); err == nil {
				t.Fatal("malformed PE accepted")
			}
		})
	}
	for _, n := range []int{0, 2, 63, 0x80, 0x98, 0x178, 0x1c7, 0x600} {
		if _, _, err := bootstrapInitializer(bootstrapFixture(true)[:n]); err == nil {
			t.Fatalf("truncation %d accepted", n)
		}
	}
}
func TestBootstrapRejectsInvalidExports(t *testing.T) {
	cases := []struct {
		name   string
		change func([]byte)
	}{
		{"missing directory", func(b []byte) { put32(b, 0x98+96, 0) }},
		{"short directory", func(b []byte) { put32(b, 0x98+100, 39) }},
		{"large directory", func(b []byte) { put32(b, 0x98+100, 1<<21) }},
		{"wrapped directory", func(b []byte) { put32(b, 0x98+96, 0xfffffff0) }},
		{"function count", func(b []byte) { put32(b, 0x414, 0xffffffff) }},
		{"name count", func(b []byte) { put32(b, 0x418, 0xffffffff) }},
		{"EAT gap", func(b []byte) { put32(b, 0x41c, 0x1800) }},
		{"names gap", func(b []byte) { put32(b, 0x420, 0x1800) }},
		{"ordinals gap", func(b []byte) { put32(b, 0x424, 0x1800) }},
		{"invalid ordinal", func(b []byte) { put16(b, 0x460, 1) }},
		{"missing initializer", func(b []byte) { b[0x470] = 'M' }},
		{"zero initializer", func(b []byte) { put32(b, 0x440, 0) }},
		{"forwarder", func(b []byte) { put32(b, 0x440, 0x2090); copy(b[0x490:], "other.Initialize\x00") }},
		{"target gap", func(b []byte) { put32(b, 0x440, 0x1800) }},
		{"target header", func(b []byte) { put32(b, 0x440, 0x100) }},
		{"target zero fill", func(b []byte) { put32(b, 0x178+8, 0x400); put32(b, 0x440, 0x1300) }},
		{"target not code", func(b []byte) { put32(b, 0x440, 0x2200) }},
		{"writable code", func(b []byte) { put32(b, 0x178+36, 0xe0000020) }},
		{"discardable code", func(b []byte) { put32(b, 0x178+36, 0x62000020) }},
		{"name out of bounds", func(b []byte) { put32(b, 0x450, 0xffffffff) }},
		{"unterminated name", func(b []byte) { copy(b[0x470:], bytes.Repeat([]byte("a"), 128)) }},
		{"duplicate name", func(b []byte) { put32(b, 0x418, 2); put32(b, 0x454, 0x2070); put16(b, 0x462, 0) }},
		{"unsorted names", func(b []byte) {
			put32(b, 0x418, 2)
			put32(b, 0x454, 0x2090)
			put16(b, 0x462, 0)
			copy(b[0x490:], "AAA\x00")
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			b := bootstrapFixture(true)
			tc.change(b)
			if _, _, err := bootstrapInitializer(b); err == nil {
				t.Fatal("invalid exports accepted")
			}
		})
	}
}
func TestBootstrapRejectsUnsafeEntry(t *testing.T) {
	for name, change := range map[string]func([]byte){
		"DLL":         func(b []byte) { put16(b, 0x96, 0x2102) },
		"TLS address": func(b []byte) { put32(b, 0x98+96+9*8, 0x2000) },
		"TLS size":    func(b []byte) { put32(b, 0x98+100+9*8, 24) },
		"breakpoint":  func(b []byte) { b[0x220] = 0xcc },
		"gap":         func(b []byte) { put32(b, 0x98+16, 0x1800) },
		"writable":    func(b []byte) { put32(b, 0x178+36, 0xe0000020) },
	} {
		t.Run(name, func(t *testing.T) {
			b := bootstrapFixture(false)
			change(b)
			if _, _, err := bootstrapEntry(b); err == nil {
				t.Fatal("unsafe entry accepted")
			}
		})
	}
}
func TestBootstrapInputBoundsAndIdentity(t *testing.T) {
	p := filepath.Join(t.TempDir(), "image")
	if err := os.WriteFile(p, bootstrapFixture(false), 0600); err != nil {
		t.Fatal(err)
	}
	f, err := os.OpenFile(p, os.O_RDWR, 0600)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	if _, err := BootstrapOpen(f, f); err == nil {
		t.Fatal("synthetic executable trusted")
	}
	if err := f.Truncate(MaxProxyBytes + 1); err != nil {
		t.Fatal(err)
	}
	if _, err := readBootstrapImage(f, MaxProxyBytes); err == nil {
		t.Fatal("oversized proxy accepted")
	}
}
func TestBootstrapActualImages(t *testing.T) {
	exePath, proxyPath := os.Getenv("NIGHTCAP_TEST_EQGAME"), os.Getenv("NIGHTCAP_TEST_PROXY")
	if exePath == "" || proxyPath == "" {
		t.Skip("set NIGHTCAP_TEST_EQGAME and NIGHTCAP_TEST_PROXY for read-only integration")
	}
	exe, err := os.Open(exePath)
	if err != nil {
		t.Fatal(err)
	}
	defer exe.Close()
	proxy, err := os.Open(proxyPath)
	if err != nil {
		t.Fatal(err)
	}
	defer proxy.Close()
	result, err := BootstrapOpen(exe, proxy)
	if err != nil {
		t.Fatal(err)
	}
	if result.EntryRVA != 0x4e3b4a || result.EntryOriginal != 0xe8 || result.InitializerRVA == 0 || result.InitializerRVA >= result.ProxyImageSize {
		t.Fatalf("bad metadata: %+v", result)
	}
	t.Logf("entry=%#x original=%#x initializer=%#x proxy image size=%#x", result.EntryRVA, result.EntryOriginal, result.InitializerRVA, result.ProxyImageSize)
	if _, err := exe.Stat(); err != nil {
		t.Fatal("executable handle closed")
	}
	if _, err := proxy.Stat(); err != nil {
		t.Fatal("proxy handle closed")
	}
}
func FuzzBootstrapPE(f *testing.F) {
	f.Add(bootstrapFixture(true))
	f.Add(bootstrapFixture(false))
	f.Add([]byte("MZ"))
	f.Fuzz(func(t *testing.T, data []byte) {
		if len(data) > 2<<20 {
			t.Skip()
		}
		bootstrapInitializer(data)
		bootstrapEntry(data)
	})
}

package session

import (
	"encoding/binary"
	"strings"
	"testing"

	"nightcap/eq-launcher/internal/preflight"
)

func frame(kind uint32, id Identity, code uint32, reason string) []byte {
	b := make([]byte, messageSize)
	binary.LittleEndian.PutUint32(b, wireMagic)
	binary.LittleEndian.PutUint32(b[4:], kind)
	binary.LittleEndian.PutUint32(b[8:], id.PID)
	binary.LittleEndian.PutUint32(b[12:], code)
	binary.LittleEndian.PutUint64(b[16:], id.Created)
	copy(b[24:], reason)
	return b
}
func TestProtocolRejectsMalformedMessages(t *testing.T) {
	good := frame(healthKind, Identity{5, 8}, 0, "")
	if m, err := decodeMessage(good); err != nil || m.identity.PID != 5 {
		t.Fatal(m, err)
	}
	for name, change := range map[string]func([]byte){
		"magic": func(b []byte) { b[0] ^= 1 }, "kind": func(b []byte) { b[4] = 9 }, "PID": func(b []byte) { b[8] = 0 }, "creation": func(b []byte) { b[16] = 0 }, "code": func(b []byte) { b[12] = 1 },
		"reason": func(b []byte) { b[24] = 'x' }, "padding": func(b []byte) { b[25] = 'x' }, "unterminated": func(b []byte) {
			for i := 24; i < len(b); i++ {
				b[i] = 'x'
			}
		},
	} {
		t.Run(name, func(t *testing.T) {
			b := append([]byte(nil), good...)
			change(b)
			if _, err := decodeMessage(b); err == nil {
				t.Fatal("bad frame accepted")
			}
		})
	}
	for _, b := range [][]byte{nil, good[:87], append(good, 0), frame(failureKind, Identity{}, 1, ""), frame(failureKind, Identity{}, 1, "bad reason")} {
		if _, err := decodeMessage(b); err == nil {
			t.Fatal("bad frame accepted")
		}
	}
	if _, err := decodeMessage(frame(failureKind, Identity{5, 0}, 259, "process_identity")); err != nil {
		t.Fatal("partial failure identity rejected:", err)
	}
}
func TestRequestLayoutAndBounds(t *testing.T) {
	metadata := preflight.BootstrapMetadata{EntryRVA: 0x1020, EntryOriginal: 0xe8, InitializerRVA: 0x2010, ProxyImageSize: 0x3000}
	handles := [3]uint64{4, 8, 12}
	b, err := encodeRequest(`E:\client é`, handles, metadata, 2000)
	if err != nil {
		t.Fatal(err)
	}
	if len(b) != 56+len([]rune(`E:\client é`))*2 || binary.LittleEndian.Uint32(b[32:]) != 0x1020 || binary.LittleEndian.Uint32(b[48:]) != 0xe8 || binary.LittleEndian.Uint64(b[24:]) != 12 {
		t.Fatalf("wrong wire layout: %x", b)
	}
	for _, path := range []string{"relative", `\\server\share`, "E:\x00bad", `E:\bad"path`, `E:\` + strings.Repeat("x", 32700)} {
		if _, err := encodeRequest(path, handles, metadata, 2000); err == nil {
			t.Fatal("unsafe directory:", path)
		}
	}
	for _, h := range [][3]uint64{{0, 8, 12}, {1 << 32, 8, 12}} {
		if _, err := encodeRequest(`E:\client`, h, metadata, 2000); err == nil {
			t.Fatal("invalid handle accepted")
		}
	}
	if _, err := encodeRequest(`E:\client`, handles, metadata, 60001); err == nil {
		t.Fatal("invalid deadline")
	}
}
func TestNonceEnvironmentIsPrivateAndCaseInsensitive(t *testing.T) {
	original := []string{"A=1", "nightcap_launch_nonce=old", "NIGHTCAP_LAUNCH_NONCE=also-old", "B=2"}
	result := nonceEnvironment(original, "new")
	if strings.Join(result, "|") != "A=1|B=2|NIGHTCAP_LAUNCH_NONCE=new" || original[1] != "nightcap_launch_nonce=old" {
		t.Fatal(result, original)
	}
}

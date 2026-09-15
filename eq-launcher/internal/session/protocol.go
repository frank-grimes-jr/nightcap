package session

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"strings"
	"unicode/utf16"
	"unicode/utf8"

	"nightcap/eq-launcher/internal/preflight"
)

const wireMagic uint32 = 0x4e434231
const messageSize = 88
const failureKind, healthKind, startedKind, exitedKind = 0, 1, 2, 3

type message struct {
	kind     uint32
	identity Identity
	code     uint32
	reason   string
}

func decodeMessage(raw []byte) (message, error) {
	var m message
	if len(raw) != messageSize || binary.LittleEndian.Uint32(raw[:4]) != wireMagic {
		return m, fmt.Errorf("invalid helper message framing")
	}
	m.kind = binary.LittleEndian.Uint32(raw[4:8])
	m.identity.PID = binary.LittleEndian.Uint32(raw[8:12])
	m.code = binary.LittleEndian.Uint32(raw[12:16])
	m.identity.Created = binary.LittleEndian.Uint64(raw[16:24])
	reason := raw[24:]
	end := bytes.IndexByte(reason, 0)
	if end < 0 || !bytes.Equal(reason[end:], make([]byte, len(reason)-end)) {
		return m, fmt.Errorf("invalid helper reason padding")
	}
	for _, b := range reason[:end] {
		if !(b >= 'a' && b <= 'z' || b >= '0' && b <= '9' || b == '_') {
			return m, fmt.Errorf("invalid helper reason")
		}
	}
	m.reason = string(reason[:end])
	if m.kind > exitedKind {
		return m, fmt.Errorf("unknown helper message")
	}
	if m.kind == failureKind {
		if m.reason == "" {
			return m, fmt.Errorf("empty helper failure")
		}
		return m, nil
	}
	if m.reason != "" || m.identity.PID == 0 || m.identity.Created == 0 || (m.kind != exitedKind && m.code != 0) {
		return m, fmt.Errorf("invalid helper message fields")
	}
	return m, nil
}
func encodeRequest(directory string, handles [3]uint64, metadata preflight.BootstrapMetadata, timeout uint32) ([]byte, error) {
	if !utf8.ValidString(directory) || strings.ContainsAny(directory, "\x00\r\n\"") || len(directory) < 3 || directory[1] != ':' || directory[2] != '\\' {
		return nil, fmt.Errorf("invalid helper directory")
	}
	units := utf16.Encode([]rune(directory))
	if len(units) > 32700 || timeout == 0 || timeout > 60000 || metadata.EntryRVA == 0 || metadata.EntryOriginal == 0xcc || metadata.InitializerRVA == 0 || metadata.InitializerRVA >= metadata.ProxyImageSize {
		return nil, fmt.Errorf("invalid helper launch metadata")
	}
	for _, h := range handles {
		if h == 0 || h > 0xffffffff {
			return nil, fmt.Errorf("invalid inherited x86 handle")
		}
	}
	raw := make([]byte, 56+len(units)*2)
	put := func(at int, v uint32) { binary.LittleEndian.PutUint32(raw[at:at+4], v) }
	put(0, wireMagic)
	put(4, 1)
	for i, h := range handles {
		binary.LittleEndian.PutUint64(raw[8+i*8:16+i*8], h)
	}
	put(32, metadata.EntryRVA)
	put(36, metadata.InitializerRVA)
	put(40, metadata.ProxyImageSize)
	put(44, timeout)
	put(48, uint32(metadata.EntryOriginal))
	put(52, uint32(len(units)))
	for i, u := range units {
		binary.LittleEndian.PutUint16(raw[56+i*2:58+i*2], u)
	}
	return raw, nil
}
func nonceEnvironment(environment []string, nonce string) []string {
	result := make([]string, 0, len(environment)+1)
	for _, entry := range environment {
		key, _, _ := strings.Cut(entry, "=")
		if !strings.EqualFold(key, "NIGHTCAP_LAUNCH_NONCE") {
			result = append(result, entry)
		}
	}
	return append(result, "NIGHTCAP_LAUNCH_NONCE="+nonce)
}

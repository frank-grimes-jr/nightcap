package manifest

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"strings"
	"testing"
	"time"
)

func fixture(t *testing.T) (Manifest, Trust, ed25519.PrivateKey) {
	t.Helper()
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 9, 15, 12, 0, 0, 0, time.UTC)
	m := Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Files: []File{{Path: "dinput8.dll", SHA256: strings.Repeat("a", 64), Size: 3, URL: "https://releases.example.test/client/dinput8.dll", Required: true}}, Tombstones: []string{}}
	trust := Trust{Keys: []Key{{ID: "release-1", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(24 * time.Hour)}}, Now: now, LauncherVersion: "0.1.0", HighestRelease: 1, Inventory: map[string]bool{"dinput8.dll": true}, Retired: map[string]bool{"old-nightcap.dll": true}, Hosts: []string{"releases.example.test"}}
	return m, trust, priv
}
func signed(t *testing.T, m Manifest, priv ed25519.PrivateKey) ([]byte, Signature) {
	t.Helper()
	raw, err := json.Marshal(m)
	if err != nil {
		t.Fatal(err)
	}
	return raw, Signature{KeyID: "release-1", Bytes: ed25519.Sign(priv, raw)}
}
func TestAuthenticity(t *testing.T) {
	for _, name := range []string{"valid", "tampered", "unsigned", "wrong key", "unknown key", "expired key", "future key", "expired manifest", "future launcher", "downgrade", "same release different bytes", "same release identical bytes", "zero release", "unknown schema", "noncanonical", "duplicate JSON field", "unknown field"} {
		t.Run(name, func(t *testing.T) {
			m, trust, priv := fixture(t)
			switch name {
			case "expired key":
				trust.Keys[0].NotAfter = trust.Now
			case "future key":
				trust.Keys[0].NotBefore = trust.Now.Add(time.Second)
			case "expired manifest":
				m.Expires = trust.Now
			case "future launcher":
				m.MinLauncher = "0.2.0"
			case "downgrade":
				trust.HighestRelease = 3
			case "same release different bytes":
				trust.HighestRelease = 2
				trust.HighestDigest = strings.Repeat("f", 64)
			case "zero release":
				m.Release = 0
			case "unknown schema":
				m.Schema = 2
			}
			raw, sig := signed(t, m, priv)
			switch name {
			case "tampered":
				raw = bytes.Replace(raw, []byte("dinput8"), []byte("evilbad"), 1)
			case "unsigned":
				sig.Bytes = nil
			case "unknown key":
				sig.KeyID = "unknown"
			case "wrong key":
				_, other, _ := ed25519.GenerateKey(rand.Reader)
				sig.Bytes = ed25519.Sign(other, raw)
			case "noncanonical":
				raw = append([]byte(" "), raw...)
				sig.Bytes = ed25519.Sign(priv, raw)
			case "duplicate JSON field":
				raw = bytes.Replace(raw, []byte(`"schema":1`), []byte(`"schema":0,"schema":1`), 1)
				sig.Bytes = ed25519.Sign(priv, raw)
			case "unknown field":
				raw = bytes.Replace(raw, []byte(`"schema":1`), []byte(`"schema":1,"unexpected":true`), 1)
				sig.Bytes = ed25519.Sign(priv, raw)
			case "same release identical bytes":
				trust.HighestRelease = 2
				trust.HighestDigest = Digest(raw)
			}
			_, err := Verify(raw, sig, trust)
			good := name == "valid" || name == "same release identical bytes"
			if (err == nil) != good {
				t.Fatalf("accepted=%v, expected=%v: %v", err == nil, good, err)
			}
		})
	}
}
func TestInventoryAndPaths(t *testing.T) {
	badPaths := []string{"../dinput8.dll", "/dinput8.dll", "C:/dinput8.dll", `uifiles\nightcap\EQUI_Test.xml`, "dinput8.dll:stream", "DINPUT8.DLL", "dinput8.dll.", "dinput8.dll ", "CON", "aux.txt", "uifiles/../dinput8.dll", "uifiles//nightcap/x.xml", "uifiles/nightcap/COM1.xml", "uifiles/nightcap/LPT9.txt", "eqgame.exe", ".nightcap/journal.json"}
	for _, p := range badPaths {
		t.Run(p, func(t *testing.T) {
			m, trust, priv := fixture(t)
			m.Files[0].Path = p
			trust.Inventory = map[string]bool{p: true}
			raw, sig := signed(t, m, priv)
			if _, err := Verify(raw, sig, trust); err == nil {
				t.Fatal("accepted unsafe/foreign path")
			}
		})
	}
	for _, name := range []string{"missing", "foreign", "duplicate", "wrong required", "negative size", "oversize", "bad hash", "http", "foreign host", "userinfo", "port", "encoded path", "fragment", "query", "duplicate tombstone", "foreign tombstone", "live tombstone", "valid retired"} {
		t.Run(name, func(t *testing.T) {
			m, trust, priv := fixture(t)
			switch name {
			case "missing":
				m.Files = nil
			case "foreign":
				m.Files[0].Path = "dbstr_us.txt"
			case "duplicate":
				m.Files = append(m.Files, m.Files[0])
			case "wrong required":
				m.Files[0].Required = false
			case "negative size":
				m.Files[0].Size = -1
			case "oversize":
				m.Files[0].Size = MaxFileBytes + 1
			case "bad hash":
				m.Files[0].SHA256 = strings.Repeat("A", 64)
			case "http":
				m.Files[0].URL = "http://releases.example.test/dinput8.dll"
			case "foreign host":
				m.Files[0].URL = "https://attacker.example.test/dinput8.dll"
			case "userinfo":
				m.Files[0].URL = "https://x@releases.example.test/dinput8.dll"
			case "port":
				m.Files[0].URL = "https://releases.example.test:8443/dinput8.dll"
			case "encoded path":
				m.Files[0].URL = "https://releases.example.test/%2e%2e/evil"
			case "fragment":
				m.Files[0].URL += "#x"
			case "query":
				m.Files[0].URL += "?token=x"
			case "duplicate tombstone":
				m.Tombstones = []string{"old-nightcap.dll", "old-nightcap.dll"}
			case "foreign tombstone":
				m.Tombstones = []string{"eqgame.exe"}
			case "live tombstone":
				m.Tombstones = []string{"dinput8.dll"}
			case "valid retired":
				m.Tombstones = []string{"old-nightcap.dll"}
			}
			raw, sig := signed(t, m, priv)
			_, err := Verify(raw, sig, trust)
			if (err == nil) != (name == "valid retired") {
				t.Fatalf("unexpected result: %v", err)
			}
		})
	}
}
func TestVersionFormat(t *testing.T) {
	for _, version := range []string{"", "1", "1.2", "1.2.3.4", "01.2.3", "1.2.-1", "1.2.3-beta", "999999999999999999999.0.0"} {
		t.Run(version, func(t *testing.T) {
			m, trust, priv := fixture(t)
			m.MinLauncher = version
			raw, sig := signed(t, m, priv)
			if _, err := Verify(raw, sig, trust); err == nil {
				t.Fatal("accepted malformed version")
			}
		})
	}
}

func TestExplicitTombstones(t *testing.T) {
	m, trust, priv := fixture(t)
	m.Tombstones = nil
	raw, sig := signed(t, m, priv)
	if _, err := Verify(raw, sig, trust); err == nil {
		t.Fatal("accepted null tombstone list")
	}
}
func TestReleaseLimits(t *testing.T) {
	for _, name := range []string{"aggregate at limit", "aggregate over limit", "files at limit", "files over limit", "raw over limit", "zero file size"} {
		t.Run(name, func(t *testing.T) {
			m, trust, priv := fixture(t)
			count := 4
			size := MaxFileBytes
			switch name {
			case "aggregate over limit":
				count = 5
			case "files at limit":
				count = MaxFiles
				size = 1
			case "files over limit":
				count = MaxFiles + 1
				size = 1
			case "zero file size":
				count = 1
				size = 0
			}
			m.Files = nil
			trust.Inventory = map[string]bool{}
			for i := 0; i < count; i++ {
				file := File{Path: fmt.Sprintf("uifiles/nightcap/equi_%04d.xml", i), Size: size, SHA256: strings.Repeat("a", 64), URL: "https://releases.example.test/file", Required: true}
				m.Files = append(m.Files, file)
				trust.Inventory[file.Path] = true
			}
			raw, sig := signed(t, m, priv)
			if name == "raw over limit" {
				raw = bytes.Repeat([]byte(" "), MaxManifestBytes+1)
				sig.Bytes = ed25519.Sign(priv, raw)
			}
			_, err := Verify(raw, sig, trust)
			good := name == "aggregate at limit" || name == "files at limit"
			if (err == nil) != good {
				t.Fatalf("accepted=%v expected=%v: %v", err == nil, good, err)
			}
		})
	}
}

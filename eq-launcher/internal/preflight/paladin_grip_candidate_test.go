package preflight

import (
	"encoding/hex"
	"encoding/json"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"
)

// Opt-in real-artifact test, never reads signing material or writes a client.
func TestPaladinGripCandidate(t *testing.T) {
	root := os.Getenv("NIGHTCAP_GRIP_CANDIDATE")
	if root == "" {
		t.Skip("set NIGHTCAP_GRIP_CANDIDATE and NIGHTCAP_TEST_EQGAME for actual paired artifacts")
	}
	read := func(path string) []byte {
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	envelope := read(filepath.Join(root, "baseline-channel.json"))
	if manifest.Digest(envelope) != "a7b4235a6d2641224293d372b2f66a1f4d4c7e3e8bba1ac366455bab89409f44" {
		t.Fatal("baseline drift")
	}
	public, _ := hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266")
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.6.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(),
		Keys:          []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}},
		Retired:       map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true},
		RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	raw, sig, e := manifest.DecodeEnvelope(envelope)
	if e != nil {
		t.Fatal(e)
	}
	old, e := manifest.Verify(raw, sig, trust)
	if e != nil {
		t.Fatal(e)
	}
	if old.Release != 2026102601 || len(old.Files) != 141 {
		t.Fatal("unexpected signed inventory")
	}
	var candidate struct {
		Assets map[string]struct {
			SHA256 string
			Size   int64
		}
		Retained   []manifest.File      `json:"retained_descriptors"`
		Notes      []manifest.PatchNote `json:"retained_patch_notes"`
		Tombstones []string             `json:"retained_tombstones"`
		Count      int                  `json:"complete_inventory_count"`
	}
	if e = json.Unmarshal(read(filepath.Join(root, "candidate.json")), &candidate); e != nil {
		t.Fatal(e)
	}
	if len(candidate.Assets) != 3 || candidate.Count != 141 || !reflect.DeepEqual(candidate.Notes, old.PatchNotes) || !reflect.DeepEqual(candidate.Tombstones, old.Tombstones) {
		t.Fatal("history/inventory mismatch")
	}
	retained := []manifest.File{}
	for _, f := range old.Files {
		if _, replace := candidate.Assets[f.Path]; !replace {
			retained = append(retained, f)
		} else {
			b := read(filepath.Join(root, "baseline", filepath.FromSlash(f.Path)))
			if int64(len(b)) != f.Size || manifest.Digest(b) != f.SHA256 {
				t.Fatal("baseline bytes mismatch", f.Path)
			}
		}
	}
	if len(retained) != 138 || !reflect.DeepEqual(retained, candidate.Retained) {
		t.Fatal("retained inventory changed")
	}
	for path, pin := range candidate.Assets {
		b := read(filepath.Join(root, "assets", filepath.FromSlash(path)))
		if int64(len(b)) != pin.Size || manifest.Digest(b) != pin.SHA256 {
			t.Fatal("candidate drift", path)
		}
	}
	exe, e := os.Open(os.Getenv("NIGHTCAP_TEST_EQGAME"))
	if e != nil {
		t.Fatal(e)
	}
	defer exe.Close()
	for _, directory := range []string{"baseline", "assets"} {
		proxy := read(filepath.Join(root, directory, "dinput8.dll"))
		catalog := read(filepath.Join(root, directory, CatalogPath))
		config := read(filepath.Join(root, directory, ConfigPath))
		if e = CheckProxyCatalog(proxy, catalog); e != nil {
			t.Fatal(directory, e)
		}
		if _, e = CheckSignedOpen(exe, config, catalog); e != nil {
			t.Fatal(directory, e)
		}
	}
	if e = CheckProxyCatalog(read(filepath.Join(root, "assets", "dinput8.dll")), read(filepath.Join(root, "baseline", CatalogPath))); e == nil {
		t.Fatal("mixed old/new pair accepted")
	}
	t.Log("signed baseline, 141-file candidate, 138 retained descriptors/history and both actual runtime pairs verified")
}

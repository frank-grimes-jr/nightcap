// Run a copy in eq-launcher/cmd/native-qol-sign. Writes a local candidate only.
package main

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { b, err := os.ReadFile(path); must(err); return b }
func write(path string, b []byte) {
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	must(err)
	_, err = f.Write(b)
	must(err)
	must(f.Sync())
	must(f.Close())
}
func main() {
	previous := flag.String("previous", "", "fresh public signed channel")
	client := flag.String("client", "", "read-only pinned executable directory")
	baselineDir := flag.String("baseline-assets", "", "verified baseline public runtime assets")
	assets := flag.String("assets", "", "reviewed proxy, catalog and two skins")
	key := flag.String("key", "", "local signing seed, never uploaded")
	out := flag.String("output", "", "new exclusive candidate directory")
	flag.Parse()
	public, err := hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266")
	must(err)
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.7.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(),
		Keys:          []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}},
		Retired:       map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true},
		RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	baseline := read(*previous)
	if manifest.Digest(baseline) != "06204d6b88079c5a386c1e19eab750bdcdfdbdd6b8f2230374b10452811e2b4f" {
		panic("baseline drift")
	}
	raw, sig, err := manifest.DecodeEnvelope(baseline)
	must(err)
	old, err := manifest.Verify(raw, sig, trust)
	must(err)
	if old.Release != 2026112101 || len(old.Files) != 148 {
		panic("unexpected baseline")
	}

	// Check the retained runtime pair and signed config using actual installed bytes.
	for _, f := range old.Files {
		if f.Path != "dinput8.dll" && f.Path != preflight.CatalogPath && f.Path != preflight.ConfigPath {
			continue
		}
		b := read(filepath.Join(*baselineDir, filepath.FromSlash(f.Path)))
		if int64(len(b)) != f.Size || manifest.Digest(b) != f.SHA256 {
			panic("installed runtime drift: " + f.Path)
		}
	}
	proxy := read(filepath.Join(*baselineDir, "dinput8.dll"))
	catalog := read(filepath.Join(*baselineDir, preflight.CatalogPath))
	must(preflight.CheckProxyCatalog(proxy, catalog))
	exe, err := os.Open(filepath.Join(*client, "eqgame.exe"))
	must(err)
	defer exe.Close()
	config := read(filepath.Join(*baselineDir, preflight.ConfigPath))
	_, err = preflight.CheckSignedOpen(exe, config, catalog)
	must(err)
	pins := map[string]string{"dinput8.dll": "9bf8b95382d4210d76e458c478cf226d74b103c24a5675704d375a913e3a6428", "nightcap-patch-sites.json": "2d88adcc351afe9e1c9567d8760c720eab7f8115737b2c6ab0ca302bb9c1b358", "uifiles/nightcap/equi_itemdisplay.xml": "8d37558ea0fa4cb3eeece8bd636643afa10b94548d76483fb31a4ecefef71196", "uifiles/nightcap/equi_targetwindow.xml": "ec59307a3091696b6c3284c829615628131ad4814d522c708b5d6c0a7e11f60f"}
	replacements := map[string][]byte{}
	for name, digest := range pins {
		b := read(filepath.Join(*assets, name))
		if manifest.Digest(b) != digest {
			panic("Native window candidate drift: " + name)
		}
		replacements[name] = b
	}
	m := old
	m.Release = 2026112201
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
	m.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-11-22", Changes: []manifest.PatchChange{{Kind: "feature", Text: "Select an NPC to see its level and class. Inspect gear to compare each eligible slot, including both rings. Use the Notes tab to save a private reminder for an item. Fully exit EverQuest and press Play to update."}}}}, old.PatchNotes...)

	for _, name := range []string{"uifiles/nightcap/equi_itemdisplay.xml", "uifiles/nightcap/equi_targetwindow.xml"} {
		m.Files = append(m.Files, manifest.File{Path: name, Required: true})
	}
	changed := 0
	for i := range m.Files {
		f := &m.Files[i]
		if b, ok := replacements[f.Path]; ok {
			f.SHA256 = manifest.Digest(b)
			f.Size = int64(len(b))
			f.URL = "https://play.nightcapgame.org/release/2026112201/" + f.Path
			changed++
		}
	}
	if changed != 4 {
		panic("Native window replacement inventory mismatch")
	}
	if len(m.Files) != 150 {
		panic("complete inventory mismatch")
	}
	proxy = replacements["dinput8.dll"]
	catalog = replacements[preflight.CatalogPath]
	must(preflight.CheckProxyCatalog(proxy, catalog))
	_, err = preflight.CheckSignedOpen(exe, config, catalog)
	must(err)

	candidate, err := manifest.Canonical(m)
	must(err)
	seed := read(*key)
	if len(seed) != ed25519.SeedSize {
		panic("invalid signing seed")
	}
	private := ed25519.NewKeyFromSeed(seed)
	if !bytes.Equal(private.Public().(ed25519.PublicKey), public) {
		panic("wrong signing key")
	}
	signature := manifest.Signature{KeyID: trust.Keys[0].ID, Bytes: ed25519.Sign(private, candidate)}
	trust.HighestRelease = old.Release
	_, err = manifest.Verify(candidate, signature, trust)
	must(err)
	envelope, err := json.Marshal(manifest.Envelope{Manifest: candidate, Signature: signature})
	must(err)
	must(os.Mkdir(*out, 0700))
	write(filepath.Join(*out, "channel.json"), envelope)
	for name, b := range replacements {
		must(os.MkdirAll(filepath.Dir(filepath.Join(*out, name)), 0700))
		write(filepath.Join(*out, name), b)
	}
	write(filepath.Join(*out, "previous-channel.json"), baseline)
	notes, err := json.MarshalIndent(m.PatchNotes, "", "  ")
	must(err)
	write(filepath.Join(*out, "patch-notes.json"), append(notes, '\n'))

	receipt, err := json.MarshalIndent(map[string]any{"status": "signed_candidate_not_published", "release": m.Release, "previous_release": old.Release, "channel_sha256": manifest.Digest(envelope), "previous_channel_sha256": manifest.Digest(baseline), "archive_sha256": pins, "assets_preserved": 146, "changed_assets": 4, "unchanged_asset_urls_preserved": true, "signature": "verified against shipped production key", "candidate_proxy_catalog_pair": "passed", "exact_executable_preflight": "passed", "native_player_acceptance": "pending"}, "", "  ")
	must(err)
	write(filepath.Join(*out, "verification.json"), append(receipt, '\n'))
	fmt.Println(string(receipt))
}

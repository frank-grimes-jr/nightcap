// Run a temporary copy inside eq-launcher/cmd/sympathetic-sign. Writes a local candidate only.
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
	assets := flag.String("assets", "", "tested sympathetic spell and string overlays")
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
	if manifest.Digest(baseline) != "f254ffea77b2c9f60506c8cd8d89099b7a334ed63fcdf4df7b12747667b67554" {
		panic("baseline drift")
	}
	raw, sig, err := manifest.DecodeEnvelope(baseline)
	must(err)
	old, err := manifest.Verify(raw, sig, trust)
	must(err)
	if old.Release != 2026111202 || len(old.Files) != 148 {
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
	pins := map[string]string{"spells_us.txt": "63067836b4b903dab1804d15bf1a1f73502ddc998a1a8ab9fdd5675b2780498b", "dbstr_us.txt": "c8d8cc97e88a4256090e7c41192f909f6651b79e97b4f484140f3075b426501c"}
	replacements := map[string][]byte{}
	for name, digest := range pins {
		b := read(filepath.Join(*assets, name))
		if manifest.Digest(b) != digest {
			panic("Sympathetic overlay drift: " + name)
		}
		replacements[name] = b
	}
	m := old
	m.Release = 2026111301
	m.Expires = time.Date(2026, 12, 13, 0, 0, 0, 0, time.UTC)
	m.Files = append([]manifest.File(nil), old.Files...)
	m.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-11-13", Changes: []manifest.PatchChange{{Kind: "feature", Text: "Adds Sympathetic Strike I and Sympathetic Healing I to the Ascended Runed Lava Pendant and Ascended Moonstone Ring. Eligible casts add 5% of the largest direct hit or heal, up to 48. Fully exit EverQuest and press Play."}}}}, old.PatchNotes...)

	changed := 0
	for i := range m.Files {
		f := &m.Files[i]
		if b, ok := replacements[f.Path]; ok {
			f.SHA256 = manifest.Digest(b)
			f.Size = int64(len(b))
			f.URL = "https://play.nightcapgame.org/release/2026111301/" + f.Path
			changed++
		}
	}
	if changed != 2 {
		panic("Sympathetic replacement inventory mismatch")
	}
	if len(m.Files) != 148 {
		panic("complete inventory mismatch")
	}
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

	receipt, err := json.MarshalIndent(map[string]any{"status": "signed_candidate_not_published", "release": m.Release, "previous_release": old.Release, "channel_sha256": manifest.Digest(envelope), "previous_channel_sha256": manifest.Digest(baseline), "archive_sha256": pins, "assets_preserved": 146, "changed_assets": 2, "unchanged_asset_urls_preserved": true, "signature": "verified against shipped production key", "retained_proxy_catalog_pair": "passed", "exact_executable_preflight": "passed", "native_player_acceptance": "pending"}, "", "  ")
	must(err)
	write(filepath.Join(*out, "verification.json"), append(receipt, '\n'))
	fmt.Println(string(receipt))
}

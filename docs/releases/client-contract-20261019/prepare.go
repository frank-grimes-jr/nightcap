// Run a copy in eq-launcher/cmd/client-contract-repair. Writes a local candidate only.
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
	"nightcap/eq-launcher/internal/runtimehealth"
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
	client := flag.String("client", "", "read-only installed game directory")
	catalog := flag.String("catalog", "", "reviewed corrected catalog")
	health := flag.String("health", "", "recorded failed launch health (offline replay only)")
	key := flag.String("key", "", "local signing seed, never uploaded")
	out := flag.String("output", "", "new exclusive candidate directory")
	flag.Parse()
	public, err := hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266")
	must(err)
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.6.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(),
		Keys:          []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}},
		Retired:       map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true},
		RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	baseline := read(*previous)
	if manifest.Digest(baseline) != "4fd7087b9a1d255c19c5ce7e3a3529c67459b339e0acbdf7dcf9a038c7cc6242" {
		panic("baseline drift")
	}
	raw, sig, err := manifest.DecodeEnvelope(baseline)
	must(err)
	old, err := manifest.Verify(raw, sig, trust)
	must(err)
	if old.Release != 2026101802 || len(old.Files) != 138 {
		panic("unexpected baseline")
	}
	// Verify every retained asset against signed bytes before deriving the repair.
	for _, f := range old.Files {
		b := read(filepath.Join(*client, filepath.FromSlash(f.Path)))
		if int64(len(b)) != f.Size || manifest.Digest(b) != f.SHA256 {
			panic("installed asset drift: " + f.Path)
		}
	}
	proxy := read(filepath.Join(*client, "dinput8.dll"))
	priorCatalog := read(filepath.Join(*client, preflight.CatalogPath))
	fixed := read(*catalog)
	if manifest.Digest(fixed) != "2599919e5701d4b2dc43e569da72a3d99e503ae6f511f690d7a09fe581f1a8b4" {
		panic("corrected catalog drift")
	}
	if err := preflight.CheckProxyCatalog(proxy, priorCatalog); err == nil {
		panic("broken pair unexpectedly passes")
	}
	must(preflight.CheckProxyCatalog(proxy, fixed))
	exe, err := os.Open(filepath.Join(*client, "eqgame.exe"))
	must(err)
	defer exe.Close()
	config := read(filepath.Join(*client, preflight.ConfigPath))
	_, err = preflight.CheckSignedOpen(exe, config, fixed)
	must(err)
	// Replay only: identity comes from an old report, so this is never launch authority.
	healthBytes := read(*health)
	var record runtimehealth.Record
	must(json.Unmarshal(healthBytes, &record))
	oldPolicy, err := preflight.RuntimeForCatalog(priorCatalog)
	must(err)
	expected := runtimehealth.Expected{PID: record.PID, ProcessCreated: record.ProcessCreated, Nonce: record.Nonce, ConfigSHA256: manifest.Digest(config), Runtime: oldPolicy}
	_, err = runtimehealth.Validate(healthBytes, expected)
	if err == nil || err.Error() != "runtime health contract mismatch" {
		panic(fmt.Sprintf("unexpected reproduction: %v", err))
	}
	expected.Runtime, err = preflight.RuntimeForCatalog(fixed)
	must(err)
	_, err = runtimehealth.Validate(healthBytes, expected)
	must(err)
	m := old
	m.Release = 2026101901
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
	m.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-10-19", Changes: []manifest.PatchChange{{Kind: "fix", Text: "Fixed the runtime health contract mismatch that prevented Play after the latest update. The launcher installs the corrected client catalog automatically."}}}}, old.PatchNotes...)
	changed := 0
	for i := range m.Files {
		f := &m.Files[i]
		if f.Path == preflight.CatalogPath {
			f.SHA256 = manifest.Digest(fixed)
			f.Size = int64(len(fixed))
			f.URL = "https://play.nightcapgame.org/release/2026101901/" + f.Path
			changed++
		}
	}
	if changed != 1 {
		panic("catalog inventory mismatch")
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
	write(filepath.Join(*out, preflight.CatalogPath), fixed)
	notes, err := json.MarshalIndent(m.PatchNotes, "", "  ")
	must(err)
	write(filepath.Join(*out, "patch-notes.json"), append(notes, '\n'))
	receipt, err := json.MarshalIndent(map[string]any{"status": "signed_candidate_not_published", "release": m.Release, "previous_release": old.Release, "channel_sha256": manifest.Digest(envelope), "catalog_sha256": manifest.Digest(fixed), "catalog_size": len(fixed), "proxy_version": expected.Runtime.ProxyVersion, "verified_installed_assets": len(old.Files), "assets_preserved": 137, "changed_assets": []string{preflight.CatalogPath}, "unchanged_asset_urls_preserved": true, "signature": "verified against shipped production key", "exact_executable_preflight": "passed", "recorded_health_old_catalog": "runtime health contract mismatch", "recorded_health_corrected_catalog": "passed offline replay; not a new native launch", "native_player_acceptance": "pending"}, "", "  ")
	must(err)
	write(filepath.Join(*out, "verification.json"), append(receipt, '\n'))
	fmt.Println(string(receipt))
}

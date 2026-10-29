// Run a copy in eq-launcher/cmd/aa-level-sign. Writes a local candidate only.
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
	assets := flag.String("assets", "", "reviewed proxy and catalog")
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
	if manifest.Digest(baseline) != "eb09f02c097eed3ba35c97756ca00ce8cdbbe04453497aa376c6143cf8bb8c8e" {
		panic("baseline drift")
	}
	raw, sig, err := manifest.DecodeEnvelope(baseline)
	must(err)
	old, err := manifest.Verify(raw, sig, trust)
	must(err)
	if old.Release != 2026102803 || len(old.Files) != 141 {
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
	pins := map[string]string{"hateplaneb.s3d":"b5bfee1c99274509a2c15792c9bf2205670192fd5ca9e92e62db342af1fb9f8d","hateplaneb_obj.s3d":"0ae40c84f57e753dbe2ea681adbdb4e5eb7064d175e1d9a4cef80ab300df3fdb","hateplane.s3d":"4a6b1a7a3025c22bd5d28a97e9e4c8999000e572f6fb90c6e6aee527bc72e341","hateplane_obj.s3d":"cebcf37b783867778b50b68ce96ffa88651981284075de242f672818e12ea435","hateplane_chr.s3d":"217adb0e89fcff849696c592d6195f43afabbb3e56fa831baf18f78d8d7a962c","hateplaneb_chr.s3d":"83b5f0631e000478bb29de36ca257aa8f3889fd495109d1d8dc59a82a2c2cee3","hateplaneb_chr.txt":"3d38d5ca5e44af15f7e279b807b66eb64a295901a861dbe045c9736db4ed3902"}
replacements := map[string][]byte{}
	for name, digest := range pins {
		b := read(filepath.Join(*assets, name))
		if manifest.Digest(b) != digest {
			panic("Hate candidate drift: " + name)
		}
		replacements[name] = b
	}
	m := old
	m.Release = 2026102901
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
	m.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-10-29", Changes: []manifest.PatchChange{{Kind: "fix", Text: "New Plane of Hate dungeon runs use a ground-level layout with Nightcap encounters and loot preserved. Existing runs keep their original layout. Fully exit EQ and use Play to update before entering Hate. Owner gameplay QA is open."}}}}, old.PatchNotes...)

	for _, f := range old.Files { if _,ok:=replacements[f.Path];ok {panic("Unexpected existing Hate asset: "+f.Path)} }
 names:=[]string{"hateplane.s3d","hateplane_obj.s3d","hateplane_chr.s3d","hateplaneb.s3d","hateplaneb_obj.s3d","hateplaneb_chr.s3d","hateplaneb_chr.txt"}
 for _,name:=range names { b:=replacements[name]; m.Files=append(m.Files,manifest.File{Path:name,Required:true,Size:int64(len(b)),SHA256:manifest.Digest(b),URL:"https://play.nightcapgame.org/release/2026102901/"+name}) }
 if len(m.Files)!=148 {panic("Hate inventory mismatch")}
 must(preflight.CheckProxyCatalog(proxy,catalog))
 _,err=preflight.CheckSignedOpen(exe,config,catalog);must(err)
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
		must(os.MkdirAll(filepath.Dir(filepath.Join(*out,name)),0700))
		write(filepath.Join(*out, name), b)
	}
	write(filepath.Join(*out, "previous-channel.json"), baseline)
	notes, err := json.MarshalIndent(m.PatchNotes, "", "  ")
	must(err)
	write(filepath.Join(*out, "patch-notes.json"), append(notes, '\n'))

	receipt, err := json.MarshalIndent(map[string]any{"status": "signed_candidate_not_published", "release": m.Release, "previous_release": old.Release, "channel_sha256": manifest.Digest(envelope), "previous_channel_sha256": manifest.Digest(baseline), "archive_sha256": pins, "assets_preserved": 141, "changed_assets": 7, "unchanged_asset_urls_preserved": true, "signature": "verified against shipped production key", "candidate_proxy_catalog_pair": "passed", "exact_executable_preflight": "passed", "native_player_acceptance": "pending"}, "", "  ")
	must(err)
	write(filepath.Join(*out, "verification.json"), append(receipt, '\n'))
	fmt.Println(string(receipt))
}

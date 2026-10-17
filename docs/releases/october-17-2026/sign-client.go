// Run a copy inside eq-launcher so its internal manifest verifier is used.
package main

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"reflect"
	"time"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { b, e := os.ReadFile(path); must(e); return b }
func main() {
	assets := flag.String("assets", "", "three reviewed changed assets")
	previous := flag.String("previous", "", "verified baseline envelope")
	notes := flag.String("notes", "", "reviewed patch notes")
	key := flag.String("key", "", "existing private seed; never uploaded")
	output := flag.String("output", "", "exclusive new envelope output")
	flag.Parse()
	public, e := hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266")
	must(e)
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.6.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(),
		Keys:          []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}},
		Retired:       map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true},
		RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	raw, sig, e := manifest.DecodeEnvelope(read(*previous))
	must(e)
	old, e := manifest.Verify(raw, sig, trust)
	must(e)
	if old.Release != 2026101701 || len(old.Files) != 106 {
		panic("baseline changed")
	}
	var history []manifest.PatchNote
	must(json.Unmarshal(read(*notes), &history))
	if len(history) != len(old.PatchNotes)+1 || history[0].Release != 2026101702 || !reflect.DeepEqual(history[1:], old.PatchNotes) {
		panic("patch history drift")
	}
	m := old
	m.Release = 2026101702
	m.PatchNotes = history
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
	changed := map[string]bool{"dinput8.dll": true, "nightcap-patch-sites.json": true, "uifiles/nightcap/equi_aawindow.xml": true}
	count := 0
	for i := range m.Files {
		f := &m.Files[i]
		if changed[f.Path] {
			b := read(filepath.Join(*assets, filepath.FromSlash(f.Path)))
			f.Size = int64(len(b))
			f.SHA256 = manifest.Digest(b)
			count++
		}
		f.URL = fmt.Sprintf("https://play.nightcapgame.org/release/%d/%s", m.Release, f.Path)
	}
	if count != 3 {
		panic("changed asset inventory mismatch")
	}
	candidate, e := manifest.Canonical(m)
	must(e)
	trust.HighestRelease = old.Release
	{
		seed := read(*key)
		if len(seed) != ed25519.SeedSize {
			panic("invalid seed length")
		}
		private := ed25519.NewKeyFromSeed(seed)
		if !bytes.Equal(private.Public().(ed25519.PublicKey), public) {
			panic("wrong production signing key")
		}
		signature := manifest.Signature{KeyID: trust.Keys[0].ID, Bytes: ed25519.Sign(private, candidate)}
		_, e = manifest.Verify(candidate, signature, trust)
		must(e)
		envelope, e := json.Marshal(manifest.Envelope{Manifest: candidate, Signature: signature})
		must(e)
		f, e := os.OpenFile(*output, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		must(e)
		_, e = f.Write(envelope)
		must(e)
		must(f.Sync())
		must(f.Close())
		fmt.Printf("Signed paired gameplay release %d; retained %d managed paths with three changed assets and prior history\n", m.Release, len(m.Files))
		return
	}
}

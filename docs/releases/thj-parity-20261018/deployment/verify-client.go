// Run a copy inside eq-launcher to use the shipped manifest parser and policy.
package main

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"reflect"
	"time"
)

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func read(p string) []byte { b, e := os.ReadFile(p); must(e); return b }
func main() {
	previous := flag.String("previous", "", "previous signed channel")
	expected := flag.String("expected", "", "exact signed candidate")
	hosted := flag.Bool("hosted", false, "download and verify all hosted assets")
	flag.Parse()
	public, e := hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266")
	must(e)
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.6.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(), Keys: []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}}, Retired: map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true}, RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	verify := func(envelope []byte) manifest.Manifest {
		raw, sig, e := manifest.DecodeEnvelope(envelope)
		must(e)
		m, e := manifest.Verify(raw, sig, trust)
		must(e)
		return m
	}
	old := verify(read(*previous))
	trust.HighestRelease = old.Release
	envelope := read(*expected)
	candidate := verify(envelope)
	if old.Release != 2026101801 || candidate.Release != 2026101802 || len(candidate.Files) != 138 || !reflect.DeepEqual(candidate.PatchNotes[1:], old.PatchNotes) || !reflect.DeepEqual(candidate.Tombstones, old.Tombstones) {
		panic("release history/inventory drift")
	}
	before := map[string]manifest.File{}
	for _, f := range old.Files {
		before[f.Path] = f
	}
	pins :=map[string]string{
		"dinput8.dll":"9dd6ad400d7390f95c3af88ffe70a67c180368a213e13cc951cee20fefb63380",
		"spells_us.txt":"eb07544cd443e56d404900d5853d09625ccea899425bcab63dc9f07283f7ec61",
		"dbstr_us.txt":"88506405c5179b1d369d261290b415937729b6f05b4e1a845a3d4bcd63f1a421",
		"uifiles/nightcap/equi_inventory.xml":"518c000142b83ecd55e149123d4b8a69133f581e23deddf43e3932de3b67ab69",
		"uifiles/nightcap/equi_petinfowindow.xml":"07205a47f2117e3f13f68d1f512d05cd268f0821b17ba5a71fe6e8b8d7b4f95b",
	}
	seen := map[string]bool{}
	for _, f := range candidate.Files {
		seen[f.Path] = true
		if f.URL != "https://play.nightcapgame.org/release/2026101802/"+f.Path {
			panic("URL drift")
		}
		prior, ok := before[f.Path]
        if !ok || f.Required != prior.Required { panic("inventory drift") }
        if expected, changed := pins[f.Path]; changed {
            if f.SHA256 != expected { panic("paired asset mismatch") }
        } else if f.SHA256 != prior.SHA256 || f.Size != prior.Size { panic("unrelated asset changed: "+f.Path) }
	}
	for name := range before {
		if !seen[name] {
			panic("existing file removed")
		}
	}
	for name := range pins {
		if !seen[name] {
			panic("zone archive omitted")
		}
	}
	var total int64
	if *hosted {
		client := &http.Client{Timeout: 60 * time.Second, CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if req.URL.Scheme != "https" || req.URL.Host != "play.nightcapgame.org" || len(via) > 3 {
				return fmt.Errorf("unexpected redirect")
			}
			return nil
		}}
		download := func(url string, limit int64) []byte {
			req, e := http.NewRequest("GET", url, nil)
			must(e)
			req.Header.Set("Accept-Encoding", "identity")
			req.Header.Set("User-Agent", "NightcapLauncher/0.6.0")
			r, e := client.Do(req)
			must(e)
			defer r.Body.Close()
			if r.StatusCode != 200 {
				panic(fmt.Sprintf("HTTP %d: %s", r.StatusCode, url))
			}
			b, e := io.ReadAll(io.LimitReader(r.Body, limit+1))
			must(e)
			if int64(len(b)) > limit {
				panic("oversize response")
			}
			return b
		}
		live := download("https://play.nightcapgame.org/channel.json", manifest.MaxEnvelopeBytes)
		if !bytes.Equal(live, envelope) {
			panic("hosted envelope mismatch")
		}
		verify(live)
		for _, f := range candidate.Files {
			b := download(f.URL, f.Size)
			if int64(len(b)) != f.Size || manifest.Digest(b) != f.SHA256 {
				panic("hosted asset mismatch: " + f.Path)
			}
			total += f.Size
		}
	}
	must(json.NewEncoder(os.Stdout).Encode(map[string]any{"release": candidate.Release, "signature": "valid against shipped production key", "managed_files": len(candidate.Files), "changed_assets": 5, "existing_assets_preserved": 133, "history_preserved": true, "hosted": *hosted, "verified_bytes": total, "channel_sha256": manifest.Digest(envelope)}))
}

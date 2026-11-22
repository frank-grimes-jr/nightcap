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
	"nightcap/eq-launcher/internal/preflight"
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
	trust := manifest.Trust{ReleaseInventory: true, LauncherVersion: "0.7.0", Hosts: []string{"play.nightcapgame.org"}, Now: time.Now().UTC(), Keys: []manifest.Key{{ID: "production-4acb02e67aeb0b51", Public: public, NotBefore: time.Unix(1789862400, 0), NotAfter: time.Unix(1853020800, 0)}}, Retired: map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true}, RetiredSHA256: map[string]string{"nektulos.eqg": "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885", "lavastorm.eqg": "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
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
	if old.Release != 2026112101 || candidate.Release != 2026112201 || len(candidate.Files) != 150 || !reflect.DeepEqual(candidate.PatchNotes[1:], old.PatchNotes) || !reflect.DeepEqual(candidate.Tombstones, old.Tombstones) {
		panic("release history/inventory drift")
	}
	before := map[string]manifest.File{}
	for _, f := range old.Files {
		before[f.Path] = f
	}
	pins := map[string]string{"dinput8.dll": "9bf8b95382d4210d76e458c478cf226d74b103c24a5675704d375a913e3a6428", "nightcap-patch-sites.json": "2d88adcc351afe9e1c9567d8760c720eab7f8115737b2c6ab0ca302bb9c1b358", "uifiles/nightcap/equi_itemdisplay.xml": "8d37558ea0fa4cb3eeece8bd636643afa10b94548d76483fb31a4ecefef71196", "uifiles/nightcap/equi_targetwindow.xml": "ec59307a3091696b6c3284c829615628131ad4814d522c708b5d6c0a7e11f60f"}
	seen := map[string]bool{}
	for _, f := range candidate.Files {
		seen[f.Path] = true
		if pins[f.Path] != "" && f.URL != "https://play.nightcapgame.org/release/2026112201/"+f.Path {
			panic("URL drift")
		}
		prior, ok := before[f.Path]
		added := f.Path == "uifiles/nightcap/equi_itemdisplay.xml" || f.Path == "uifiles/nightcap/equi_targetwindow.xml"
		if ok == added || (ok && f.Required != prior.Required) || !f.Required {
			panic("inventory drift")
		}
		if expected, changed := pins[f.Path]; changed {
			if f.SHA256 != expected {
				panic("paired asset mismatch")
			}
		} else if f.SHA256 != prior.SHA256 || f.Size != prior.Size || f.URL != prior.URL {
			panic("unrelated asset changed: " + f.Path)
		}
	}
	for name := range before {
		if !seen[name] {
			panic("existing file removed")
		}
	}
	for name := range pins {
		if !seen[name] {
			panic("Native window asset omitted")
		}
	}
	var total int64
	paired := map[string][]byte{}
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
			req.Header.Set("User-Agent", "NightcapLauncher/0.7.0")
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
			if f.Path == "dbstr_us.txt" {
				if manifest.Digest(b) != before[f.Path].SHA256 {
					panic("retained client strings drift")
				}
			}
			total += f.Size
			if f.Path == "dinput8.dll" || f.Path == preflight.CatalogPath {
				paired[f.Path] = b
			}
		}
		must(preflight.CheckProxyCatalog(paired["dinput8.dll"], paired[preflight.CatalogPath]))
	}
	must(json.NewEncoder(os.Stdout).Encode(map[string]any{"release": candidate.Release, "signature": "valid against shipped production key", "managed_files": len(candidate.Files), "changed_assets": 4, "existing_assets_preserved": 146, "history_preserved": true, "hosted": *hosted, "verified_bytes": total, "channel_sha256": manifest.Digest(envelope)}))
}

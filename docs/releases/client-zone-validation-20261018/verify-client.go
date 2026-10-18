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
	if old.Release != 2026101702 || candidate.Release != 2026101801 || len(candidate.Files) != 138 || !reflect.DeepEqual(candidate.PatchNotes[1:], old.PatchNotes) || !reflect.DeepEqual(candidate.Tombstones, old.Tombstones) {
		panic("release history/inventory drift")
	}
	before := map[string]manifest.File{}
	for _, f := range old.Files {
		before[f.Path] = f
	}
	pins := map[string]string{
		"butcher.s3d":         "af504e71d3f3497b5eef037d86475ba96985b261d96f6469915e058e05308839",
		"butcher_obj.s3d":     "ad4c886395c9af7f3de17be1c1a24785e295f892097b8e5785eec670a089c047",
		"cazicthule.s3d":      "b4224fa40afd6ef8b02e292568bddc96e405fb90c2db3c0d0d893192b9407fbf",
		"cazicthule_obj.s3d":  "b2d858bc0ecca2a585a3f4a95243651799149889abeb2616f40ddec387ea74ea",
		"commons.s3d":         "3ce0a15467d0b4c4cd2292f443d895a957f5fdfdba84ca3771e52655d5b08346",
		"commons_obj.s3d":     "2963640a7f3886e7f13ff9bb0b35c056f76785737aab80067b13428d8080a536",
		"everfrost.s3d":       "f438cb1bbf1986f20f4dcd4e3d444c00fdf0e2a57aca980e6fc4879003024de3",
		"everfrost_obj.s3d":   "370746b01d23f99d3396194c1d583dba358a64420858afa3307ca2ac2dfb391d",
		"feerrott.s3d":        "c4002988cfcf4ce74bb1b16d151ed9196d36046d61fc5271aaa2b7366f4b7d8b",
		"feerrott_obj.s3d":    "393802aaaa6b3f14989e373f541849892831cb1897ab62d004a1045f59d29a5b",
		"freportw.s3d":        "6187e4284e8240b46b576ad48ffa3e693a1de70cf08545952749bf63df74149a",
		"freportw_obj.s3d":    "e84f0865a59f13bfa415360328a081507dbd0087f0a736e3deae8d8fcc34aba4",
		"gfaydark.s3d":        "078beb1b67436bd3e07ae49569f0662882ffe189ea25771dac4bd559d08167a3",
		"gfaydark_obj.s3d":    "5564f980f5fdf8829c79ace8902a3af536e0b6770e05ff477be16be0630edf1f",
		"innothule.s3d":       "91ed53a55bdc0dbc8feae474fcbcf967aa4631c9cf9ccf3aeef7cd0929548121",
		"innothule_obj.s3d":   "d776595e2462b90c32ea5824fdbe07fb9097e5dff8dc48a2464fb595ca342f2d",
		"misty.s3d":           "81c6d110d57a12deaa09867f70afdeb372c3cc2391792e9247497d919eefcf0b",
		"misty_obj.s3d":       "5ba51c7d40e070a4f5349b6a081cb314187587683461834ab82b3c9e0a5557b3",
		"nektulos.s3d":        "6cfb7612bfe2703242add44d7cff285a37e08423df8082fffe10ce3dd84c7f21",
		"nektulos_obj.s3d":    "980717cdf70834429ed9667c14321a93f15aa38f78e331e8b6a15938f626969c",
		"northkarana.s3d":     "faf2ac94ec9e70eb558e4c83b82a3cc14bdb90355ef0095a0bda43733a79b54d",
		"northkarana_obj.s3d": "bad348a7f1921d8cacf8917e39f029f8b6c64b7bcab2dfb326a65ec070c80f48",
		"nro.s3d":             "c4f36795a6a1b1b86c4f677644506980a368da7d3a3ec6e09a4cfa2169232d24",
		"nro_obj.s3d":         "4556f6986f68ae90b471a4df83f6e1431c8bfedb640de2bf4944f12069ac4d7c",
		"qey2hh1.s3d":         "4d2ab8f0d1f03678dbb75a62496102b97ca6c63dcc78b38e449608fdbeab2182",
		"qey2hh1_obj.s3d":     "b1bafa220125dbc8e8f7c59c262e7025ac2a0a65832857f6198291131e6309c2",
		"qeynos2.s3d":         "5d80aaa2a9c532b6867956e72aa67dfdd4731cbb87aaced238c15746ca97aefc",
		"qeynos2_obj.s3d":     "345d9a2631c9464592945ec5f536dfda4f3eb488a0fbeaab09a966fb3bdb11dc",
		"sro.s3d":             "4a32a8deeeaade31d020ac84402d6b6c4d6c0527ded4cbfbe3fc30b816819f8e",
		"sro_obj.s3d":         "f61cbe10f3b940a076bc08d95cbbda03b836638cb933fc410263ae10f8e81491",
		"steamfont.s3d":       "367b98b89f936dc3c18fdef5aff995ac966bb2c1ebfab0afb71ccae821281704",
		"steamfont_obj.s3d":   "41a715859be18d1c63a483a9b444fe69c1200395d08260d121492bed31533154",
		"tox.s3d":             "d6da558f0cb42bb664c0a4eb0b2bf7416ac2e609edb404c321f14c679a093dd2",
		"tox_obj.s3d":         "41632c745f01410a0cc6aef27f47bed312195e17ebdca403410df5dc687c1425",
	}
	seen := map[string]bool{}
	for _, f := range candidate.Files {
		seen[f.Path] = true
		if f.URL != "https://play.nightcapgame.org/release/2026101801/"+f.Path {
			panic("URL drift")
		}
		if prior, ok := before[f.Path]; ok {
			if f.Required != prior.Required || f.SHA256 != prior.SHA256 || f.Size != prior.Size {
				panic("existing asset changed: " + f.Path)
			}
		} else if expected, ok := pins[f.Path]; !ok || expected != f.SHA256 || !f.Required {
			panic("unexpected addition")
		}
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
	must(json.NewEncoder(os.Stdout).Encode(map[string]any{"release": candidate.Release, "signature": "valid against shipped production key", "managed_files": len(candidate.Files), "added_assets": 32, "existing_assets_preserved": 106, "history_preserved": true, "hosted": *hosted, "verified_bytes": total, "channel_sha256": manifest.Digest(envelope)}))
}

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
	"sort"
	"time"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { b, e := os.ReadFile(path); must(e); return b }
func main() {
	assets := flag.String("assets", "", "reviewed zone archive directory")
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
	if old.Release != 2026101702 || len(old.Files) != 106 {
		panic("baseline changed")
	}
	var history []manifest.PatchNote
	must(json.Unmarshal(read(*notes), &history))
	if len(history) != len(old.PatchNotes)+1 || history[0].Release != 2026101801 || !reflect.DeepEqual(history[1:], old.PatchNotes) {
		panic("patch history drift")
	}
	m := old
	m.Release = 2026101801
	m.PatchNotes = history
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
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
	for i := range m.Files {
		f := &m.Files[i]
		seen[f.Path] = true
		if expected, ok := pins[f.Path]; ok && f.SHA256 != expected {
			panic("existing zone archive differs")
		}
		f.URL = fmt.Sprintf("https://play.nightcapgame.org/release/%d/%s", m.Release, f.Path)
	}
	for name, expected := range pins {
		data := read(filepath.Join(*assets, name))
		if manifest.Digest(data) != expected {
			panic("zone archive source changed: " + name)
		}
		if seen[name] {
			continue
		}
		m.Files = append(m.Files, manifest.File{Path: name, Size: int64(len(data)), SHA256: expected, URL: fmt.Sprintf("https://play.nightcapgame.org/release/%d/%s", m.Release, name), Required: true})
	}
	sort.Slice(m.Files, func(i, j int) bool { return m.Files[i].Path < m.Files[j].Path })
	if len(m.Files) != 138 {
		panic("unexpected candidate inventory")
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
		fmt.Printf("Signed zone repair release %d; retained %d managed paths with preserved existing bytes and prior history\n", m.Release, len(m.Files))
		return
	}
}

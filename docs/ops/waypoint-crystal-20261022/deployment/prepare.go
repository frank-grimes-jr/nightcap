// Run a copy in eq-launcher/cmd/waypoint-sign. Writes a local candidate only.
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
	"sort"
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
	client := flag.String("client", "", "read-only installed game directory")
	assets := flag.String("assets", "", "reviewed five-file waypoint delta")
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
	if manifest.Digest(baseline) != "78e1173d2279ff185c883645f8c2d43e1d1454676bf696f8ac0b545d2e3174fa" {
		panic("baseline drift")
	}
	raw, sig, err := manifest.DecodeEnvelope(baseline)
	must(err)
	old, err := manifest.Verify(raw, sig, trust)
	must(err)
	if old.Release != 2026102201 || len(old.Files) != 138 {
		panic("unexpected baseline")
	}

	// Check the retained runtime pair and signed config using actual installed bytes.
	for _, f := range old.Files {
		if f.Path != "dinput8.dll" && f.Path != preflight.CatalogPath && f.Path != preflight.ConfigPath {
			continue
		}
		b := read(filepath.Join(*client, filepath.FromSlash(f.Path)))
		if int64(len(b)) != f.Size || manifest.Digest(b) != f.SHA256 {
			panic("installed runtime drift: " + f.Path)
		}
	}
	proxy := read(filepath.Join(*client, "dinput8.dll"))
	catalog := read(filepath.Join(*client, preflight.CatalogPath))
	must(preflight.CheckProxyCatalog(proxy, catalog))
	exe, err := os.Open(filepath.Join(*client, "eqgame.exe"))
	must(err)
	defer exe.Close()
	config := read(filepath.Join(*client, preflight.ConfigPath))
	_, err = preflight.CheckSignedOpen(exe, config, catalog)
	must(err)
	pins := map[string]string{"dinput8.dll": "013e2323cf4146db34760fbc93b1ed684841c0d11ed9df42d99d6c318a14a1df", "nightcap-patch-sites.json": "282eef8492f50153a3b14ef9dda78ad446c9e835d659d9a28b37681be30fc3ed", "crs.eqg": "0a06d4b41d49843b40518105b50057a50d1abb07147e10fb3769135ee1223f6b", "nightcap_models_chr.txt": "0f4a170e588cc9475a8abb57425406b87d49eb26c82a3839fa6907e8f15ce470", "nightcap_modern_chr.txt": "505533bcf05cb38eeb8f241ea942312ea28ad82813ce3559f5ff5dd994ff179f"}
	replacements := map[string][]byte{}
	for name, digest := range pins {
		b := read(filepath.Join(*assets, name))
		if manifest.Digest(b) != digest {
			panic("waypoint candidate drift: " + name)
		}
		replacements[name] = b
	}
	m := old
	m.Release = 2026102202
	m.Expires = time.Now().UTC().Add(30 * 24 * time.Hour).Truncate(time.Second)
	m.Files = append([]manifest.File(nil), old.Files...)
	m.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-10-22", Changes: []manifest.PatchChange{{Kind: "fix", Text: "Live testing: Waypoints now have a glowing crystal and waypoint label. Close EverQuest completely and use launcher Play to update both model modes. Discovery and recall locations are unchanged; native visibility QA remains open."}}}}, old.PatchNotes...)

	changed := 0
	for i := range m.Files {
		f := &m.Files[i]
		if b, ok := replacements[f.Path]; ok {
			f.SHA256 = manifest.Digest(b)
			f.Size = int64(len(b))
			f.URL = "https://play.nightcapgame.org/release/2026102202/" + f.Path
			changed++
		}
	}
	if changed != 3 {
		panic("waypoint replacement inventory mismatch")
	}
	for _, name := range []string{"crs.eqg", "nightcap_modern_chr.txt"} {
		for _, f := range old.Files {
			if f.Path == name {
				panic("new asset already exists")
			}
		}
		b := replacements[name]
		m.Files = append(m.Files, manifest.File{Path: name, SHA256: manifest.Digest(b), Size: int64(len(b)), URL: "https://play.nightcapgame.org/release/2026102202/" + name, Required: true})
	}
	sort.Slice(m.Files, func(i, j int) bool { return m.Files[i].Path < m.Files[j].Path })
	if len(m.Files) != 140 {
		panic("complete inventory mismatch")
	}
	contract := map[string]string{"crs.eqg": "0a06d4b41d49843b40518105b50057a50d1abb07147e10fb3769135ee1223f6b", "ncm01_chr.s3d": "8354da04868a47e6de06d589b61df5cfb92c0a7dc14ceff3e81bbd45c8c17876", "ncm02_chr.s3d": "2bb0a9a97f4cf7c85b66021683beb031adbe25446d522661f55d1f0b5232d9bc", "ncm03_chr.s3d": "ff94f5f28afffb7f06cb0ca886982321b31816684b013c67b5030f5eda6836ed", "ncm04_chr.s3d": "4ec905bb44602fa98bbcc3ba8c6675e8630e21fc9967ea44ae63518479341ddf", "ncm05_chr.s3d": "33af3aba6789a42895da0cccbf8691ccabe685799c554be7bcd1f9d58267d30d", "ncm06_chr.s3d": "3839329d014dbc47e0459cf7ddd21a3262c6f1c96b6408f15a0bca6b5d0c8969", "ncm07_chr.s3d": "9d3036ac7e10cc372990ce483e9f6f1a7a3059b2c0f3fd02381a74093e210cfb", "ncm08_chr.s3d": "6de3e2616da64e612e5e1e4bc92baefa67b3d81cf10b22f268c4705969f94561", "ncm09_chr.s3d": "c21aef7c21dc34a35b961e7e385f049dd9486f5b2aaf00b1420ab376db097a9e", "ncm10_chr.s3d": "870f1ae03bddfb6e7ee3cc25c7856f2fb5936feac9a9c57c35d8b284a9ac1dd9", "ncm11_chr.s3d": "537d7ec4538f0f677d309280d7202fceeae6acaf0ae12da63c25207c045f0315", "ncm12_chr.s3d": "a56b311bb69d78da2a00f59d9323c02e7b94b72f5c9ad40ac9cd3aab301e3684", "ncm13_chr.s3d": "08ba52a4977a2fc3b556218a0d0c63602068790e656879bd740f1ea1df08ba82", "ncm14_chr.s3d": "b760d7ba1376840042475f00d2d6f9dbb455078011325f83c7670724499b8490", "ncm15_chr.s3d": "52f79ac48bee996dd9fc62d627d58ece01c0a990f86c6abbdffa2112ab9eafbd", "ncm16_chr.s3d": "2d3efed794be6ae596bdbc6d0117c63707aeae6d11ad2163b4c747e13037452c", "ncm17_chr.s3d": "0baa44b9ef8e9b24142c4e85489b52563570af2c44f7ef553ab5372a736fa584", "ncm18_chr.s3d": "3034b915f8a80a0ab86994f67aed11a4361844773277ca6e3afd0dbeb02df584", "ncm19_chr.s3d": "2569098db84cfa12355aedb32be6069c890a4b9b35778a5082bb150a113ce643", "ncm20_chr.s3d": "fb6fd9f4f471a93cc9127b6a558a0bcbfb3b0c17dd2d4b6dc22454676e3ead34", "ncm21_chr.s3d": "a521a30f20128860fa4fb586e9218c1495bbdaebc3d3696ec53db69f8c59aafa", "ncm22_chr.s3d": "05456af2c2f738cab109392a273d73047bc7109e1a69532aa192ec8a92844f1f", "nightcap_models_chr.txt": "0f4a170e588cc9475a8abb57425406b87d49eb26c82a3839fa6907e8f15ce470", "nightcap_modern_chr.txt": "505533bcf05cb38eeb8f241ea942312ea28ad82813ce3559f5ff5dd994ff179f"}
	matched := 0
	for _, f := range m.Files {
		if expected, ok := contract[f.Path]; ok {
			if f.SHA256 != expected {
				panic("model contract mismatch: " + f.Path)
			}
			matched++
		}
	}
	if matched != 25 {
		panic("incomplete model contract")
	}
	must(preflight.CheckProxyCatalog(replacements["dinput8.dll"], replacements[preflight.CatalogPath]))
	_, err = preflight.CheckSignedOpen(exe, config, replacements[preflight.CatalogPath])
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
		write(filepath.Join(*out, name), b)
	}
	write(filepath.Join(*out, "previous-channel.json"), baseline)
	notes, err := json.MarshalIndent(m.PatchNotes, "", "  ")
	must(err)
	write(filepath.Join(*out, "patch-notes.json"), append(notes, '\n'))

	receipt, err := json.MarshalIndent(map[string]any{"status": "signed_candidate_not_published", "release": m.Release, "previous_release": old.Release, "channel_sha256": manifest.Digest(envelope), "previous_channel_sha256": manifest.Digest(baseline), "archive_sha256": pins, "assets_preserved": 135, "changed_assets": 5, "unchanged_asset_urls_preserved": true, "signature": "verified against shipped production key", "candidate_proxy_catalog_pair": "passed", "exact_executable_preflight": "passed", "native_player_acceptance": "pending"}, "", "  ")
	must(err)
	write(filepath.Join(*out, "verification.json"), append(receipt, '\n'))
	fmt.Println(string(receipt))
}

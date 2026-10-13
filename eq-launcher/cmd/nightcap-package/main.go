// nightcap-package assembles a signed, offline local QA build. Run from eq-launcher.
package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"go/format"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

const classicNektulosRetirementSHA256 = "de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885"
const classicLavastormRetirementSHA256 = "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"

func main() {
	client := flag.String("client", "", "supported eqgame.exe (read only)")
	assets := flag.String("assets", "", "generated gameplay asset directory")
	keyPath := flag.String("key", "", "private seed in an access-restricted directory outside source/package")
	newKey := flag.Bool("new-key", false, "create a fresh private seed exclusively; never replace")
	release := flag.Uint64("release", 0, "unique increasing QA release number")
	output := flag.String("output", "internal/launcher", "generated policy directory")
	profilePath := flag.String("production-profile", "", "reviewed production profile JSON; otherwise build offline QA")
	publish := flag.String("publish", "", "new directory for hosted production files")
	launcherExe := flag.String("launcher-exe", "", "sign this desktop EXE into a separate launcher channel instead of packaging game files")
	notesPath := flag.String("patch-notes", "", "reviewed JSON patch history to include in the signed game manifest")
	flag.Parse()
	profile, err := loadProfile(*profilePath, *publish)
	if err == nil {
		if *launcherExe != "" {
			err = buildLauncher(*launcherExe, *keyPath, *release, profile)
		} else {
			var notes []manifest.PatchNote
			notes, err = loadPatchNotes(*notesPath, *release)
			if err == nil {
				err = buildWithNotes(*client, *assets, *keyPath, *newKey, *release, *output, profile, notes)
			}
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func readBounded(path string, limit int64) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > limit {
		return nil, fmt.Errorf("invalid input size/type: %s", path)
	}
	data := make([]byte, info.Size()+1)
	n, err := f.ReadAt(data, 0)
	if (err != nil && err != io.EOF) || int64(n) != info.Size() {
		return nil, fmt.Errorf("input changed: %s", path)
	}
	return data[:n], nil
}

func privateKey(path string, create bool) (ed25519.PrivateKey, error) {
	if path == "" || !filepath.IsAbs(path) {
		return nil, fmt.Errorf("absolute private seed path required")
	}
	if create {
		seed := make([]byte, ed25519.SeedSize)
		if _, err := rand.Read(seed); err != nil {
			return nil, err
		}
		f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			return nil, err
		}
		_, err = f.Write(seed)
		err = errors.Join(err, f.Sync(), f.Close())
		if err != nil {
			return nil, err
		}
	}
	seed, err := readBounded(path, ed25519.SeedSize)
	if err != nil {
		return nil, err
	}
	if len(seed) != ed25519.SeedSize {
		return nil, fmt.Errorf("invalid private seed length")
	}
	return ed25519.NewKeyFromSeed(seed), nil
}

func build(client, assets, keyPath string, create bool, release uint64, output string) error {
	return buildConfigured(client, assets, keyPath, create, release, output, nil)
}

func buildConfigured(client, assets, keyPath string, create bool, release uint64, output string, profile *productionProfile) error {
	return buildWithNotes(client, assets, keyPath, create, release, output, profile, nil)
}

func buildWithNotes(client, assets, keyPath string, create bool, release uint64, output string, profile *productionProfile, notes []manifest.PatchNote) error {
	if err := manifest.ValidatePatchNotes(notes, release); err != nil {
		return err
	}
	if len(notes) > 0 && profile != nil && !manifest.SupportsPatchNotes(profile.Version) {
		return fmt.Errorf("patch notes require desktop version 0.6.0 or newer")
	}
	if client == "" || release == 0 {
		return fmt.Errorf("client and nonzero release required")
	}
	names := []string{"dinput8.dll", "nightcap-bootstrap.exe", preflight.ConfigPath, preflight.CatalogPath}
	paths := []string{"../eq-client-dll/build/dinput8.dll", "../eq-client-dll/build/nightcap-bootstrap.exe", "../eq-client-dll/config/nightcap-patches.cfg", "../eq-client-dll/config/patch-sites.json"}
	data := map[string][]byte{}
	for i, name := range names {
		raw, err := readBounded(paths[i], manifest.MaxFileBytes)
		if err != nil {
			return err
		}
		data[name] = raw
	}
	gameplay, err := loadGameplayAssets(assets, client)
	if err != nil {
		return err
	}
	if err = validateClassicModels(gameplay); err != nil {
		return err
	}
	for _, name := range gameplayNames {
		names = append(names, name)
		data[name] = gameplay[name]
	}
	exe, err := os.Open(client)
	if err != nil {
		return err
	}
	defer exe.Close()
	report, err := preflight.CheckOpen(exe, data[preflight.ConfigPath], data[preflight.CatalogPath])
	if err != nil {
		return err
	}
	// Validate the very bytes to be published, rather than reopening mutable inputs.
	temp, err := os.MkdirTemp("", "nightcap-package-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(temp)
	for _, name := range names[:2] {
		if err = os.WriteFile(filepath.Join(temp, name), data[name], 0600); err != nil {
			return err
		}
	}
	proxy, err := os.Open(filepath.Join(temp, names[0]))
	if err != nil {
		return err
	}
	defer proxy.Close()
	boot, err := preflight.BootstrapOpen(exe, proxy)
	if err != nil {
		return err
	}
	helper, err := os.Open(filepath.Join(temp, names[1]))
	if err != nil {
		return err
	}
	defer helper.Close()
	if err = preflight.CheckHelperOpen(helper); err != nil {
		return err
	}
	private, err := privateKey(keyPath, create)
	if err != nil {
		return err
	}
	public := private.Public().(ed25519.PublicKey)
	now := time.Now().UTC().Truncate(time.Second)
	key := manifest.Key{ID: "local-qa-" + manifest.Digest(public)[:16], Public: public, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(90 * 24 * time.Hour)}
	baseURL, version := "https://qa.nightcap.invalid", "0.1.0"
	if len(notes) > 0 {
		version = manifest.PatchNotesMinimumLauncher
	}
	hosts := []string{"qa.nightcap.invalid"}
	if profile != nil {
		key = manifest.Key{ID: "production-" + manifest.Digest(public)[:16], Public: public, NotBefore: profile.KeyNotBefore, NotAfter: profile.KeyNotAfter}
		baseURL, version, hosts = profile.BaseURL, profile.Version, profile.hosts()
		if now.Before(key.NotBefore) || !now.Add(30*24*time.Hour).Before(key.NotAfter) {
			return fmt.Errorf("production key must cover the whole release lifetime")
		}
	}
	trust := manifest.Trust{Keys: []manifest.Key{key}, Now: now, LauncherVersion: "0.1.0", Hosts: []string{"qa.nightcap.invalid"}, Inventory: map[string]bool{}, Retired: map[string]bool{"nektulos.eqg": true, "lavastorm.eqg": true}, RetiredSHA256: map[string]string{"nektulos.eqg": classicNektulosRetirementSHA256, "lavastorm.eqg": classicLavastormRetirementSHA256}}
	m := manifest.Manifest{Schema: 1, Release: release, MinLauncher: "0.1.0", Expires: now.Add(30 * 24 * time.Hour), Tombstones: []string{"nektulos.eqg", "lavastorm.eqg"}, PatchNotes: notes}
	trust.Keys, trust.Hosts, trust.LauncherVersion = []manifest.Key{key}, hosts, version
	m.MinLauncher = version
	if profile != nil {
		trust.ReleaseInventory = true
		m.MinLauncher = loadingScreensMinimumLauncher
		if profile.MinLauncher != "" {
			m.MinLauncher = profile.MinLauncher
		}
	}

	if len(notes) > 0 && !manifest.SupportsPatchNotes(m.MinLauncher) {
		m.MinLauncher = manifest.PatchNotesMinimumLauncher
	}
	for _, name := range names {
		trust.Inventory[name] = true
		m.Files = append(m.Files, manifest.File{Path: name, SHA256: manifest.Digest(data[name]), Size: int64(len(data[name])), URL: fmt.Sprintf("%s/release/%d/%s", baseURL, release, name), Required: true})
	}
	raw, err := manifest.Canonical(m)
	if err != nil {
		return err
	}
	sig := manifest.Signature{KeyID: key.ID, Bytes: ed25519.Sign(private, raw)}
	if _, err = manifest.Verify(raw, sig, trust); err != nil {
		return err
	}
	if profile != nil {
		return publishProduction(profile, output, key, m, raw, sig, data)
	}
	signature, err := json.Marshal(sig)
	if err != nil {
		return err
	}
	source, err := policySource(key, release, names, version)
	if err != nil {
		return err
	}
	bundle := filepath.Join(output, "qabundle")
	// Exclusive creation prevents accidental reuse or mixing generations.
	if err = os.Mkdir(bundle, 0700); err != nil {
		return err
	}
	if err = os.Mkdir(filepath.Join(bundle, "files"), 0700); err != nil {
		return err
	}
	for _, name := range names {
		target := filepath.Join(bundle, "files", filepath.FromSlash(name))
		if err = os.MkdirAll(filepath.Dir(target), 0700); err != nil {
			return err
		}
		if err = os.WriteFile(target, data[name], 0600); err != nil {
			return err
		}
	}
	if err = os.WriteFile(filepath.Join(bundle, "manifest.json"), raw, 0600); err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(bundle, "signature.json"), signature, 0600); err != nil {
		return err
	}
	audit, err := json.MarshalIndent(map[string]any{"release": release, "created": now, "expires": m.Expires, "key_id": key.ID, "public_key": hex.EncodeToString(public), "public_key_sha256": manifest.Digest(public), "manifest_sha256": manifest.Digest(raw), "files": m.Files, "preflight": report, "bootstrap": boot, "scope": "LOCAL QA CANDIDATE; package signature is not Windows Authenticode or gameplay acceptance"}, "", "  ")
	if err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(bundle, "audit.json"), audit, 0600); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(output, "policy_qa_generated.go"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	_, err = f.Write(source)
	if err = errors.Join(err, f.Close()); err != nil {
		return err
	}
	fmt.Printf("Signed QA release %d; %d verified patch sites; public key %s\n", release, report.SitesVerified, key.ID)
	return nil
}

func policySource(key manifest.Key, release uint64, names []string, version string) ([]byte, error) {
	var inventory strings.Builder
	for _, name := range names {
		fmt.Fprintf(&inventory, "%q:true,", name)
	}
	source := fmt.Sprintf(`//go:build qacandidate

// Code generated by nightcap-package. DO NOT EDIT.
package launcher
import ("embed"; "io/fs"; "time"; "encoding/hex"; "nightcap/eq-launcher/internal/manifest")
//go:embed qabundle/manifest.json qabundle/signature.json qabundle/files/*
var qaBundle embed.FS
func DefaultPolicy() Policy {
 bundle, err := fs.Sub(qaBundle,"qabundle"); if err != nil { panic(err) }
 public, err := hex.DecodeString(%q); if err != nil { panic(err) }
 return Policy{Bundle:bundle, Label:"LOCAL QA CANDIDATE", EnablePlay:true, Trust:manifest.Trust{
 LauncherVersion:%q, Hosts:[]string{"qa.nightcap.invalid"},
 Keys:[]manifest.Key{{ID:%q,Public:public,NotBefore:time.Unix(%d,0),NotAfter:time.Unix(%d,0)}},
 Inventory:map[string]bool{%s}, Retired:map[string]bool{"nektulos.eqg":true,"lavastorm.eqg":true}, RetiredSHA256:map[string]string{"nektulos.eqg":%q,"lavastorm.eqg":%q},
 }}
}
// Embedded release: %d
`, hex.EncodeToString(key.Public), version, key.ID, key.NotBefore.Unix(), key.NotAfter.Unix(), inventory.String(), classicNektulosRetirementSHA256, classicLavastormRetirementSHA256, release)
	return format.Source([]byte(source))
}

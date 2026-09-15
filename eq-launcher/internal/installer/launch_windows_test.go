package installer

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/launchlock"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

type launchFixture struct {
	dir   string
	m     manifest.Manifest
	trust manifest.Trust
	key   ed25519.PrivateKey
}

func newLaunchFixture(t *testing.T) *launchFixture {
	t.Helper()
	pub, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	f := &launchFixture{dir: t.TempDir(), key: key, m: manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Tombstones: []string{"old.dll"}}, trust: manifest.Trust{Keys: []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-24 * time.Hour), NotAfter: now.Add(24 * time.Hour)}}, Now: now, LauncherVersion: "0.1.0", HighestRelease: 1, Inventory: map[string]bool{}, Retired: map[string]bool{"old.dll": true}, Hosts: []string{"release.test"}}}
	config, err := os.ReadFile("../../../eq-client-dll/config/nightcap-patches.cfg")
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range []struct {
		name     string
		data     []byte
		required bool
	}{
		{"dinput8.dll", []byte("fixture signed proxy bytes"), true},
		{preflight.ConfigPath, config, true},
		{preflight.CatalogPath, preflight.Catalog(), true},
		{"uifiles/nightcap/window.xml", []byte("fixture UI"), false},
		{HelperPath, []byte("fixture helper bytes"), true},
	} {
		put(t, f.dir, item.name, string(item.data))
		f.m.Files = append(f.m.Files, manifest.File{Path: item.name, Size: int64(len(item.data)), SHA256: manifest.Digest(item.data), URL: "https://release.test/" + item.name, Required: item.required})
		f.trust.Inventory[item.name] = item.required
	}
	put(t, f.dir, "eqgame.exe", "unsupported fixture executable")
	put(t, f.dir, "eqclient.ini", "user settings")
	f.sign(t)
	return f
}
func (f *launchFixture) sign(t *testing.T) {
	t.Helper()
	raw, err := manifest.Canonical(f.m)
	if err != nil {
		t.Fatal(err)
	}
	a := activeRecord{Release: f.m.Release, ManifestDigest: manifest.Digest(raw), Manifest: raw, Signature: manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(f.key, raw)}}
	data, err := json.Marshal(a)
	if err != nil {
		t.Fatal(err)
	}
	put(t, f.dir, ".nightcap/active.json", string(data))
}
func (f *launchFixture) changeSigned(t *testing.T, name, value string) {
	t.Helper()
	put(t, f.dir, name, value)
	for i := range f.m.Files {
		if f.m.Files[i].Path == name {
			f.m.Files[i].Size = int64(len(value))
			f.m.Files[i].SHA256 = manifest.Digest([]byte(value))
		}
	}
	f.sign(t)
}
func TestLockedGenerationRejectsInvalidRelease(t *testing.T) {
	cases := []struct {
		name, want string
		change     func(*testing.T, *launchFixture)
	}{
		{"pending", "recovery", func(t *testing.T, f *launchFixture) { put(t, f.dir, ".nightcap/pending.json", "malformed journal") }},
		{"missing checkpoint", "", func(t *testing.T, f *launchFixture) {
			if err := os.Remove(filepath.Join(f.dir, ".nightcap/active.json")); err != nil {
				t.Fatal(err)
			}
		}},
		{"corrupt checkpoint", "", func(t *testing.T, f *launchFixture) { put(t, f.dir, ".nightcap/active.json", "{}") }},
		{"bad signature", "signature", func(t *testing.T, f *launchFixture) { f.key[0] ^= 1; f.key[32] ^= 1; f.sign(t) }},
		{"expired release", "expired", func(t *testing.T, f *launchFixture) { f.trust.Now = f.trust.Now.Add(2 * time.Hour) }},
		{"downgrade", "downgrade", func(t *testing.T, f *launchFixture) { f.trust.HighestRelease = 3 }},
		{"same ID different digest", "reused", func(t *testing.T, f *launchFixture) {
			f.trust.HighestRelease = 2
			f.trust.HighestDigest = strings.Repeat("0", 64)
		}},
		{"tampered asset", "hash mismatch", func(t *testing.T, f *launchFixture) { put(t, f.dir, "uifiles/nightcap/window.xml", "changed UI") }},
		{"longer asset", "size", func(t *testing.T, f *launchFixture) {
			put(t, f.dir, "dinput8.dll", "fixture signed proxy bytes plus extra")
		}},
		{"missing optional asset", "", func(t *testing.T, f *launchFixture) {
			if err := os.Remove(filepath.Join(f.dir, "uifiles/nightcap/window.xml")); err != nil {
				t.Fatal(err)
			}
		}},
		{"retired file", "absent", func(t *testing.T, f *launchFixture) { put(t, f.dir, "old.dll", "old plugin") }},
		{"empty trust", "unknown key", func(t *testing.T, f *launchFixture) { f.trust.Keys = nil }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newLaunchFixture(t)
			tc.change(t, f)
			lease, err := PrepareLaunch(context.Background(), f.dir, f.trust)
			if err == nil || lease != nil || (tc.want != "" && !strings.Contains(err.Error(), tc.want)) {
				if lease != nil {
					lease.Close()
				}
				t.Fatalf("expected %q rejection: %v", tc.want, err)
			}
			for _, name := range []string{"eqgame.exe", ".nightcap/active.json", "dinput8.dll"} {
				if err := os.WriteFile(filepath.Join(f.dir, name), []byte("after rejection"), 0600); err != nil {
					t.Fatal("rejected generation leaked lock:", err)
				}
			}
		})
	}
}
func TestLockedGenerationRetainsCheckpointAndEveryAsset(t *testing.T) {
	f := newLaunchFixture(t)
	locks, err := launchlock.Acquire(f.dir)
	if err != nil {
		t.Fatal(err)
	}
	defer locks.Close()
	lease, m, err := verifyLaunchGeneration(context.Background(), locks, f.trust)
	if err != nil {
		t.Fatal(err)
	}
	if lease.Release() != 2 || len(m.Files) != 5 || lease.Proxy() == nil {
		t.Fatal("wrong lease")
	}
	names := []string{"eqgame.exe", ".nightcap/active.json"}
	for _, entry := range m.Files {
		names = append(names, entry.Path)
	}
	for _, name := range names {
		if err := os.WriteFile(filepath.Join(f.dir, filepath.FromSlash(name)), []byte("mutation"), 0600); err == nil {
			t.Fatal("verified file writable:", name)
		}
	}
}
func TestPrepareLaunchRejectsPreflightAndReleasesLocks(t *testing.T) {
	cases := []struct {
		name, want string
		change     func(*testing.T, *launchFixture)
	}{
		{"unsupported executable", "", func(t *testing.T, f *launchFixture) {}},
		{"disabled required hook", "required patch configuration disabled", func(t *testing.T, f *launchFixture) {
			b, err := os.ReadFile(filepath.Join(f.dir, preflight.ConfigPath))
			if err != nil {
				t.Fatal(err)
			}
			f.changeSigned(t, preflight.ConfigPath, strings.Replace(string(b), "equipment=1", "equipment=0", 1))
		}},
		{"wrong catalog", "catalog", func(t *testing.T, f *launchFixture) { f.changeSigned(t, preflight.CatalogPath, "{}") }},
		{"missing required config", "preflight asset", func(t *testing.T, f *launchFixture) {
			f.m.Files[1].Required = false
			f.trust.Inventory[preflight.ConfigPath] = false
			f.sign(t)
		}},
		{"optional helper", "required bootstrap helper", func(t *testing.T, f *launchFixture) {
			f.m.Files[4].Required = false
			f.trust.Inventory[HelperPath] = false
			f.sign(t)
		}},
		{"missing helper inventory", "required bootstrap helper", func(t *testing.T, f *launchFixture) {
			f.m.Files = f.m.Files[:4]
			delete(f.trust.Inventory, HelperPath)
			f.sign(t)
		}},
		{"optional proxy", "required proxy", func(t *testing.T, f *launchFixture) {
			f.m.Files[0].Required = false
			f.trust.Inventory["dinput8.dll"] = false
			f.sign(t)
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newLaunchFixture(t)
			tc.change(t, f)
			lease, err := PrepareLaunch(context.Background(), f.dir, f.trust)
			if err == nil || lease != nil || (tc.want != "" && !strings.Contains(err.Error(), tc.want)) {
				if lease != nil {
					lease.Close()
				}
				t.Fatalf("expected %q: %v", tc.want, err)
			}
			for _, name := range []string{"eqgame.exe", ".nightcap/active.json", "dinput8.dll", preflight.ConfigPath} {
				if err := os.WriteFile(filepath.Join(f.dir, name), []byte("after failure"), 0600); err != nil {
					t.Fatal("failed preparation leaked lock:", err)
				}
			}
		})
	}
}
func TestLaunchCancellation(t *testing.T) {
	f := newLaunchFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if lease, err := PrepareLaunch(ctx, f.dir, f.trust); lease != nil || !errors.Is(err, context.Canceled) {
		t.Fatalf("cancellation: %v", err)
	}
	locks, err := launchlock.Acquire(f.dir)
	if err != nil {
		t.Fatal(err)
	}
	defer locks.Close()
	if lease, _, err := verifyLaunchGeneration(ctx, locks, f.trust); lease != nil || !errors.Is(err, context.Canceled) {
		t.Fatalf("generation cancellation: %v", err)
	}
	r := contextReader{ctx, strings.NewReader("data")}
	var b [8]byte
	if n, err := r.Read(b[:]); n != 0 || !errors.Is(err, context.Canceled) {
		t.Fatal("hash read ignored cancellation")
	}
}
func TestPrepareLaunchSupportedClientOffline(t *testing.T) {
	source, proxySource, helperSource := os.Getenv("NIGHTCAP_TEST_EQGAME"), os.Getenv("NIGHTCAP_TEST_PROXY"), os.Getenv("NIGHTCAP_TEST_HELPER")
	if source == "" || proxySource == "" || helperSource == "" {
		t.Skip("set NIGHTCAP_TEST_EQGAME, NIGHTCAP_TEST_PROXY and NIGHTCAP_TEST_HELPER for disposable copies; never executes the game")
	}
	data, err := os.ReadFile(source)
	if err != nil {
		t.Fatal(err)
	}
	f := newLaunchFixture(t)
	put(t, f.dir, "eqgame.exe", string(data))
	proxy, err := os.ReadFile(proxySource)
	if err != nil {
		t.Fatal(err)
	}
	f.changeSigned(t, "dinput8.dll", string(proxy))
	helper, err := os.ReadFile(helperSource)
	if err != nil {
		t.Fatal(err)
	}
	f.changeSigned(t, HelperPath, string(helper))
	lease, err := PrepareLaunch(context.Background(), f.dir, f.trust)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Close()
	metadata := lease.Bootstrap()
	if metadata.EntryRVA != 0x4e3b4a || metadata.EntryOriginal != 0xe8 || metadata.InitializerRVA == 0 || metadata.ProxyImageSize <= metadata.InitializerRVA {
		t.Fatalf("incorrect bootstrap metadata: %+v", metadata)
	}
	metadata.EntryRVA = 0
	if lease.Bootstrap().EntryRVA == 0 {
		t.Fatal("caller mutated lease metadata")
	}
	config, err := os.ReadFile(filepath.Join(f.dir, preflight.ConfigPath))
	if err != nil {
		t.Fatal(err)
	}
	if lease.ConfigDigest() != manifest.Digest(config) || lease.ManifestDigest() == "" || lease.Directory() != f.dir {
		t.Fatal("incorrect lease metadata")
	}
	if err := os.WriteFile(filepath.Join(f.dir, "eqclient.ini"), []byte("user change"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := lease.Close(); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(f.dir, "eqgame.exe"), []byte("after close"), 0600); err != nil {
		t.Fatal("successful lease leaked:", err)
	}
}

func TestPrepareLaunchRejectsSignedInvalidProxy(t *testing.T) {
	source := os.Getenv("NIGHTCAP_TEST_EQGAME")
	if source == "" {
		t.Skip("set NIGHTCAP_TEST_EQGAME for a disposable copy; no execution")
	}
	data, err := os.ReadFile(source)
	if err != nil {
		t.Fatal(err)
	}
	f := newLaunchFixture(t)
	put(t, f.dir, "eqgame.exe", string(data))
	lease, err := PrepareLaunch(context.Background(), f.dir, f.trust)
	if lease != nil || err == nil || !strings.Contains(err.Error(), "bootstrap PE") {
		if lease != nil {
			lease.Close()
		}
		t.Fatalf("signed non-PE proxy accepted: %v", err)
	}
	for _, name := range []string{"eqgame.exe", "dinput8.dll", ".nightcap/active.json"} {
		if err := os.WriteFile(filepath.Join(f.dir, name), []byte("after failure"), 0600); err != nil {
			t.Fatal("bootstrap validation leaked lock:", err)
		}
	}
}

package launcher

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"errors"
	"path/filepath"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
)

func fixture(t *testing.T) (*Controller, []byte, manifest.Signature) {
	t.Helper()
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Files: []manifest.File{{Path: "dinput8.dll", Size: 3, SHA256: manifest.Digest([]byte("dll")), URL: "https://release.test/dinput8.dll", Required: true}}, Tombstones: []string{}}
	raw, err := manifest.Canonical(m)
	if err != nil {
		t.Fatal(err)
	}
	sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, raw)}
	policy := Policy{ManifestURL: "https://release.test/manifest.json", SignatureURL: "https://release.test/signature.json", Trust: manifest.Trust{Keys: []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour)}}, LauncherVersion: "0.1.0", Inventory: map[string]bool{"dinput8.dll": true}, Hosts: []string{"release.test"}}}
	c, err := New(t.TempDir(), policy)
	if err != nil {
		t.Fatal(err)
	}
	c.probe = func(string) (client.Report, error) { return client.Report{Supported: true}, nil }
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { return raw, sig, nil }
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{}, nil
	}
	c.diff = func(context.Context, []byte, manifest.Signature, manifest.Trust, string) (assets.Diff, error) {
		return assets.Diff{Files: []assets.FileStatus{{Path: "dinput8.dll", State: assets.Missing}}}, nil
	}
	if err = c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	return c, raw, sig
}
func TestInitialStateAndPreviewPolicy(t *testing.T) {
	home := t.TempDir()
	c, err := New(home, Policy{})
	if err != nil {
		t.Fatal(err)
	}
	if s := c.Snapshot(); s.CanPlay || s.CanUpdate || s.Busy || s.ClientDir != "" {
		t.Fatalf("unsafe initial state %+v", s)
	}
	c.probe = func(string) (client.Report, error) { return client.Report{Supported: true}, nil }
	folder := t.TempDir()
	if err = c.SelectClient(context.Background(), folder); err != nil {
		t.Fatal(err)
	}
	if s := c.Snapshot(); s.Phase != "preview" || s.CanUpdate || s.CanPlay {
		t.Fatalf("unconfigured release enabled: %+v", s)
	}
	again, err := New(home, Policy{})
	if err != nil {
		t.Fatal(err)
	}
	if again.Snapshot().ClientDir != folder {
		t.Fatal("client selection not persisted")
	}
}
func TestSignedCheckAndUpdateDispatch(t *testing.T) {
	c, _, _ := fixture(t)
	staged, installed := 0, 0
	c.stage = func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error) {
		staged++
		return assets.Generation{Directory: filepath.Join(t.TempDir(), "candidate"), Release: 2}, nil
	}
	c.install = func(context.Context, string, string, manifest.Trust) (installer.Result, error) {
		installed++
		return installer.Result{Release: 2, ManifestDigest: "verified"}, nil
	}
	if err := c.Check(context.Background()); err != nil {
		t.Fatal(err)
	}
	if s := c.Snapshot(); !s.CanUpdate || s.Release != 2 || s.CanPlay {
		t.Fatalf("bad checked state: %+v", s)
	}
	if err := c.Update(context.Background()); err != nil {
		t.Fatal(err)
	}
	if s := c.Snapshot(); len(s.Files) != 1 || s.Files[0].State != assets.Current || len(s.Remove) != 0 {
		t.Fatalf("stale inventory after installation: %+v", s)
	}
	if staged != 1 || installed != 1 || c.Snapshot().CanPlay || c.Snapshot().Phase != "health_pending" {
		t.Fatalf("wrong dispatch/result: %d %d %+v", staged, installed, c.Snapshot())
	}
}
func TestUpdateReverifiesMetadata(t *testing.T) {
	c, raw, sig := fixture(t)
	if err := c.Check(context.Background()); err != nil {
		t.Fatal(err)
	}
	raw[0] ^= 1
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { return raw, sig, nil }
	c.stage = func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error) {
		t.Fatal("unverified bytes staged")
		return assets.Generation{}, nil
	}
	if err := c.Update(context.Background()); err == nil {
		t.Fatal("tampered release accepted")
	}
	if s := c.Snapshot(); s.CanUpdate || s.CanPlay || s.Busy {
		t.Fatalf("stale UI permission: %+v", s)
	}
}
func TestConcurrentActionsAndCancellation(t *testing.T) {
	c, _, _ := fixture(t)
	entered := make(chan struct{})
	done := make(chan error, 1)
	c.fetch = func(ctx context.Context, _ Policy) ([]byte, manifest.Signature, error) {
		close(entered)
		<-ctx.Done()
		return nil, manifest.Signature{}, ctx.Err()
	}
	go func() { done <- c.Check(context.Background()) }()
	<-entered
	if !c.Snapshot().Busy {
		t.Fatal("busy state missing")
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); !errors.Is(err, ErrBusy) {
		t.Fatalf("folder changed during operation: %v", err)
	}
	if err := c.Update(context.Background()); !errors.Is(err, ErrBusy) {
		t.Fatalf("concurrent update admitted: %v", err)
	}
	c.Cancel()
	if err := <-done; !errors.Is(err, context.Canceled) {
		t.Fatal(err)
	}
	if c.Snapshot().Busy || c.Snapshot().CanPlay {
		t.Fatal("cancel retained unsafe state")
	}
}
func TestPendingRecoveryBlocksUpdate(t *testing.T) {
	c, _, _ := fixture(t)
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{RecoveryRequired: true}, nil
	}
	if err := c.Check(context.Background()); err != nil {
		t.Fatal(err)
	}
	if s := c.Snapshot(); !s.CanRecover || s.CanUpdate {
		t.Fatalf("recovery not offered: %+v", s)
	}
	called := false
	c.recover = func(string, manifest.Trust) error { called = true; return nil }
	if err := c.Recover(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !called {
		t.Fatal("recovery not dispatched")
	}
}

func TestEmptySelectionDoesNotReplaceSavedClient(t *testing.T) {
	c, _, _ := fixture(t)
	before := c.Snapshot().ClientDir
	if err := c.SelectClient(context.Background(), ""); err == nil {
		t.Fatal("empty selection accepted")
	}
	if c.Snapshot().ClientDir != before {
		t.Fatal("empty selection replaced saved folder")
	}
}

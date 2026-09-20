package launcher

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"errors"
	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"reflect"
	"testing"
	"time"
)

func autoFixture(t *testing.T) (*Controller, *testSession, []byte, manifest.Signature) {
	c, s := playFixture(t)
	c.policy.AutomaticUpdates = true
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	now := time.Now().UTC()
	c.policy.Trust.Keys = []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour)}}
	m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Tombstones: []string{}}
	for _, name := range manifest.CoreAssets {
		m.Files = append(m.Files, manifest.File{Path: name, Size: 3, SHA256: manifest.Digest([]byte("new")), URL: "https://release.test/" + name, Required: true})
	}
	raw, _ := manifest.Canonical(m)
	sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, raw)}
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { return raw, sig, nil }
	return c, s, raw, sig
}
func TestAutomaticPlayChecksUpdatesThenStarts(t *testing.T) {
	for _, current := range []bool{false, true} {
		t.Run(map[bool]string{false: "missing", true: "current"}[current], func(t *testing.T) {
			c, s, raw, _ := autoFixture(t)
			order := []string{}
			close(s.done)
			fetch := c.fetch
			c.fetch = func(ctx context.Context, p Policy) ([]byte, manifest.Signature, error) {
				order = append(order, "fetch")
				return fetch(ctx, p)
			}
			if current {
				c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
					return installer.Inspection{Present: true, Current: true, Release: 2, ManifestDigest: manifest.Digest(raw)}, nil
				}
				c.diff = func(context.Context, []byte, manifest.Signature, manifest.Trust, string) (assets.Diff, error) {
					return assets.Diff{}, nil
				}
			}
			c.stage = func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error) {
				order = append(order, "stage")
				return assets.Generation{}, nil
			}
			c.install = func(context.Context, string, string, manifest.Trust) (installer.Result, error) {
				order = append(order, "install")
				return installer.Result{Release: 2, ManifestDigest: manifest.Digest(raw)}, nil
			}
			c.start = func(ctx context.Context, dir string, trust manifest.Trust) (gameSession, error) {
				order = append(order, "start")
				if !c.Snapshot().Busy || trust.HighestRelease != 2 {
					t.Fatal("lost operation/floor")
				}
				return s, nil
			}
			if !c.Snapshot().CanPlay {
				t.Fatal("first Play must install")
			}
			if err := c.Play(context.Background()); err != nil {
				t.Fatal(err)
			}
			want := []string{"fetch", "stage", "install", "start"}
			if current {
				want = []string{"fetch", "start"}
			}
			if !reflect.DeepEqual(order, want) {
				t.Fatal(order)
			}
		})
	}
}
func TestAutomaticFailuresNeverLaunch(t *testing.T) {
	for _, at := range []string{"fetch", "signature", "stage", "install", "cancel", "recovery"} {
		t.Run(at, func(t *testing.T) {
			c, _, raw, sig := autoFixture(t)
			failure := errors.New(at)
			c.stage = func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error) {
				if at == "stage" {
					return assets.Generation{}, failure
				}
				return assets.Generation{}, nil
			}
			c.install = func(context.Context, string, string, manifest.Trust) (installer.Result, error) {
				return installer.Result{}, failure
			}
			switch at {
			case "fetch":
				c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { return nil, sig, failure }
			case "signature":
				raw[0] ^= 1
			case "cancel":
				c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { c.Cancel(); return raw, sig, nil }
			case "recovery":
				c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
					return installer.Inspection{RecoveryRequired: true}, nil
				}
				c.recover = func(string, manifest.Trust) error { return failure }
			}
			c.start = func(context.Context, string, manifest.Trust) (gameSession, error) {
				t.Fatal("launch after failed update")
				return nil, nil
			}
			if err := c.Play(context.Background()); err == nil {
				t.Fatal("failure ignored")
			}
		})
	}
}
func TestAutomaticSelectionRecoversAndChecks(t *testing.T) {
	c, _, _, _ := autoFixture(t)
	recovered := false
	checked := false
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{RecoveryRequired: !recovered}, nil
	}
	c.recover = func(string, manifest.Trust) error { recovered = true; return nil }
	fetch := c.fetch
	c.fetch = func(ctx context.Context, p Policy) ([]byte, manifest.Signature, error) {
		checked = true
		return fetch(ctx, p)
	}
	if err := c.SelectClient(context.Background(), c.Snapshot().ClientDir); err != nil {
		t.Fatal(err)
	}
	if !recovered || !checked {
		t.Fatal("automatic startup missing")
	}
}

func TestAutomaticPlayRepairsInvalidActiveSignatureAndRefreshesTime(t *testing.T) {
	c, s, raw, _ := autoFixture(t)
	close(s.done)
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{Present: true, Current: false, Release: 2, ManifestDigest: manifest.Digest(raw), ValidationMessage: "invalid signature"}, nil
	}
	c.diff = func(context.Context, []byte, manifest.Signature, manifest.Trust, string) (assets.Diff, error) {
		return assets.Diff{}, nil
	}
	c.stage = func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error) {
		return assets.Generation{}, nil
	}
	var completed time.Time
	c.install = func(context.Context, string, string, manifest.Trust) (installer.Result, error) {
		completed = time.Now().UTC()
		return installer.Result{Release: 2, ManifestDigest: manifest.Digest(raw)}, nil
	}
	c.start = func(ctx context.Context, dir string, trust manifest.Trust) (gameSession, error) {
		if completed.IsZero() || trust.Now.Before(completed) {
			t.Fatal("skipped repair or stale verification time")
		}
		return s, nil
	}
	if err := c.Play(context.Background()); err != nil {
		t.Fatal(err)
	}
}

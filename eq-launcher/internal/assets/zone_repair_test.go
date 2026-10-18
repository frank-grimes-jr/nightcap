package assets

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"io"
	"net/http"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestSignedZoneArchivesMissingCorruptAndCurrent(t *testing.T) {
	for _, scenario := range []string{"missing", "same-size corruption", "current", "bad download"} {
		t.Run(scenario, func(t *testing.T) {
			_, _, trust, client, parent := fixture(t)
			public, private, err := ed25519.GenerateKey(rand.Reader)
			if err != nil {
				t.Fatal(err)
			}
			trust.Keys[0].Public = public
			trust.ReleaseInventory = true
			m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: trust.Now.Add(time.Hour), Tombstones: []string{}}
			names := append(append([]string{}, manifest.CoreAssets[:]...), "commons.s3d", "commons_obj.s3d")
			for _, name := range names {
				m.Files = append(m.Files, manifest.File{Path: name, Size: 3, SHA256: manifest.Digest([]byte("new")), URL: "https://release.test/" + name, Required: true})
				if name != "commons.s3d" || scenario == "current" {
					put(t, client, name, "new")
				}
			}
			if scenario == "same-size corruption" {
				put(t, client, "commons.s3d", "bad")
			}
			put(t, client, "eqclient.ini", "user settings")
			raw, err := manifest.Canonical(m)
			if err != nil {
				t.Fatal(err)
			}
			sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(private, raw)}
			diff, err := Inspect(context.Background(), raw, sig, trust, client)
			if err != nil {
				t.Fatal(err)
			}
			want := Missing
			if scenario == "current" {
				want = Current
			}
			if scenario == "same-size corruption" {
				want = Changed
			}
			for _, f := range diff.Files {
				if f.Path == "commons.s3d" && f.State != want {
					t.Fatalf("%s: %s", f.Path, f.State)
				}
			}
			requests := 0
			transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				requests++
				if r.URL.Path != "/commons.s3d" {
					t.Errorf("downloaded unchanged asset %s", r.URL.Path)
				}
				if scenario == "bad download" {
					io.WriteString(w, "bad")
				} else {
					io.WriteString(w, "new")
				}
			}))
			generation, err := stage(context.Background(), raw, sig, trust, client, parent, transport)
			if scenario == "bad download" {
				if err == nil || generation.Directory != "" {
					t.Fatal("corrupt download accepted")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			expectedRequests := 1
			if scenario == "current" {
				expectedRequests = 0
			}
			if requests != expectedRequests {
				t.Fatalf("requests=%d", requests)
			}
			data, err := os.ReadFile(filepath.Join(generation.Directory, "files", "commons.s3d"))
			if err != nil || string(data) != "new" {
				t.Fatalf("repair staging: %s %v", data, err)
			}
			settings, _ := os.ReadFile(filepath.Join(client, "eqclient.ini"))
			if string(settings) != "user settings" {
				t.Fatal("settings changed")
			}
		})
	}
}

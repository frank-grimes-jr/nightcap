//go:build windows

package installer

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/manifest"
)

func TestCompleteLoadingGalleryInstallAndRecovery(t *testing.T) {
	for _, interrupted := range []bool{false, true} {
		t.Run(map[bool]string{false: "install", true: "recover"}[interrupted], func(t *testing.T) {
			clientDir, stageDir := t.TempDir(), t.TempDir()
			put(t, clientDir, "eqclient.ini", "player settings")
			put(t, clientDir, "uifiles/default/equi_inventory.xml", "stock UI")
			now := time.Now().UTC()
			pub, priv, err := ed25519.GenerateKey(rand.Reader)
			if err != nil {
				t.Fatal(err)
			}
			m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.4.0", Expires: now.Add(time.Hour), Tombstones: []string{}}
			for _, name := range append(manifest.CoreAssets[:], manifest.LoadingScreenPaths()...) {
				oldName := name
				if strings.HasPrefix(name, "resources/") {
					oldName = "Resources/" + filepath.Base(name)
				}
				put(t, clientDir, oldName, "previous "+name)
				data := "replacement " + name
				put(t, stageDir, "files/"+name, data)
				m.Files = append(m.Files, manifest.File{Path: name, Size: int64(len(data)), SHA256: manifest.Digest([]byte(data)), URL: "https://release.test/" + name, Required: true})
			}
			raw, err := manifest.Canonical(m)
			if err != nil {
				t.Fatal(err)
			}
			sig := manifest.Signature{KeyID: "gallery", Bytes: ed25519.Sign(priv, raw)}
			trust := manifest.Trust{Keys: []manifest.Key{{ID: "gallery", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(2 * time.Hour)}}, Now: now, LauncherVersion: "0.4.0", ReleaseInventory: true, Hosts: []string{"release.test"}}
			client, err := os.OpenRoot(clientDir)
			if err != nil {
				t.Fatal(err)
			}
			defer client.Close()
			stage, err := os.OpenRoot(stageDir)
			if err != nil {
				t.Fatal(err)
			}
			defer stage.Close()
			_, err = installLocked(context.Background(), client, stage, raw, sig, trust, func(at string) error {
				if interrupted && at == "replace:30" {
					return errInterrupted
				}
				return nil
			})
			want := "replacement "
			if interrupted {
				if !errors.Is(err, errInterrupted) {
					t.Fatal(err)
				}
				if err = recoverLocked(client, trust); err != nil {
					t.Fatal(err)
				}
				want = "previous "
			} else if err != nil {
				t.Fatal(err)
			}
			for _, name := range manifest.LoadingScreenPaths() {
				assertBytes(t, client, name, want+name)
			}
			assertBytes(t, client, "eqclient.ini", "player settings")
			assertBytes(t, client, "uifiles/default/equi_inventory.xml", "stock UI")
		})
	}
}

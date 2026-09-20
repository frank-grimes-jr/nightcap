package installer

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"errors"
	"nightcap/eq-launcher/internal/manifest"
	"testing"
	"time"
)

func TestDynamicRecoveryRetainsSignedAuthorityAfterExpiry(t *testing.T) {
	for _, attack := range []string{"none", "unsigned path", "bad proof", "missing entry"} {
		t.Run(attack, func(t *testing.T) {
			root, stage, _, _, trust := fixture(t)
			pub, priv, _ := ed25519.GenerateKey(rand.Reader)
			trust.Keys[0].Public = pub
			trust.ReleaseInventory = true
			m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: trust.Now.Add(time.Hour), Tombstones: []string{}}
			for _, name := range append(manifest.CoreAssets[:], "gfaydark.s3d") {
				put(t, stage.Name(), "files/"+name, "new")
				m.Files = append(m.Files, manifest.File{Path: name, Size: 3, SHA256: manifest.Digest([]byte("new")), URL: "https://release.test/" + name, Required: true})
			}
			raw, _ := manifest.Canonical(m)
			sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, raw)}
			_, err := installLocked(context.Background(), root, stage, raw, sig, trust, func(at string) error {
				if at == "replace:4" {
					return errInterrupted
				}
				return nil
			})
			if !errors.Is(err, errInterrupted) {
				t.Fatal(err)
			}
			p, _ := readPending(root)
			j, _ := readJournal(root, p)
			if j.Schema != 2 {
				t.Fatal("missing proof")
			}
			switch attack {
			case "unsigned path":
				j.Entries[4].Path = "unowned.s3d"
			case "bad proof":
				j.Manifest[0] ^= 1
			case "missing entry":
				j.Entries = append(j.Entries[:4], j.Entries[5:]...)
			}
			trust.Now = trust.Now.Add(365 * 24 * time.Hour)
			trust.HighestRelease = 999
			if attack != "none" {
				if err := validateJournal(j, p, trust); err == nil {
					t.Fatal("unauthorized recovery accepted")
				}
				return
			}
			if err := recoverLocked(root, trust); err != nil {
				t.Fatal(err)
			}
			assertAbsent(t, root, "gfaydark.s3d")
			assertBytes(t, root, "dinput8.dll", "old dll")
			assertBytes(t, root, "eqclient.ini", "user settings")
			// A schema-1 journal never gains authority over newly scoped names.
			j.Schema = 1
			j.Manifest = nil
			j.Signature = manifest.Signature{}
			if err := validateJournal(j, p, trust); err == nil {
				b, _ := json.Marshal(j)
				t.Fatalf("legacy gained authority %s", b)
			}
		})
	}
}

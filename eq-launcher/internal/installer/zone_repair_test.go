package installer

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"nightcap/eq-launcher/internal/manifest"
	"testing"
	"time"
)

func TestInstallRepairsSignedZoneArchivesAndPreservesSettings(t *testing.T) {
	root, stage, _, _, trust := fixture(t)
	public, private, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	trust.Keys[0].Public = public
	trust.ReleaseInventory = true
	m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: trust.Now.Add(time.Hour), Tombstones: []string{}}
	names := append(append([]string{}, manifest.CoreAssets[:]...), "commons.s3d", "commons_obj.s3d")
	put(t, root.Name(), "commons_obj.s3d", "bad")
	for _, name := range names {
		put(t, stage.Name(), "files/"+name, "new")
		m.Files = append(m.Files, manifest.File{Path: name, Size: 3, SHA256: manifest.Digest([]byte("new")), URL: "https://release.test/" + name, Required: true})
	}
	raw, err := manifest.Canonical(m)
	if err != nil {
		t.Fatal(err)
	}
	sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(private, raw)}
	if _, err = installLocked(context.Background(), root, stage, raw, sig, trust, nil); err != nil {
		t.Fatal(err)
	}
	assertBytes(t, root, "commons.s3d", "new")
	assertBytes(t, root, "commons_obj.s3d", "new")
	assertBytes(t, root, "eqclient.ini", "user settings")
}

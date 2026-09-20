package selfupdate

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"nightcap/eq-launcher/internal/manifest"
	"testing"
	"time"
)

func signedFixture(t *testing.T, data []byte) (Channel, manifest.Trust, func(Channel) []byte) {
	t.Helper()
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	now := time.Now().UTC()
	trust := manifest.Trust{Keys: []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(24 * time.Hour)}}, Now: now, Hosts: []string{"release.test"}}
	c := Channel{Schema: 1, Kind: "nightcap-desktop", Platform: "windows-amd64", Release: 1, Version: "0.3.0", Expires: now.Add(time.Hour), Size: int64(len(data)), SHA256: manifest.Digest(data), URL: "https://release.test/launcher.exe"}
	sign := func(c Channel) []byte {
		b, _ := Canonical(c)
		raw, _ := json.Marshal(Envelope{b, manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, b)}})
		return raw
	}
	return c, trust, sign
}
func TestLauncherChannelRejectsWrongAuthority(t *testing.T) {
	for _, mode := range []string{"valid", "wrong key", "signature", "kind", "platform", "schema", "expired", "key expired", "size", "url", "hash", "rollback", "conflict", "game manifest", "noncanonical"} {
		t.Run(mode, func(t *testing.T) {
			c, trust, sign := signedFixture(t, []byte("exe"))
			floor := Checkpoint{}
			switch mode {
			case "wrong key":
				trust.Keys[0].Public, _, _ = ed25519.GenerateKey(rand.Reader)
			case "kind":
				c.Kind = "game"
			case "platform":
				c.Platform = "linux"
			case "schema":
				c.Schema = 2
			case "expired":
				c.Expires = trust.Now
			case "key expired":
				trust.Now = trust.Keys[0].NotAfter
			case "size":
				c.Size = MaxExecutableBytes + 1
			case "url":
				c.URL = "https://evil.test/evil.exe"
			case "hash":
				c.SHA256 = "bad"
			case "rollback":
				floor.Release = 2
			case "conflict":
				floor.Release = 1
				floor.Digest = manifest.Digest([]byte("other"))
			}
			raw := sign(c)
			if mode == "signature" {
				raw[50] ^= 1
			}
			if mode == "game manifest" {
				raw, _ = json.Marshal(manifest.Envelope{})
			}
			if mode == "noncanonical" {
				raw = append(raw, '\n')
			}
			_, err := Verify(raw, trust, floor)
			if (err == nil) != (mode == "valid") {
				t.Fatalf("%s: %v", mode, err)
			}
		})
	}
}

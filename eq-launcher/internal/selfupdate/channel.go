// Package selfupdate authenticates the desktop launcher independently of game releases.
package selfupdate

import (
	"bytes"
	"crypto/ed25519"
	"encoding/json"
	"fmt"
	"nightcap/eq-launcher/internal/manifest"
	"regexp"
	"time"
)

const MaxChannelBytes = 16384
const MaxExecutableBytes int64 = 128 << 20

// Channel is signed as exact compact JSON. No remote command, filename or destination exists.
type Channel struct {
	Schema   int       `json:"schema"`
	Kind     string    `json:"kind"`
	Platform string    `json:"platform"`
	Release  uint64    `json:"release"`
	Version  string    `json:"version"`
	Expires  time.Time `json:"expires"`
	Size     int64     `json:"size"`
	SHA256   string    `json:"sha256"`
	URL      string    `json:"url"`
}
type Envelope struct {
	Channel   []byte
	Signature manifest.Signature
}
type Checkpoint struct {
	Release uint64
	Digest  string
}

var digestPattern = regexp.MustCompile(`^[a-f0-9]{64}$`)
var versionPattern = regexp.MustCompile(`^[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}$`)

func Canonical(c Channel) ([]byte, error) { return json.Marshal(c) }
func strict(raw []byte, value any) error {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(value); err != nil {
		return err
	}
	b, err := json.Marshal(value)
	if err != nil || !bytes.Equal(b, raw) {
		return fmt.Errorf("noncanonical launcher metadata")
	}
	return nil
}
func Verify(raw []byte, trust manifest.Trust, floor Checkpoint) (Channel, error) {
	var c Channel
	var e Envelope
	if len(raw) == 0 || len(raw) > MaxChannelBytes {
		return c, fmt.Errorf("launcher channel size invalid")
	}
	if err := strict(raw, &e); err != nil {
		return c, err
	}
	var key *manifest.Key
	for i := range trust.Keys {
		if trust.Keys[i].ID == e.Signature.KeyID {
			if key != nil {
				return c, fmt.Errorf("ambiguous launcher key")
			}
			key = &trust.Keys[i]
		}
	}
	if key == nil || trust.Now.IsZero() || trust.Now.Before(key.NotBefore) || !trust.Now.Before(key.NotAfter) || len(key.Public) != ed25519.PublicKeySize || len(e.Signature.Bytes) != ed25519.SignatureSize || !ed25519.Verify(key.Public, e.Channel, e.Signature.Bytes) {
		return c, fmt.Errorf("launcher signature or key validity failed")
	}
	if err := strict(e.Channel, &c); err != nil {
		return c, err
	}
	if c.Schema != 1 || c.Kind != "nightcap-desktop" || c.Platform != "windows-amd64" || c.Release == 0 || !versionPattern.MatchString(c.Version) || !trust.Now.Before(c.Expires) || c.Expires.After(key.NotAfter) || c.Size <= 0 || c.Size > MaxExecutableBytes || !digestPattern.MatchString(c.SHA256) {
		return c, fmt.Errorf("unsupported or expired launcher channel")
	}
	if c.Release < floor.Release || (c.Release == floor.Release && manifest.Digest(e.Channel) != floor.Digest) {
		return c, fmt.Errorf("launcher rollback or release conflict rejected")
	}
	if err := manifest.ValidateURL(c.URL, trust.Hosts); err != nil {
		return c, err
	}
	return c, nil
}
func checkpoint(c Channel) Checkpoint {
	raw, _ := Canonical(c)
	return Checkpoint{c.Release, manifest.Digest(raw)}
}

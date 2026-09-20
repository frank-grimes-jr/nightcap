package main

import (
	"crypto/ed25519"
	"encoding/json"
	"fmt"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/selfupdate"
	"os"
	"path/filepath"
	"time"
)

func buildLauncher(executable, keyPath string, release uint64, p *productionProfile) error {
	if p == nil || release == 0 {
		return fmt.Errorf("production profile and launcher release required")
	}
	data, err := readBounded(executable, selfupdate.MaxExecutableBytes)
	if err != nil {
		return err
	}
	private, err := privateKey(keyPath, false)
	if err != nil {
		return err
	}
	public := private.Public().(ed25519.PublicKey)
	now := time.Now().UTC().Truncate(time.Second)
	key := manifest.Key{ID: "production-" + manifest.Digest(public)[:16], Public: public, NotBefore: p.KeyNotBefore, NotAfter: p.KeyNotAfter}
	c := selfupdate.Channel{Schema: 1, Kind: "nightcap-desktop", Platform: "windows-amd64", Release: release, Version: p.Version, Expires: now.Add(30 * 24 * time.Hour), Size: int64(len(data)), SHA256: manifest.Digest(data), URL: fmt.Sprintf("%s/launcher/%d/nightcap-desktop.exe", p.BaseURL, release)}
	raw, _ := selfupdate.Canonical(c)
	envelope, _ := json.Marshal(selfupdate.Envelope{Channel: raw, Signature: manifest.Signature{KeyID: key.ID, Bytes: ed25519.Sign(private, raw)}})
	if _, err = selfupdate.Verify(envelope, manifest.Trust{Keys: []manifest.Key{key}, Now: now, Hosts: p.hosts()}, selfupdate.Checkpoint{}); err != nil {
		return err
	}
	if err = os.Mkdir(p.publish, 0700); err != nil {
		return err
	}
	folder := filepath.Join(p.publish, "launcher", fmt.Sprint(release))
	if err = os.MkdirAll(folder, 0700); err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(folder, selfupdate.ImageName), data, 0644); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(p.publish, "launcher-channel.json"), envelope, 0644)
}

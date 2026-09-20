package main

import (
	"bytes"
	"crypto/ed25519"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPrivateKeyExclusiveAndStable(t *testing.T) {
	path := filepath.Join(t.TempDir(), "seed")
	first, err := privateKey(path, true)
	if err != nil {
		t.Fatal(err)
	}
	second, err := privateKey(path, false)
	if err != nil || !bytes.Equal(first, second) {
		t.Fatal("key changed", err)
	}
	if _, err = privateKey(path, true); err == nil {
		t.Fatal("replaced existing key")
	}
	if err = os.WriteFile(path, []byte("short"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = privateKey(path, false); err == nil {
		t.Fatal("accepted malformed seed")
	}
}

func TestClassicLavastormPolicyIncludesPinnedRetirement(t *testing.T) {
	key := manifest.Key{Public: make(ed25519.PublicKey, ed25519.PublicKeySize)}
	source, err := policySource(key, 2026092003, gameplayNames)
	if err != nil {
		t.Fatal(err)
	}
	for _, required := range []string{"lavastorm.s3d", "lavastorm_obj.s3d", "lavastorm.eqg", "86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"} {
		if !strings.Contains(string(source), required) {
			t.Fatalf("missing %s from signed QA policy", required)
		}
	}
}

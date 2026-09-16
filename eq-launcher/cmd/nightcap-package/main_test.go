package main

import (
	"bytes"
	"os"
	"path/filepath"
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

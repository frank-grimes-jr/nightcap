package playeraccess

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestWindowsCredentialRoundTripReplacementAndTamper(t *testing.T) {
	home := t.TempDir()
	if _, err := LoadCredential(home); !errors.Is(err, ErrCodeRequired) {
		t.Fatal(err)
	}
	token, _, _ := Generate("joe")
	if err := SaveCredential(home, token); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(home, credentialFile))
	if err != nil || bytes.Contains(b, []byte(token)) {
		t.Fatal("plaintext credential on disk", err)
	}
	got, err := LoadCredential(home)
	if err != nil || got != token {
		t.Fatal("native DPAPI roundtrip failed", err)
	}
	next, _, _ := Generate("joe")
	if err := SaveCredential(home, next); err != nil {
		t.Fatal(err)
	}
	got, err = LoadCredential(home)
	if err != nil || got != next {
		t.Fatal("replacement failed", err)
	}
	b[len(b)/2] ^= 0x80
	if err := os.WriteFile(filepath.Join(home, credentialFile), b, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadCredential(home); !errors.Is(err, ErrSavedCode) {
		t.Fatal("tampered ciphertext accepted", err)
	}
	if err := ForgetCredential(home); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadCredential(home); !errors.Is(err, ErrCodeRequired) {
		t.Fatal("forgotten credential recovered", err)
	}
}

package playeraccess

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func registryBytes(t *testing.T, records ...Record) []byte {
	t.Helper()
	b, err := json.Marshal(Registry{Version: 1, Credentials: records})
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func TestCredentialLifecycleAndFailClosedRegistry(t *testing.T) {
	token, record, err := Generate("joe")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "credentials.json")
	write := func(b []byte) {
		t.Helper()
		if err := os.WriteFile(path, b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	write(registryBytes(t, record))
	store, err := Open(path)
	if err != nil {
		t.Fatal(err)
	}
	if player, ok := store.Authenticate(token); !ok || player != "joe" {
		t.Fatal("issued credential rejected")
	}
	for _, bad := range []string{"", "joe", token + " ", "Bearer " + token, strings.ToUpper(token), token[:len(token)-1], strings.Replace(token, ".", "_", 1)} {
		if _, ok := store.Authenticate(bad); ok {
			t.Fatal("malformed credential accepted")
		}
	}
	other, _, _ := Generate("joe")
	if _, ok := store.Authenticate(other); ok {
		t.Fatal("unissued credential accepted")
	}
	write(registryBytes(t))
	if err := store.Refresh(); err != nil {
		t.Fatal(err)
	}
	if _, ok := store.Authenticate(token); ok {
		t.Fatal("revoked credential accepted")
	}
	write(registryBytes(t, record))
	if err := store.Refresh(); err != nil {
		t.Fatal(err)
	}
	write([]byte(`{"version":1,"credentials":[`))
	if err := store.Refresh(); err == nil {
		t.Fatal("corrupt registry accepted")
	}
	if _, ok := store.Authenticate(token); ok {
		t.Fatal("corrupt registry kept old authorization")
	}
	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if err := store.Refresh(); err == nil {
		t.Fatal("missing registry accepted")
	}
}

func TestRegistryRejectsAmbiguousOrUnboundedState(t *testing.T) {
	_, record, _ := Generate("joe")
	cases := [][]byte{
		registryBytes(t, record, record),
		[]byte(`{"version":2,"credentials":[]}`),
		[]byte(`{"version":1,"credentials":[],"allow_all":true}`),
		append(registryBytes(t), []byte(` {}`)...),
		[]byte(strings.Repeat(" ", MaxRegistryBytes+1)),
	}
	bad := record
	bad.Player = "../admin"
	cases = append(cases, registryBytes(t, bad))
	bad = record
	bad.SecretHash = "bad"
	cases = append(cases, registryBytes(t, bad))
	for _, b := range cases {
		path := filepath.Join(t.TempDir(), "credentials.json")
		if err := os.WriteFile(path, b, 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := Open(path); err == nil {
			t.Fatal("invalid registry accepted")
		}
	}
	if _, _, err := Generate("bad\nplayer"); err == nil {
		t.Fatal("unsafe audit label accepted")
	}
}

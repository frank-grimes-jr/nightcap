package assets

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestRejectWindowsJunction(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	outside := t.TempDir()
	put(t, outside, "nightcap/window.xml", "xml")
	link := filepath.Join(client, "uifiles")
	if output, err := exec.Command("cmd", "/c", "mklink", "/J", link, outside).CombinedOutput(); err != nil {
		t.Fatalf("create junction: %v %s", err, output)
	}
	if _, err := Inspect(context.Background(), raw, sig, trust, client); err == nil {
		t.Fatal("junction parent accepted")
	}
	if _, err := Stage(context.Background(), raw, sig, trust, client, parent); err == nil {
		t.Fatal("junction parent staged")
	}
}

func TestRejectStagingThroughClientJunction(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	alias := filepath.Join(parent, "client-alias")
	if output, err := exec.Command("cmd", "/c", "mklink", "/J", alias, client).CombinedOutput(); err != nil {
		t.Fatalf("create junction: %v %s", err, output)
	}
	if _, err := Stage(context.Background(), raw, sig, trust, client, alias); err == nil {
		t.Fatal("staged through alias into client")
	}
	entries, err := os.ReadDir(client)
	if err != nil || len(entries) != 0 {
		t.Fatalf("client modified: %v %v", entries, err)
	}
}

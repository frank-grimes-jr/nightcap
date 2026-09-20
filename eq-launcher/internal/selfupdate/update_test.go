//go:build windows

package selfupdate

import (
	"context"

	"errors"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestUpdateCacheAndRecovery(t *testing.T) {
	ctx := context.Background()
	data := []byte("fixture version one")
	c, trust, sign := signedFixture(t, data)
	raw := sign(c)
	downloads := 0
	cache := t.TempDir()
	get := func(_ context.Context, url string, _ int64) ([]byte, error) {
		if url == "channel" {
			return raw, nil
		}
		downloads++
		return data, nil
	}
	prep := func() (*Lease, error) { return prepare(ctx, cache, "channel", trust, func(string) {}, get) }
	lease, err := prep()
	if err != nil {
		t.Fatal(err)
	}
	// Retained handle prevents a replacement between hashing and process creation.
	if err = os.WriteFile(lease.Path, []byte("tamper"), 0600); err == nil {
		t.Fatal("verified image writable")
	}
	lease.Close()
	lease, err = prep()
	if err != nil {
		t.Fatal(err)
	}
	lease.Close()
	if downloads != 1 {
		t.Fatal("unchanged exe downloaded")
	}
	oldPath := filepath.Join(cache, c.SHA256, ImageName)
	// A new signed version reuses the same starter/cache and retains the prior image.
	c.Release++
	c.Version = "0.3.1"
	data = []byte("fixture version two")
	c.Size = int64(len(data))
	c.SHA256 = manifest.Digest(data)
	raw = sign(c)
	lease, err = prep()
	if err != nil {
		t.Fatal(err)
	}
	lease.Close()
	if downloads != 2 {
		t.Fatal(downloads)
	}
	if _, err = os.Stat(oldPath); err != nil {
		t.Fatal("previous version removed")
	}
	c.Release--
	raw = sign(c)
	if _, err = prep(); err == nil {
		t.Fatal("rollback accepted")
	}
	c.Release++
	raw = sign(c)
	// Interrupted partial download is disposable. The durable checkpoint remains valid.
	target := filepath.Join(cache, c.SHA256, ImageName)
	if err = os.WriteFile(target, []byte("corrupt"), 0600); err != nil {
		t.Fatal(err)
	}
	os.WriteFile(target+".partial", []byte("interrupted"), 0600)
	lease, err = prep()
	if err != nil {
		t.Fatal(err)
	}
	lease.Close()
	getBad := func(context.Context, string, int64) ([]byte, error) { return nil, errors.New("offline") }
	if _, err = prepare(ctx, cache, "channel", trust, func(string) {}, getBad); err == nil {
		t.Fatal("offline fallback allowed")
	}
}
func TestInvalidDownloadNeverPublishes(t *testing.T) {
	c, trust, sign := signedFixture(t, []byte("expected"))
	cache := t.TempDir()
	_, err := prepare(context.Background(), cache, "channel", trust, func(string) {}, func(_ context.Context, u string, _ int64) ([]byte, error) {
		if u == "channel" {
			return sign(c), nil
		}
		return []byte("tampered"), nil
	})
	if err == nil {
		t.Fatal("bad exe accepted")
	}
	if _, err = os.Stat(filepath.Join(cache, "checkpoint.json")); !errors.Is(err, os.ErrNotExist) {
		t.Fatal("advanced checkpoint on failed download")
	}
}
func TestStarterLock(t *testing.T) {
	cache := t.TempDir()
	lock, err := Lock(cache)
	if err != nil {
		t.Fatal(err)
	}
	if other, err := Lock(cache); err == nil {
		other.Close()
		t.Fatal("two starters")
	}
	lock.Close()
	lock, err = Lock(cache)
	if err != nil {
		t.Fatal(err)
	}
	lock.Close()
}
func TestActualWindowsUpgrade(t *testing.T) {
	if os.Getenv("NIGHTCAP_TEST_STARTER") == "" {
		t.Skip("enable fixture executable build with NIGHTCAP_TEST_STARTER=1")
	}
	build := t.TempDir()
	cache := t.TempDir()
	var raw, data []byte
	var trust manifest.Trust
	for i, version := range []string{"one", "two"} {
		source := filepath.Join(build, "main.go")
		code := `package main;import "os";func main(){os.WriteFile("ran.txt",[]byte("` + version + `"),0600)}`
		if err := os.WriteFile(source, []byte(code), 0600); err != nil {
			t.Fatal(err)
		}
		exe := filepath.Join(build, "fixture.exe")
		cmd := exec.Command("go", "build", "-o", exe, source)
		if b, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("build %v %s", err, b)
		}
		data, _ = os.ReadFile(exe)
		c, tr, sign := signedFixture(t, data)
		trust = tr
		c.Release = uint64(i + 1)
		raw = sign(c)
		lease, err := prepare(context.Background(), cache, "channel", trust, func(string) {}, func(_ context.Context, u string, _ int64) ([]byte, error) {
			if u == "channel" {
				return raw, nil
			}
			return data, nil
		})
		if err != nil {
			t.Fatal(err)
		}
		child, err := StartDesktop(lease)
		if err != nil {
			lease.Close()
			t.Fatal(err)
		}
		err = child.Wait()
		lease.Close()
		if err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(filepath.Join(filepath.Dir(lease.Path), "ran.txt"))
		if err != nil || string(b) != version {
			t.Fatalf("wrong desktop %s %v", b, err)
		}
	}
}

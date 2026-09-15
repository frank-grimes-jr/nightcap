package installer

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/manifest"
)

func fixture(t *testing.T) (*os.Root, *os.Root, []byte, manifest.Signature, manifest.Trust) {
	t.Helper()
	clientPath := t.TempDir()
	stagePath := t.TempDir()
	put(t, clientPath, "dinput8.dll", "old dll")
	put(t, clientPath, "old.dll", "retired bytes")
	put(t, clientPath, "eqclient.ini", "user settings")
	put(t, stagePath, "files/dinput8.dll", "new dll")
	put(t, stagePath, "files/uifiles/nightcap/window.xml", "new xml")
	client, err := os.OpenRoot(clientPath)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { client.Close() })
	stage, err := os.OpenRoot(stagePath)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { stage.Close() })
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Files: []manifest.File{
		{Path: "dinput8.dll", Size: 7, SHA256: manifest.Digest([]byte("new dll")), URL: "https://release.test/dll", Required: true},
		{Path: "uifiles/nightcap/window.xml", Size: 7, SHA256: manifest.Digest([]byte("new xml")), URL: "https://release.test/xml", Required: true},
	}, Tombstones: []string{"old.dll"}}
	raw, err := manifest.Canonical(m)
	if err != nil {
		t.Fatal(err)
	}
	sig := manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, raw)}
	trust := manifest.Trust{Keys: []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour)}}, Now: now, LauncherVersion: "0.1.0", HighestRelease: 1, Inventory: map[string]bool{"dinput8.dll": true, "uifiles/nightcap/window.xml": true}, Retired: map[string]bool{"old.dll": true}, Hosts: []string{"release.test"}}
	return client, stage, raw, sig, trust
}
func put(t *testing.T, root, name, data string) {
	t.Helper()
	p := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(data), 0600); err != nil {
		t.Fatal(err)
	}
}
func assertBytes(t *testing.T, root *os.Root, name, want string) {
	t.Helper()
	b, err := root.ReadFile(name)
	if err != nil || string(b) != want {
		t.Fatalf("%s = %q, %v; want %q", name, b, err, want)
	}
}
func assertAbsent(t *testing.T, root *os.Root, name string) {
	t.Helper()
	if _, err := root.Lstat(name); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("%s not absent: %v", name, err)
	}
}
func assertRestored(t *testing.T, root *os.Root) {
	t.Helper()
	assertBytes(t, root, "dinput8.dll", "old dll")
	assertBytes(t, root, "old.dll", "retired bytes")
	assertBytes(t, root, "eqclient.ini", "user settings")
	assertAbsent(t, root, "uifiles/nightcap/window.xml")
	assertAbsent(t, root, ".nightcap/active.json")
	assertAbsent(t, root, ".nightcap/pending.json")
}
func TestInstallGeneration(t *testing.T) {
	client, stage, raw, sig, trust := fixture(t)
	result, err := installLocked(context.Background(), client, stage, raw, sig, trust, nil)
	if err != nil {
		t.Fatal(err)
	}
	if result.Release != 2 || result.ManifestDigest != manifest.Digest(raw) || result.ReadyToPlay {
		t.Fatalf("bad result: %+v", result)
	}
	assertBytes(t, client, "dinput8.dll", "new dll")
	assertBytes(t, client, "uifiles/nightcap/window.xml", "new xml")
	assertAbsent(t, client, "old.dll")
	assertAbsent(t, client, ".nightcap/pending.json")
	assertBytes(t, client, "eqclient.ini", "user settings")
	if err := recoverLocked(client, trust); err != nil {
		t.Fatalf("idle recovery: %v", err)
	}
}
func TestFailuresRestoreWholeGeneration(t *testing.T) {
	for _, point := range []string{"pending", "replace:0", "replace:1", "remove:2", "active"} {
		t.Run(point, func(t *testing.T) {
			client, stage, raw, sig, trust := fixture(t)
			failure := errors.New("injected operation failure")
			_, err := installLocked(context.Background(), client, stage, raw, sig, trust, func(at string) error {
				if at == point {
					return failure
				}
				return nil
			})
			if !errors.Is(err, failure) {
				t.Fatalf("missing failure: %v", err)
			}
			assertRestored(t, client)
		})
	}
}
func TestRestartRecoveryAtEveryBoundary(t *testing.T) {
	for _, point := range []string{"pending", "replace:0", "replace:1", "remove:2", "active"} {
		t.Run(point, func(t *testing.T) {
			client, stage, raw, sig, trust := fixture(t)
			// A process-loss fault deliberately bypasses automatic rollback. Close and
			// reopen the directory handle so recovery uses only persisted state.
			_, err := installLocked(context.Background(), client, stage, raw, sig, trust, func(at string) error {
				if at == point {
					return errInterrupted
				}
				return nil
			})
			if !errors.Is(err, errInterrupted) {
				t.Fatalf("missing interruption: %v", err)
			}
			name := client.Name()
			client.Close()
			reopened, err := os.OpenRoot(name)
			if err != nil {
				t.Fatal(err)
			}
			defer reopened.Close()
			if err := recoverLocked(reopened, trust); err != nil {
				t.Fatal(err)
			}
			assertRestored(t, reopened)
			if err := recoverLocked(reopened, trust); err != nil {
				t.Fatalf("repeat recovery: %v", err)
			}
		})
	}
}
func TestCorruptStageRejectedBeforeMutation(t *testing.T) {
	client, stage, raw, sig, trust := fixture(t)
	put(t, stage.Name(), "files/dinput8.dll", "corrupt")
	if _, err := installLocked(context.Background(), client, stage, raw, sig, trust, nil); err == nil {
		t.Fatal("corrupt staged file accepted")
	}
	assertRestored(t, client)
}
func TestJournalCannotTargetUserFiles(t *testing.T) {
	client, stage, raw, sig, trust := fixture(t)
	_, err := installLocked(context.Background(), client, stage, raw, sig, trust, func(at string) error {
		if at == "pending" {
			return errInterrupted
		}
		return nil
	})
	if !errors.Is(err, errInterrupted) {
		t.Fatal(err)
	}
	// Rewrite the persisted journal and its digest as an untrusted local file;
	// valid JSON and a matching digest must not authorize a protected path.
	pending, err := readPending(client)
	if err != nil {
		t.Fatal(err)
	}
	j, err := readJournal(client, pending)
	if err != nil {
		t.Fatal(err)
	}
	j.Entries[0].Path = "eqclient.ini"
	if err := rewriteJournalForTest(client, pending, j); err != nil {
		t.Fatal(err)
	}
	if err := recoverLocked(client, trust); err == nil {
		t.Fatal("forged user-file journal accepted")
	}
	assertBytes(t, client, "eqclient.ini", "user settings")
}
func TestCorruptBackupStopsBeforeRecoveryWrites(t *testing.T) {
	client, stage, raw, sig, trust := fixture(t)
	_, err := installLocked(context.Background(), client, stage, raw, sig, trust, func(at string) error {
		if at == "replace:0" {
			return errInterrupted
		}
		return nil
	})
	if !errors.Is(err, errInterrupted) {
		t.Fatal(err)
	}
	pending, err := readPending(client)
	if err != nil {
		t.Fatal(err)
	}
	put(t, client.Name(), fmt.Sprintf(".nightcap/tx/%s/backup/0", pending.ID), "bad")
	if err := recoverLocked(client, trust); err == nil {
		t.Fatal("corrupt backup restored")
	}
	assertBytes(t, client, "dinput8.dll", "new dll")
	if _, err := client.Lstat(".nightcap/pending.json"); err != nil {
		t.Fatal("failed recovery discarded journal")
	}
}

func rewriteJournalForTest(root *os.Root, p pendingRecord, j journal) error {
	b, err := encode(j)
	if err != nil {
		return err
	}
	if err = replaceBlob(root, txPath(p.ID)+"/journal.json", b, p.ID, -3); err != nil {
		return err
	}
	p.SHA256 = manifest.Digest(b)
	b, err = encode(p)
	if err != nil {
		return err
	}
	return replaceBlob(root, ".nightcap/pending.json", b, p.ID, -1)
}

func release(t *testing.T, raw []byte, trust manifest.Trust, n uint64) ([]byte, manifest.Signature, manifest.Trust) {
	t.Helper()
	var m manifest.Manifest
	if err := json.Unmarshal(raw, &m); err != nil {
		t.Fatal(err)
	}
	m.Release = n
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	key := fmt.Sprintf("release-%d", n)
	trust.Keys = append(trust.Keys, manifest.Key{ID: key, Public: pub, NotBefore: trust.Now.Add(-time.Hour), NotAfter: trust.Now.Add(time.Hour)})
	raw, err = manifest.Canonical(m)
	if err != nil {
		t.Fatal(err)
	}
	return raw, manifest.Signature{KeyID: key, Bytes: ed25519.Sign(priv, raw)}, trust
}
func TestRepairAndDowngradeCheckpoint(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	if _, err := installLocked(context.Background(), root, stage, raw, sig, trust, nil); err != nil {
		t.Fatal(err)
	}
	put(t, root.Name(), "dinput8.dll", "corrupt")
	if err := root.Remove("uifiles/nightcap/window.xml"); err != nil {
		t.Fatal(err)
	}
	if _, err := installLocked(context.Background(), root, stage, raw, sig, trust, nil); err != nil {
		t.Fatalf("same release repair: %v", err)
	}
	assertBytes(t, root, "dinput8.dll", "new dll")
	assertBytes(t, root, "uifiles/nightcap/window.xml", "new xml")
	next, nextSig, nextTrust := release(t, raw, trust, 3)
	if _, err := installLocked(context.Background(), root, stage, next, nextSig, nextTrust, nil); err != nil {
		t.Fatal(err)
	}
	if _, err := installLocked(context.Background(), root, stage, raw, sig, trust, nil); err == nil {
		t.Fatal("persisted high-water mark ignored")
	}
}
func TestRecoveryRestoresPriorActiveRecord(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	if _, err := installLocked(context.Background(), root, stage, raw, sig, trust, nil); err != nil {
		t.Fatal(err)
	}
	before, err := root.ReadFile(".nightcap/active.json")
	if err != nil {
		t.Fatal(err)
	}
	raw, sig, trust = release(t, raw, trust, 3)
	_, err = installLocked(context.Background(), root, stage, raw, sig, trust, func(at string) error {
		if at == "active" {
			return errInterrupted
		}
		return nil
	})
	if !errors.Is(err, errInterrupted) {
		t.Fatal(err)
	}
	if _, err = installLocked(context.Background(), root, stage, raw, sig, trust, nil); !errors.Is(err, ErrRecoveryRequired) {
		t.Fatalf("pending generation ignored: %v", err)
	}
	if err = recoverLocked(root, trust); err != nil {
		t.Fatal(err)
	}
	assertBytes(t, root, ".nightcap/active.json", string(before))
}
func TestCancellationRollsBack(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	_, err := installLocked(ctx, root, stage, raw, sig, trust, func(at string) error {
		if at == "replace:0" {
			cancel()
		}
		return nil
	})
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("missing cancellation: %v", err)
	}
	assertRestored(t, root)
}

func TestPublicInstallRejectsUnsignedCandidateBeforeClientAccess(t *testing.T) {
	_, stage, raw, sig, trust := fixture(t)
	sig.Bytes[0] ^= 1
	b, err := encode(sig)
	if err != nil {
		t.Fatal(err)
	}
	if err = newBlob(stage, "manifest.json", raw); err != nil {
		t.Fatal(err)
	}
	if err = newBlob(stage, "signature.json", b); err != nil {
		t.Fatal(err)
	}
	if _, err = Install(context.Background(), "missing-client", stage.Name(), trust); err == nil || !strings.Contains(err.Error(), "signature verification failed") {
		t.Fatalf("client accessed before signature validation: %v", err)
	}
}

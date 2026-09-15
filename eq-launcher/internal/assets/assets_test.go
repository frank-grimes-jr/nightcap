package assets

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/tls"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/manifest"
)

func fixture(t *testing.T) ([]byte, manifest.Signature, manifest.Trust, string, string) {
	t.Helper()
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	m := manifest.Manifest{Schema: 1, Release: 2, MinLauncher: "0.1.0", Expires: now.Add(time.Hour), Files: []manifest.File{
		{Path: "dinput8.dll", SHA256: manifest.Digest([]byte("dll")), Size: 3, URL: "https://release.test/dinput8.dll", Required: true},
		{Path: "uifiles/nightcap/window.xml", SHA256: manifest.Digest([]byte("xml")), Size: 3, URL: "https://release.test/window.xml", Required: true},
	}, Tombstones: []string{"old.dll"}}
	raw, err := manifest.Canonical(m)
	if err != nil {
		t.Fatal(err)
	}
	trust := manifest.Trust{Keys: []manifest.Key{{ID: "test", Public: pub, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour)}}, Now: now, LauncherVersion: "0.1.0", Inventory: map[string]bool{"dinput8.dll": true, "uifiles/nightcap/window.xml": true}, Retired: map[string]bool{"old.dll": true}, Hosts: []string{"release.test"}}
	return raw, manifest.Signature{KeyID: "test", Bytes: ed25519.Sign(priv, raw)}, trust, t.TempDir(), t.TempDir()
}
func put(t *testing.T, root, name, contents string) {
	t.Helper()
	p := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(contents), 0600); err != nil {
		t.Fatal(err)
	}
}
func TestInspectDiff(t *testing.T) {
	raw, sig, trust, client, _ := fixture(t)
	put(t, client, "dinput8.dll", "bad")
	put(t, client, "old.dll", "old")
	put(t, client, "eqclient.ini", "user settings")
	d, err := Inspect(context.Background(), raw, sig, trust, client)
	if err != nil {
		t.Fatal(err)
	}
	if len(d.Files) != 2 || d.Files[0].State != Changed || d.Files[1].State != Missing || len(d.Remove) != 1 || d.Remove[0] != "old.dll" {
		t.Fatalf("unexpected diff: %+v", d)
	}
	put(t, client, "dinput8.dll", "dll")
	put(t, client, "uifiles/nightcap/window.xml", "xml")
	d, err = Inspect(context.Background(), raw, sig, trust, client)
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range d.Files {
		if f.State != Current {
			t.Fatalf("not current: %+v", f)
		}
	}
	b, _ := os.ReadFile(filepath.Join(client, "eqclient.ini"))
	if string(b) != "user settings" {
		t.Fatal("user file modified")
	}
}
func TestInvalidMetadataBeforeFilesystem(t *testing.T) {
	raw, sig, trust, _, stage := fixture(t)
	raw[0] ^= 1
	_, err := Inspect(context.Background(), raw, sig, trust, "nonexistent")
	if err == nil || !strings.Contains(err.Error(), "manifest:") {
		t.Fatalf("signature not first: %v", err)
	}
	_, err = Stage(context.Background(), raw, sig, trust, "nonexistent", stage)
	if err == nil || !strings.Contains(err.Error(), "manifest:") {
		t.Fatalf("signature not first: %v", err)
	}
	entries, _ := os.ReadDir(stage)
	if len(entries) != 0 {
		t.Fatal("untrusted input wrote staging")
	}
}
func TestRejectNonRegularLocalAsset(t *testing.T) {
	raw, sig, trust, client, _ := fixture(t)
	if err := os.Mkdir(filepath.Join(client, "dinput8.dll"), 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := Inspect(context.Background(), raw, sig, trust, client); err == nil {
		t.Fatal("directory asset accepted")
	}
}
func TestRejectLinkParent(t *testing.T) {
	raw, sig, trust, client, _ := fixture(t)
	outside := t.TempDir()
	put(t, outside, "nightcap/window.xml", "xml")
	if err := os.Symlink(outside, filepath.Join(client, "uifiles")); err != nil {
		t.Skipf("symlink privilege unavailable: %v", err)
	}
	if _, err := Inspect(context.Background(), raw, sig, trust, client); err == nil {
		t.Fatal("linked parent accepted")
	}
}

// Keep production HTTPS/TLS verification enabled. Only route the test host to
// a local TLS server whose certificate is trusted by its test client.
func localTransport(t *testing.T, handler http.Handler) *http.Transport {
	t.Helper()
	s := httptest.NewTLSServer(handler)
	t.Cleanup(s.Close)
	transport := s.Client().Transport.(*http.Transport).Clone()
	transport.TLSClientConfig = transport.TLSClientConfig.Clone()
	transport.TLSClientConfig.ServerName = "example.com"
	transport.TLSClientConfig.MinVersion = tls.VersionTLS12
	transport.DialContext = func(ctx context.Context, network, addr string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, network, s.Listener.Addr().String())
	}
	t.Cleanup(transport.CloseIdleConnections)
	return transport
}
func TestStageCompleteGeneration(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	put(t, client, "dinput8.dll", "dll")
	put(t, client, "old.dll", "old")
	requests := 0
	transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests++
		if r.URL.Path != "/window.xml" {
			t.Errorf("downloaded current asset: %s", r.URL.Path)
		}
		io.WriteString(w, "xml")
	}))
	g, err := stage(context.Background(), raw, sig, trust, client, parent, transport)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(g.Directory, "complete.json")); err != nil {
		t.Fatalf("missing completion marker: %v", err)
	}
	if g.Release != 2 || g.ManifestDigest != manifest.Digest(raw) || requests != 1 {
		t.Fatalf("bad result: %+v requests=%d", g, requests)
	}
	for name, want := range map[string]string{"dinput8.dll": "dll", "uifiles/nightcap/window.xml": "xml"} {
		b, err := os.ReadFile(filepath.Join(g.Directory, "files", filepath.FromSlash(name)))
		if err != nil || string(b) != want {
			t.Fatalf("staged %s: %q %v", name, b, err)
		}
	}
	b, _ := os.ReadFile(filepath.Join(g.Directory, "manifest.json"))
	if string(b) != string(raw) {
		t.Fatal("manifest not retained")
	}
	b, _ = os.ReadFile(filepath.Join(client, "old.dll"))
	if string(b) != "old" {
		t.Fatal("tombstone applied before install")
	}
	if _, err := os.Stat(filepath.Join(client, "uifiles")); !os.IsNotExist(err) {
		t.Fatal("live client mutated")
	}
}
func TestStageRejectDownloadFailures(t *testing.T) {
	for _, scenario := range []string{"bad hash", "short", "oversize", "chunked oversize", "partial generation", "status", "encoding", "redirect host", "redirect http", "redirect cycle", "cancel"} {
		t.Run(scenario, func(t *testing.T) {
			raw, sig, trust, client, parent := fixture(t)
			transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				switch scenario {
				case "bad hash":
					io.WriteString(w, "bad")
				case "short":
					io.WriteString(w, "x")
				case "oversize":
					io.WriteString(w, "dll-extra")
				case "chunked oversize":
					w.(http.Flusher).Flush()
					io.WriteString(w, "dll-extra")
				case "partial generation":
					if r.URL.Path == "/dinput8.dll" {
						io.WriteString(w, "dll")
					} else {
						io.WriteString(w, "bad")
					}
				case "status":
					w.WriteHeader(404)
				case "encoding":
					w.Header().Set("Content-Encoding", "gzip")
					io.WriteString(w, "dll")
				case "redirect host":
					http.Redirect(w, r, "https://evil.test/asset", 302)
				case "redirect http":
					http.Redirect(w, r, "http://release.test/asset", 302)
				case "redirect cycle":
					http.Redirect(w, r, "https://release.test/asset", 302)
				default:
					io.WriteString(w, "dll")
				}
			}))
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if scenario == "cancel" {
				cancel()
			}
			g, err := stage(ctx, raw, sig, trust, client, parent, transport)
			if err == nil || g.Directory != "" {
				t.Fatalf("bad generation accepted: %+v %v", g, err)
			}
			entries, _ := os.ReadDir(parent)
			if len(entries) != 0 {
				t.Fatalf("failed staging retained: %v", entries)
			}
			entries, _ = os.ReadDir(client)
			if len(entries) != 0 {
				t.Fatal("failed staging modified client")
			}
		})
	}
}
func TestStageOfflineCurrentFiles(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	put(t, client, "dinput8.dll", "dll")
	put(t, client, "uifiles/nightcap/window.xml", "xml")
	transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("network used for current files")
		w.WriteHeader(500)
	}))
	if _, err := stage(context.Background(), raw, sig, trust, client, parent, transport); err != nil {
		t.Fatal(err)
	}
}

func TestAllowedRedirect(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/dinput8.dll" {
			http.Redirect(w, r, "https://release.test/dll-final", 302)
			return
		}
		if r.URL.Path == "/dll-final" {
			io.WriteString(w, "dll")
			return
		}
		io.WriteString(w, "xml")
	}))
	if _, err := stage(context.Background(), raw, sig, trust, client, parent, transport); err != nil {
		t.Fatal(err)
	}
}
func TestWrongSizeAndMissingRetired(t *testing.T) {
	raw, sig, trust, client, _ := fixture(t)
	put(t, client, "dinput8.dll", "longer than dll")
	d, err := Inspect(context.Background(), raw, sig, trust, client)
	if err != nil {
		t.Fatal(err)
	}
	if d.Files[0].State != Changed || len(d.Remove) != 0 {
		t.Fatalf("unexpected diff: %+v", d)
	}
}
func TestVerifyCopyBoundedAndCancelled(t *testing.T) {
	// Chunked or dishonest Content-Length must not force unbounded disk use.
	data := strings.Repeat("x", 1<<20)
	var out strings.Builder
	err := verifyCopy(context.Background(), &out, strings.NewReader(data), manifest.File{Path: "asset", Size: 3, SHA256: manifest.Digest([]byte("xxx"))})
	if err == nil || out.Len() != 4 {
		t.Fatalf("not bounded: bytes=%d err=%v", out.Len(), err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	out.Reset()
	if err := verifyCopy(ctx, &out, strings.NewReader("xxx"), manifest.File{Size: 3}); err == nil || out.Len() != 0 {
		t.Fatal("cancelled copy wrote bytes")
	}
}

func TestRejectStagingInsideClient(t *testing.T) {
	for _, nested := range []bool{false, true} {
		t.Run(fmt.Sprint(nested), func(t *testing.T) {
			raw, sig, trust, client, _ := fixture(t)
			parent := client
			if nested {
				parent = filepath.Join(client, "staging")
				if err := os.Mkdir(parent, 0700); err != nil {
					t.Fatal(err)
				}
			}
			if _, err := Stage(context.Background(), raw, sig, trust, client, parent); err == nil {
				t.Fatal("staged inside client")
			}
			entries, _ := os.ReadDir(parent)
			if len(entries) != 0 {
				t.Fatalf("wrote client staging: %v", entries)
			}
		})
	}
}
func TestCleanupFailureIsReportedAndUnmarked(t *testing.T) {
	raw, sig, trust, client, parent := fixture(t)
	transport := localTransport(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, "bad") }))
	cleanupFailure := errors.New("test cleanup denied")
	g, err := stageWithCleanup(context.Background(), raw, sig, trust, client, parent, transport, func(*os.Root, string) error { return cleanupFailure })
	if err == nil || !errors.Is(err, cleanupFailure) || !errors.Is(err, errContent) || g.Directory != "" {
		t.Fatalf("cleanup not joined with original failure: %+v %v", g, err)
	}
	entries, err := os.ReadDir(parent)
	if err != nil || len(entries) != 1 {
		t.Fatalf("fixture did not retain orphan: %v %v", entries, err)
	}
	if _, err := os.Stat(filepath.Join(parent, entries[0].Name(), "complete.json")); !os.IsNotExist(err) {
		t.Fatal("failed generation marked complete")
	}
}

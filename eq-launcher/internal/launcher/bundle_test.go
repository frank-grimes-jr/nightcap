package launcher

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"testing"
	"testing/fstest"
)

func TestBundleCheckAndUpdateNeverUseHTTP(t *testing.T) {
	original := http.DefaultTransport
	http.DefaultTransport = &http.Transport{DialContext: func(context.Context, string, string) (net.Conn, error) {
		t.Error("offline bundle attempted network")
		return nil, fmt.Errorf("network forbidden")
	}}
	defer func() { http.DefaultTransport = original }()
	fixtureController, raw, sig := fixture(t)
	signature, _ := json.Marshal(sig)
	p := fixtureController.policy
	p.Bundle = fstest.MapFS{"manifest.json": {Data: raw}, "signature.json": {Data: signature}, "files/dinput8.dll": {Data: []byte("dll")}}
	c, err := New(t.TempDir(), p)
	if err != nil {
		t.Fatal(err)
	}
	c.probe = func(string) (client.Report, error) { return client.Report{Supported: true}, nil }
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{}, nil
	}
	installed := false
	c.install = func(_ context.Context, _ string, stage string, _ manifest.Trust) (installer.Result, error) {
		data, err := os.ReadFile(filepath.Join(stage, "files", "dinput8.dll"))
		if err != nil || string(data) != "dll" {
			t.Fatal("bundle did not stage verified bytes", err)
		}
		installed = true
		return installer.Result{Release: 2}, nil
	}
	if err = c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	if err = c.Check(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err = c.Update(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !installed {
		t.Fatal("installer not called")
	}
	// Missing embedded metadata must fail rather than falling back to valid URLs.
	delete(p.Bundle.(fstest.MapFS), "manifest.json")
	if err = c.Check(context.Background()); err == nil {
		t.Fatal("missing bundle accepted")
	}
}

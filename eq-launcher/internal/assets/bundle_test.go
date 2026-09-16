package assets

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"testing/fstest"
	"time"
)

func TestBundleStagingRejectsDamageAndCleansUp(t *testing.T) {
	for _, mode := range []string{"valid", "tampered", "missing", "signature", "expired", "cancelled"} {
		t.Run(mode, func(t *testing.T) {
			raw, sig, trust, client, parent := fixture(t)
			bundle := fstest.MapFS{"files/dinput8.dll": {Data: []byte("dll")}, "files/uifiles/nightcap/window.xml": {Data: []byte("xml")}}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			switch mode {
			case "tampered":
				bundle["files/dinput8.dll"].Data = []byte("bad")
			case "missing":
				delete(bundle, "files/dinput8.dll")
			case "signature":
				sig.Bytes[0] ^= 1
			case "expired":
				trust.Now = trust.Now.Add(2 * time.Hour)
			case "cancelled":
				cancel()
			}
			generation, err := StageBundle(ctx, raw, sig, trust, client, parent, bundle)
			if mode == "valid" {
				if err != nil {
					t.Fatal(err)
				}
				if _, err := os.Stat(filepath.Join(generation.Directory, "complete.json")); err != nil {
					t.Fatal(err)
				}
				data, err := os.ReadFile(filepath.Join(generation.Directory, "files/dinput8.dll"))
				if err != nil || string(data) != "dll" {
					t.Fatal("incorrect staged asset", err)
				}
			} else {
				if err == nil {
					t.Fatal("invalid bundle accepted")
				}
				entries, _ := os.ReadDir(parent)
				if len(entries) != 0 {
					t.Fatal("failed staging retained files")
				}
			}
			if entries, _ := os.ReadDir(client); len(entries) != 0 {
				t.Fatal("staging modified client")
			}
		})
	}
}
func TestBundleMetadataBoundedAndCanonical(t *testing.T) {
	raw, sig, _, _, _ := fixture(t)
	signature, _ := json.Marshal(sig)
	for _, mode := range []string{"valid", "noncanonical whitespace", "oversized", "missing"} {
		t.Run(mode, func(t *testing.T) {
			bundle := fstest.MapFS{"manifest.json": {Data: raw}, "signature.json": {Data: signature}}
			switch mode {
			case "noncanonical whitespace":
				bundle["signature.json"].Data = append(signature, 10)
			case "oversized":
				bundle["signature.json"].Data = make([]byte, 4097)
			case "missing":
				delete(bundle, "manifest.json")
			}
			got, _, err := BundleMetadata(bundle)
			if mode == "valid" {
				if err != nil || string(got) != string(raw) {
					t.Fatal(err)
				}
			} else if err == nil {
				t.Fatal("invalid metadata accepted")
			}
		})
	}
}

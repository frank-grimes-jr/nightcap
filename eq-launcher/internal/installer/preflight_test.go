package installer

import (
	"context"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
	"testing"
)

func TestPatchAssetsBindParsedBytesToRequiredManifest(t *testing.T) {
	for _, mode := range []string{"valid", "missing", "optional", "changed", "oversize", "missing file"} {
		t.Run(mode, func(t *testing.T) {
			_, stage, _, _, _ := fixture(t)
			config := []byte("test config")
			put(t, stage.Name(), "files/"+preflight.ConfigPath, string(config))
			put(t, stage.Name(), "files/"+preflight.CatalogPath, string(preflight.Catalog()))
			m := manifest.Manifest{Files: []manifest.File{
				{Path: preflight.ConfigPath, Required: true, Size: int64(len(config)), SHA256: manifest.Digest(config)},
				{Path: preflight.CatalogPath, Required: true, Size: int64(len(preflight.Catalog())), SHA256: manifest.Digest(preflight.Catalog())},
			}}
			switch mode {
			case "missing":
				m.Files = m.Files[:1]
			case "optional":
				m.Files[0].Required = false
			case "changed":
				put(t, stage.Name(), "files/"+preflight.ConfigPath, "altered")
			case "oversize":
				m.Files[0].Size = preflight.MaxConfigBytes + 1
			case "missing file":
				if err := stage.Remove("files/" + preflight.CatalogPath); err != nil {
					t.Fatal(err)
				}
			}
			actual, _, err := patchAssets(stage, m)
			if mode == "valid" {
				if err != nil || string(actual) != string(config) {
					t.Fatalf("valid assets: %q %v", actual, err)
				}
			} else if err == nil {
				t.Fatal("unsafe preflight asset accepted")
			}
		})
	}
}
func TestPublicInstallRejectsMissingPreflightBeforeMutation(t *testing.T) {
	client, stage, raw, sig, trust := fixture(t)
	data, err := encode(sig)
	if err != nil {
		t.Fatal(err)
	}
	put(t, stage.Name(), "manifest.json", string(raw))
	put(t, stage.Name(), "signature.json", string(data))
	if _, err = Install(context.Background(), client.Name(), stage.Name(), trust); err == nil {
		t.Fatal("missing required preflight accepted")
	}
	assertRestored(t, client)
}

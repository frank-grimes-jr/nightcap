package main

import (
	"testing"

	"nightcap/eq-launcher/internal/manifest"
)

func TestClassicContractRejectsMissingOrChangedAssets(t *testing.T) {
	if len(classicModelNames) != 25 || len(classicModelDigests) != len(classicModelNames) {
		t.Fatal("classic inventory and embedded proxy contract differ")
	}
	if err := validateClassicModels(nil); err == nil {
		t.Fatal("accepted missing classic assets")
	}
	files := make(map[string][]byte)
	for _, name := range classicModelNames {
		if len(classicModelDigests[name]) != 64 {
			t.Fatalf("missing digest: %s", name)
		}
		files[name] = []byte("changed archive")
	}
	if err := validateClassicModels(files); err == nil {
		t.Fatal("accepted changed classic assets")
	}
}

func TestWaypointAssetsAreRequiredAndChecked(t *testing.T) {
	// Use a complete small fixture to exercise the production gate without
	// checking 92 MB of proprietary model archives into the repository.
	original := classicModelDigests
	defer func() { classicModelDigests = original }()
	classicModelDigests = make(map[string]string)
	files := make(map[string][]byte)
	for _, name := range classicModelNames {
		files[name] = []byte("fixture " + name)
		classicModelDigests[name] = manifest.Digest(files[name])
	}
	if err := validateClassicModels(files); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"crs.eqg", "nightcap_modern_chr.txt", "nightcap_models_chr.txt"} {
		if _, exists := original[name]; !exists {
			t.Fatalf("waypoint model contract omits %s", name)
		}
		good := files[name]
		delete(files, name)
		if err := validateClassicModels(files); err == nil {
			t.Fatalf("accepted missing %s", name)
		}
		files[name] = []byte("changed")
		if err := validateClassicModels(files); err == nil {
			t.Fatalf("accepted changed %s", name)
		}
		files[name] = good
	}
}

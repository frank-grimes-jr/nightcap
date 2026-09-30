package main

import "testing"

func TestClassicContractRejectsMissingOrChangedAssets(t *testing.T) {
	if len(classicModelNames) != 23 || len(classicModelDigests) != len(classicModelNames) {
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

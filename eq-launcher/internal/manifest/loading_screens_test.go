package manifest

import "testing"

func TestLoadingScreensAreTheOnlyStockUIException(t *testing.T) {
	allowed := LoadingScreenPaths()
	if len(allowed) != 56 {
		t.Fatal("incomplete RoF2 gallery")
	}
	for _, name := range allowed {
		if !GameAssetPath(name) {
			t.Fatalf("loading screen rejected: %s", name)
		}
	}
	for _, name := range []string{
		"resources/other.jpg", "resources/loadscreen.dll", "Resources/loadscreen.jpg",
		"uifiles/default/equi_inventory.xml", "uifiles/default/loadscreens/loadscreen01.xml",
		"uifiles/default/loadscreens/loadscreen00.jpg", "uifiles/default/loadscreens/loadscreen56.jpg",
		"uifiles/default/loadscreens/loadscreen1.jpg", "uifiles/default/loadscreens/../loadscreen01.jpg",
		"uifiles/other/loadscreens/loadscreen01.jpg", "eqclient.ini",
	} {
		if GameAssetPath(name) {
			t.Fatalf("out-of-scope file accepted: %s", name)
		}
	}
}

func TestSignedLoadingGalleryVersionGate(t *testing.T) {
	m, trust, key := fixture(t)
	trust.ReleaseInventory = true
	trust.LauncherVersion = "0.4.0"
	m.MinLauncher = "0.4.0"
	for _, name := range append(CoreAssets[1:], LoadingScreenPaths()...) {
		f := m.Files[0]
		f.Path = name
		m.Files = append(m.Files, f)
	}
	raw, sig := signed(t, m, key)
	if _, err := Verify(raw, sig, trust); err != nil {
		t.Fatal(err)
	}
	trust.LauncherVersion = "0.3.1"
	if _, err := Verify(raw, sig, trust); err == nil {
		t.Fatal("old desktop accepted new scope")
	}
}

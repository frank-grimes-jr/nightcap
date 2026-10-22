package preflight

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"

	"nightcap/eq-launcher/internal/manifest"
)

func contractFixture(t *testing.T, metadata []byte) []byte {
	t.Helper()
	policy, err := RuntimeForCatalog(metadata)
	if err != nil {
		t.Fatal(err)
	}
	b := bootstrapFixture(true)
	copy(b[0x600:], policy.CatalogSHA256+"\x00"+policy.ProxyVersion+"\x00")
	return b
}

func TestProxyCatalogPair(t *testing.T) {
	proxy := contractFixture(t, catalogBytes)
	if err := CheckProxyCatalog(proxy, catalogBytes); err != nil {
		t.Fatal(err)
	}
	var old catalog
	if err := json.Unmarshal(catalogBytes, &old); err != nil {
		t.Fatal(err)
	}
	old.ProxyVersion = "0.10.0"
	oldBytes, _ := json.Marshal(old)
	for name, pair := range map[string][2][]byte{
		"new DLL with retained old catalog": {proxy, oldBytes},
		"stale DLL with new catalog":        {contractFixture(t, oldBytes), catalogBytes},
		"noncanonical catalog":              {proxy, append(bytes.Clone(catalogBytes), '\n')},
		"invalid image":                     {[]byte("not a DLL"), catalogBytes},
		"missing identity":                  {bootstrapFixture(true), catalogBytes},
		"identity only in overlay":          {append(bootstrapFixture(true), proxy[0x600:0x700]...), catalogBytes},
	} {
		t.Run(name, func(t *testing.T) {
			if err := CheckProxyCatalog(pair[0], pair[1]); err == nil {
				t.Fatal("invalid proxy/catalog pair accepted")
			}
		})
	}
	wrongVersion := bytes.Clone(proxy)
	policy, _ := RuntimeForCatalog(catalogBytes)
	wrongVersion[0x600+len(policy.CatalogSHA256)+1] = '9'
	if err := CheckProxyCatalog(wrongVersion, catalogBytes); err == nil {
		t.Fatal("wrong proxy version accepted")
	}
	for _, flags := range []uint32{0xc0000040, 0x60000040, 0x42000040} {
		bad := bytes.Clone(proxy)
		put32(bad, 0x1a0+36, flags)
		if err := CheckProxyCatalog(bad, catalogBytes); err == nil {
			t.Fatalf("unsafe identity section %x accepted", flags)
		}
	}
}

// Run against the installed, signed October 18 bytes without loading the DLL.
func TestReleasedProxyCatalog(t *testing.T) {
	path := os.Getenv("NIGHTCAP_CONTRACT_PROXY")
	if path == "" {
		t.Skip("set NIGHTCAP_CONTRACT_PROXY for released-artifact regression")
	}
	proxy, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if manifest.Digest(proxy) != "9dd6ad400d7390f95c3af88ffe70a67c180368a213e13cc951cee20fefb63380" {
		t.Fatal("release proxy fixture drift")
	}
	old, err := os.ReadFile(os.Getenv("NIGHTCAP_CONTRACT_OLD_CATALOG"))
	if err != nil {
		t.Fatal(err)
	}
	if manifest.Digest(old) != "42351ac8e1f402b03f04dc55ab9aa20ec6a6946c65f20d314f94bc682d9e55a7" {
		t.Fatal("release catalog fixture drift")
	}
	if err := CheckProxyCatalog(proxy, old); err == nil {
		t.Fatal("broken published pair accepted")
	}
	// Preserve this incident regression when the current proxy version changes.
	good, err := os.ReadFile("testdata/released-catalog-20261019.json")
	if err != nil {
		t.Fatal(err)
	}
	if manifest.Digest(good) != "2599919e5701d4b2dc43e569da72a3d99e503ae6f511f690d7a09fe581f1a8b4" {
		t.Fatal("released catalog fixture drift")
	}
	if err := CheckProxyCatalog(proxy, good); err != nil {
		t.Fatal(err)
	}
}

func TestBuiltProxyCatalog(t *testing.T) {
	path := os.Getenv("NIGHTCAP_BUILT_PROXY")
	if path == "" {
		t.Skip("set NIGHTCAP_BUILT_PROXY to check the actual candidate artifact")
	}
	proxy, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := CheckProxyCatalog(proxy, catalogBytes); err != nil {
		t.Fatal(err)
	}
	old, err := os.ReadFile(os.Getenv("NIGHTCAP_PREVIOUS_CATALOG"))
	if err != nil {
		t.Fatal(err)
	}
	if err := CheckProxyCatalog(proxy, old); err == nil {
		t.Fatal("candidate accepted the previous proxy catalog")
	}
}

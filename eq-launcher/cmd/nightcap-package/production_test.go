package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"go/parser"
	"go/token"
	"nightcap/eq-launcher/internal/manifest"
	"strings"
	"testing"
	"time"
)

func profileFixture() productionProfile {
	return productionProfile{BaseURL: "https://play.nightcapgame.com", GuideURL: "https://play.nightcapgame.com/guide.html", RelayURL: "https://play.nightcapgame.com/connect", Version: "0.2.0", KeyNotBefore: time.Now().Add(-time.Hour), KeyNotAfter: time.Now().Add(365 * 24 * time.Hour)}
}
func TestProductionProfileRejectsUnsafeEndpoints(t *testing.T) {
	for _, bad := range []string{"http://play.nightcapgame.com", "https://play.example", "https://127.0.0.1", "https://play.nightcapgame.com/", "https://play.nightcapgame.com:443", "https://play.nightcapgame.com?x=1"} {
		p := profileFixture()
		p.BaseURL = bad
		if p.validate() == nil {
			t.Fatalf("accepted %s", bad)
		}
	}
	p := profileFixture()
	if err := p.validate(); err != nil {
		t.Fatal(err)
	}
	p.RelayURL = "https://elsewhere.com/connect"
	if p.validate() == nil {
		t.Fatal("foreign relay host accepted")
	}
}
func TestProductionPolicyHasHostedTrustAndNoBundle(t *testing.T) {
	public, _, _ := ed25519.GenerateKey(rand.Reader)
	p := profileFixture()
	key := manifest.Key{ID: "production-fixture", Public: public, NotBefore: p.KeyNotBefore, NotAfter: p.KeyNotAfter}
	b, err := productionSource(p, key, manifest.Manifest{Files: []manifest.File{{Path: "dinput8.dll"}}})
	if err != nil {
		t.Fatal(err)
	}
	if _, err = parser.ParseFile(token.NewFileSet(), "policy.go", b, 0); err != nil {
		t.Fatal(err)
	}
	for _, expected := range []string{"//go:build production", "EnvelopeURL:", "RelayURL:", "GuideURL:"} {
		if !strings.Contains(string(b), expected) {
			t.Fatal("missing", expected)
		}
	}
	if strings.Contains(string(b), "Bundle:") || strings.Contains(string(b), "local-qa-") {
		t.Fatal("QA authority leaked")
	}
}

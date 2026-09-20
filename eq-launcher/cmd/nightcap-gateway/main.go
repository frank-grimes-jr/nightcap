package main

import (
	"log"
	"net/http"
	"net/netip"
	"os"
	"strings"
	"time"

	"nightcap/eq-launcher/internal/gametunnel"
)

func prefixes(name string, required bool) []netip.Prefix {
	raw := strings.Fields(os.Getenv(name))
	if required && len(raw) == 0 {
		log.Fatalf("%s is required", name)
	}
	p, err := gametunnel.Prefixes(raw)
	if err != nil {
		log.Fatalf("invalid %s", name)
	}
	return p
}
func main() {
	target := os.Getenv("GAME_TARGET")
	if target == "" {
		log.Fatal("GAME_TARGET is required")
	}
	g := &gametunnel.Gateway{Target: target, TrustedProxies: prefixes("TRUSTED_PROXIES", true), Allow: prefixes("ALLOW_CIDRS", true), Deny: prefixes("DENY_CIDRS", false)}
	s := &http.Server{Addr: ":8080", Handler: g, ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 8192}
	log.Print("Nightcap gateway listening; only trusted proxy and approved player addresses are accepted")
	log.Fatal(s.ListenAndServe())
}

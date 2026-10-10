package main

import (
	"log"
	"net/http"
	"net/netip"
	"os"
	"strings"
	"time"

	"nightcap/eq-launcher/internal/gametunnel"
	"nightcap/eq-launcher/internal/playeraccess"
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
	access, err := playeraccess.Open(os.Getenv("PLAYER_ACCESS_FILE"))
	if err != nil {
		log.Fatal("PLAYER_ACCESS_FILE must identify a valid player credential registry")
	}
	go func() {
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()
		healthy := true
		for range ticker.C {
			next := access.Refresh() == nil
			if next != healthy {
				log.Printf("player credential registry available=%t", next)
				healthy = next
			}
		}
	}()
	g := &gametunnel.Gateway{Target: target, TrustedProxies: prefixes("TRUSTED_PROXIES", true), Access: access, Deny: prefixes("DENY_CIDRS", false)}
	s := newServer(g)
	log.Print("Nightcap gateway listening; trusted proxy and player credentials required")
	log.Fatal(s.ListenAndServe())
}

func newServer(handler http.Handler) *http.Server {
	// Bound unauthenticated request bodies and responses as well as headers.
	// The WebSocket upgrader clears HTTP deadlines after a successful upgrade;
	// the relay then owns its independent ping/read/write deadlines.
	return &http.Server{Addr: ":8080", Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 15 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 8192}
}

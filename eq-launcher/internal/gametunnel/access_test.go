package gametunnel

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"nightcap/eq-launcher/internal/playeraccess"
)

func testAccess(t *testing.T) (*playeraccess.Store, string, func()) {
	t.Helper()
	token, record, err := playeraccess.Generate("joe")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "access.json")
	raw, _ := json.Marshal(playeraccess.Registry{Version: 1, Credentials: []playeraccess.Record{record}})
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	store, err := playeraccess.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	return store, token, func() {
		t.Helper()
		if err := os.WriteFile(path, []byte(`{"version":1,"credentials":[]}`), 0600); err != nil {
			t.Fatal(err)
		}
		if err := store.Refresh(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestGatewayCredentialSurvivesIPChangesAndRevocationClosesSession(t *testing.T) {
	store, token, revoke := testAccess(t)
	proxy, _ := Prefixes([]string{"127.0.0.1/32"})
	g := &Gateway{TrustedProxies: proxy, Access: store}
	s := httptest.NewServer(g)
	defer s.Close()
	var connections []*websocket.Conn
	for _, ip := range []string{"198.51.100.1", "203.0.113.9", "2001:db8:1::42", "2001:db8:2::99"} {
		h := http.Header{"Cf-Connecting-Ip": {ip}, "Authorization": {"Bearer " + token}}
		c, response, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(s.URL, "http")+"/connect", h)
		if err != nil {
			if response != nil {
				response.Body.Close()
			}
			t.Fatal("IP change rejected", ip, err)
		}
		connections = append(connections, c)
		defer c.Close()
	}
	g.mu.Lock()
	count := g.sessions["joe"]
	g.mu.Unlock()
	if count != 4 {
		t.Fatalf("sessions not counted by player across IPs: %d", count)
	}
	revoke()
	for _, c := range connections {
		c.SetReadDeadline(time.Now().Add(4 * time.Second))
		_, _, err := c.ReadMessage()
		if err == nil {
			t.Fatal("revoked session survived")
		}
		if e, ok := err.(interface{ Timeout() bool }); ok && e.Timeout() {
			t.Fatal("revocation did not close active session")
		}
	}
	r := httptest.NewRequest("GET", "/connect", nil)
	r.RemoteAddr = "127.0.0.1:1234"
	r.Header.Set("CF-Connecting-IP", "198.51.100.1")
	r.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	g.ServeHTTP(w, r)
	if w.Code != 401 {
		t.Fatalf("revoked reconnect status %d", w.Code)
	}
}

func TestGatewayRequiresSingleCredentialEvenFromPreviouslyApprovedAddress(t *testing.T) {
	store, token, _ := testAccess(t)
	proxy, _ := Prefixes([]string{"127.0.0.1/32"})
	g := &Gateway{TrustedProxies: proxy, Access: store}
	for _, values := range [][]string{nil, {"Bearer wrong"}, {"Bearer " + token, "Bearer " + token}, {"Basic " + token}} {
		r := httptest.NewRequest("GET", "/connect", nil)
		r.RemoteAddr = "127.0.0.1:1234"
		r.Header.Set("CF-Connecting-IP", "76.119.26.170")
		r.Header["Authorization"] = values
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if w.Code != 401 {
			t.Fatalf("missing/bad credential status %d", w.Code)
		}
		if strings.Contains(w.Body.String(), token) {
			t.Fatal("secret echoed")
		}
	}
}

func TestGatewayPlayerLimitsCannotBeBypassedByChangingIP(t *testing.T) {
	g := &Gateway{}
	for i := 0; i < 10; i++ {
		if !g.acquire("joe") {
			t.Fatal("early limit")
		}
	}
	if g.acquire("joe") {
		t.Fatal("player limit bypassed")
	}
	if !g.acquire("another-player") {
		t.Fatal("unrelated player blocked")
	}
	g.release("joe")
	if !g.acquire("joe") {
		t.Fatal("released slot not reusable")
	}
}

package gametunnel

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"nightcap/eq-launcher/internal/playeraccess"
)

func TestClientSendsCredentialOnlyToValidatedTLSRelay(t *testing.T) {
	token, _, _ := playeraccess.Generate("joe")
	for _, status := range []int{101, 401, 403, 429, 302} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			calls := 0
			s := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				calls++
				if r.URL.Path != "/connect" || r.URL.RawQuery != "" || r.Header.Get("Authorization") != "Bearer "+token {
					t.Error("credential transport contract violated")
				}
				if status == 101 {
					u := websocket.Upgrader{}
					c, err := u.Upgrade(w, r, nil)
					if err == nil {
						c.Close()
					}
					return
				}
				if status == 302 {
					w.Header().Set("Location", "https://elsewhere.test/connect")
				}
				w.WriteHeader(status)
			}))
			defer s.Close()
			roots := x509.NewCertPool()
			roots.AddCert(s.Certificate())
			d := &websocket.Dialer{HandshakeTimeout: time.Second, TLSClientConfig: &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12}, NetDialContext: func(ctx context.Context, network, address string) (net.Conn, error) {
				if address != "example.com:443" {
					t.Error("redirect followed")
				}
				return (&net.Dialer{}).DialContext(ctx, network, s.Listener.Addr().String())
			}}
			c, err := dialAuthenticated(context.Background(), "https://example.com/connect", []string{"example.com"}, token, d)
			if status == 101 {
				if err != nil {
					t.Fatal(err)
				}
				c.Close()
			} else {
				if err == nil || strings.Contains(err.Error(), token) {
					t.Fatal("HTTP failure missing or leaks secret")
				}
				if status == 401 && !strings.Contains(err.Error(), "access code was rejected") {
					t.Fatal(err)
				}
				if status == 403 && !strings.Contains(err.Error(), "HTTP 403") {
					t.Fatal(err)
				}
			}
			if calls != 1 {
				t.Fatalf("unexpected request count %d", calls)
			}
			for _, bad := range []string{"https://elsewhere.test/connect", "http://example.com/connect", "https://example.com/connect?token=secret"} {
				if c, err := dialAuthenticated(context.Background(), bad, []string{"example.com"}, token, d); err == nil {
					c.Close()
					t.Fatal("unsafe destination accepted")
				}
			}
			if calls != 1 {
				t.Fatal("credential sent to unvalidated destination")
			}
		})
	}
}

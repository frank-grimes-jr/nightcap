package gametunnel

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func TestProtocolRejectsUnboundedAndForeignDestinations(t *testing.T) {
	for _, p := range []packet{{3306, 1, []byte("secret")}, {9001, 1, []byte("admin")}, {7000, 0, []byte("x")}, {7000, 1, make([]byte, MaxPayload+1)}} {
		if _, err := decode(encode(p)); err == nil {
			t.Fatal("unsafe packet accepted")
		}
	}
	for _, port := range Ports() {
		p := packet{uint16(port), 12, []byte("hello")}
		got, err := decode(encode(p))
		if err != nil || got.flow != 12 || string(got.data) != "hello" {
			t.Fatal("roundtrip", err)
		}
	}
}
func TestGatewayRejectsUntrustedAndDeniedClients(t *testing.T) {
	proxy, _ := Prefixes([]string{"127.0.0.1/32"})
	access, token, _ := testAccess(t)
	deny, _ := Prefixes([]string{"198.51.100.2/32"})
	g := &Gateway{Target: "127.0.0.1", TrustedProxies: proxy, Access: access, Deny: deny}
	for _, c := range []struct {
		remote, ip, path, origin string
		status                   int
	}{
		{"10.0.0.1:123", "198.51.100.1", "/connect", "", 403},
		{"127.0.0.1:123", "198.51.100.2", "/connect", "", 403},
		{"127.0.0.1:123", "", "/connect", "", 403},
		{"127.0.0.1:123", "198.51.100.1", "/connect?target=secret", "", 400},
		{"127.0.0.1:123", "198.51.100.1", "/connect?", "", 400},
		{"127.0.0.1:123", "198.51.100.1", "/con%6eect", "", 400},
		{"127.0.0.1:123", "198.51.100.1", "/connect", "https://evil.test", 400},
	} {
		r := httptest.NewRequest("GET", c.path, nil)
		r.RemoteAddr = c.remote
		r.Header.Set("CF-Connecting-IP", c.ip)
		r.Header.Set("Origin", c.origin)
		r.Header.Set("Authorization", "Bearer "+token)
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if w.Code != c.status {
			t.Fatalf("got%d want%d", w.Code, c.status)
		}
	}
}
func TestTLSClientRejectsInvalidCertificateAndUnsafeURLs(t *testing.T) {
	for _, address := range []string{"http://nightcap.test/connect", "https://elsewhere.test/connect", "https://nightcap.test/connect?target=foo"} {
		if _, err := Start(context.Background(), address, []string{"nightcap.test"}, ""); err == nil {
			t.Fatal("unsafe URL accepted")
		}
	}
}

func TestUDPReaderFailureClosesRelay(t *testing.T) {
	broken := make(chan *net.UDPConn, 1)
	echo, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer echo.Close()
	g := &Gateway{dial: func(int) (*net.UDPConn, error) {
		c, e := net.DialUDP("udp4", nil, echo.LocalAddr().(*net.UDPAddr))
		if e == nil {
			broken <- c
		}
		return c, e
	}}
	u := websocket.Upgrader{}
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c, e := u.Upgrade(w, r, nil)
		if e == nil {
			g.serve(c)
		}
	}))
	defer s.Close()
	c, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(s.URL, "http"), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	c.SetReadDeadline(time.Now().Add(3 * time.Second))
	c.WriteMessage(websocket.BinaryMessage, encode(packet{7000, 1, []byte("start")}))
	select {
	case socket := <-broken:
		socket.Close()
	case <-time.After(3 * time.Second):
		t.Fatal("flow was not opened")
	}
	_, _, err = c.ReadMessage()
	if err == nil {
		t.Fatal("broken flow silently survived")
	}
	if e, ok := err.(net.Error); ok && e.Timeout() {
		t.Fatal("reader failed without closing relay")
	}
}
func TestGatewayFlowIsolationAndDisconnect(t *testing.T) {
	// Test-only dial seam uses an ephemeral UDP port; production never permits it.
	echo, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer echo.Close()
	go func() {
		b := make([]byte, 1024)
		for {
			n, a, e := echo.ReadFromUDP(b)
			if e != nil {
				return
			}
			echo.WriteToUDP(b[:n], a)
		}
	}()
	g := &Gateway{Target: "127.0.0.1", dial: func(int) (*net.UDPConn, error) { return net.DialUDP("udp4", nil, echo.LocalAddr().(*net.UDPAddr)) }}
	u := websocket.Upgrader{}
	s := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c, e := u.Upgrade(w, r, nil)
		if e == nil {
			g.serve(c)
		}
	}))
	defer s.Close()
	d := websocket.Dialer{TLSClientConfig: s.Client().Transport.(*http.Transport).TLSClientConfig}
	var sockets []*websocket.Conn
	for _, payload := range []string{"player-one", "player-two"} {
		c, _, e := d.Dial("wss"+strings.TrimPrefix(s.URL, "https"), nil)
		if e != nil {
			t.Fatal(e)
		}
		sockets = append(sockets, c)
		defer c.Close()
		c.SetReadDeadline(time.Now().Add(3 * time.Second))
		if e = c.WriteMessage(websocket.BinaryMessage, encode(packet{7000, 1, []byte(payload)})); e != nil {
			t.Fatal(e)
		}
	}
	for i, c := range sockets {
		_, raw, e := c.ReadMessage()
		if e != nil {
			t.Fatal(e)
		}
		p, e := decode(raw)
		if e != nil || string(p.data) != []string{"player-one", "player-two"}[i] {
			t.Fatal("cross-session routing", e)
		}
	}
	// An administrative destination tears down just that session.
	sockets[0].WriteMessage(websocket.BinaryMessage, encode(packet{3306, 2, []byte("bad")}))
	if _, _, e := sockets[0].ReadMessage(); e == nil {
		t.Fatal("disallowed flow survived")
	}
	sockets[1].WriteMessage(websocket.BinaryMessage, encode(packet{7000, 1, []byte("still-here")}))
	_, raw, e := sockets[1].ReadMessage()
	if e != nil {
		t.Fatal(e)
	}
	p, _ := decode(raw)
	if string(p.data) != "still-here" {
		t.Fatal("other session affected")
	}
}

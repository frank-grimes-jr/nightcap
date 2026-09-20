package gametunnel

import (
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func TestClientOwnsLoopbackAndClosesOnTransportLoss(t *testing.T) {
	upgrader := websocket.Upgrader{}
	remote := make(chan *websocket.Conn, 1)
	s := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c, e := upgrader.Upgrade(w, r, nil)
		if e != nil {
			return
		}
		defer c.Close()
		remote <- c
		for {
			k, b, e := c.ReadMessage()
			if e != nil {
				return
			}
			if e = c.WriteMessage(k, b); e != nil {
				return
			}
		}
	}))
	defer s.Close()
	d := websocket.Dialer{TLSClientConfig: s.Client().Transport.(*http.Transport).TLSClientConfig}
	conn, _, err := d.Dial("wss"+strings.TrimPrefix(s.URL, "https"), nil)
	if err != nil {
		t.Fatal(err)
	}
	client, err := startClientListening(conn, []int{7000}, func(int) (*net.UDPConn, error) {
		return net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	})
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	game, err := net.DialUDP("udp4", nil, client.sockets[0].LocalAddr().(*net.UDPAddr))
	if err != nil {
		t.Fatal(err)
	}
	defer game.Close()
	game.SetDeadline(time.Now().Add(3 * time.Second))
	game.Write([]byte("zone-packet"))
	b := make([]byte, 100)
	n, err := game.Read(b)
	if err != nil || string(b[:n]) != "zone-packet" {
		t.Fatal("local roundtrip", err)
	}
	(<-remote).Close()
	select {
	case <-client.Done():
	case <-time.After(3 * time.Second):
		t.Fatal("transport loss did not release listeners")
	}
	if _, err = client.sockets[0].WriteToUDP([]byte("x"), game.LocalAddr().(*net.UDPAddr)); err == nil {
		t.Fatal("listener survived disconnect")
	}
}

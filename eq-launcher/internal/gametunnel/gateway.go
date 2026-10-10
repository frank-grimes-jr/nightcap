package gametunnel

import (
	"fmt"
	"net"
	"net/http"
	"net/netip"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

// Gateway must only be reachable by a trusted reverse proxy on an isolated
// Docker network. Player admission uses independently revocable credentials.
type AccessVerifier interface {
	Authenticate(string) (string, bool)
}

type Gateway struct {
	Target               string
	dial                 func(int) (*net.UDPConn, error)
	TrustedProxies, Deny []netip.Prefix
	Access               AccessVerifier
	mu                   sync.Mutex
	sessions             map[string]int
	total                int
}

func contains(prefixes []netip.Prefix, ip netip.Addr) bool {
	for _, p := range prefixes {
		if p.Contains(ip) {
			return true
		}
	}
	return false
}
func (g *Gateway) acquire(player string) bool {
	g.mu.Lock()
	defer g.mu.Unlock()
	if g.total >= 20 || g.sessions[player] >= 10 {
		return false
	}
	if g.sessions == nil {
		g.sessions = map[string]int{}
	}
	g.sessions[player]++
	g.total++
	return true
}
func (g *Gateway) release(player string) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.total--
	g.sessions[player]--
	if g.sessions[player] == 0 {
		delete(g.sessions, player)
	}
}
func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	peer, e := netip.ParseAddr(host)
	ip, e2 := netip.ParseAddr(r.Header.Get("CF-Connecting-IP"))
	if err != nil || e != nil || e2 != nil || len(r.Header.Values("CF-Connecting-IP")) != 1 || !contains(g.TrustedProxies, peer.Unmap()) || contains(g.Deny, ip.Unmap()) {
		http.Error(w, "Access unavailable", http.StatusForbidden)
		return
	}
	if r.Method != "GET" || r.URL.Path != "/connect" || r.URL.RawQuery != "" || r.URL.ForceQuery || r.URL.RawPath != "" || r.Header.Get("Origin") != "" || r.ContentLength != 0 || len(r.TransferEncoding) != 0 {
		http.Error(w, "Invalid connection request", http.StatusBadRequest)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	values := r.Header.Values("Authorization")
	token := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
	player, authorized := "", false
	if g.Access != nil && len(values) == 1 && strings.HasPrefix(values[0], "Bearer ") {
		player, authorized = g.Access.Authenticate(token)
	}
	if !authorized || player == "" {
		w.Header().Set("WWW-Authenticate", `Bearer realm="Nightcap"`)
		http.Error(w, "Player access required", http.StatusUnauthorized)
		return
	}
	if !g.acquire(player) {
		http.Error(w, "Connection limit reached", http.StatusTooManyRequests)
		return
	}
	defer g.release(player)
	u := websocket.Upgrader{HandshakeTimeout: 10 * time.Second, CheckOrigin: func(r *http.Request) bool { return r.Header.Get("Origin") == "" }}
	c, err := u.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	// Revocation also closes established relays. This goroutine owns no game
	// state; the regular wire cleanup releases every UDP flow and session slot.
	done, checked := make(chan struct{}), make(chan struct{})
	go func() {
		defer close(checked)
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				current, ok := g.Access.Authenticate(token)
				if !ok || current != player {
					_ = c.Close()
					return
				}
			}
		}
	}()
	g.serve(c)
	close(done)
	<-checked
}

type remoteFlow struct {
	conn   *net.UDPConn
	port   uint16
	closed *atomic.Bool
}

func (g *Gateway) serve(conn *websocket.Conn) {
	w := newWire(conn)
	flows := map[uint32]remoteFlow{}
	// Only the reader owns this map; response goroutines own their socket reads.
	defer func() {
		w.close()
		for _, f := range flows {
			f.conn.Close()
		}
		w.wg.Wait()
	}()
	q := quota{}
	for {
		p, err := w.read()
		if err != nil || !q.accept(len(p.data)) {
			return
		}
		f, exists := flows[p.flow]
		if exists && f.closed.Load() {
			delete(flows, p.flow)
			exists = false
		}
		if exists && f.port != p.port {
			return
		}
		if !exists {
			for id, old := range flows {
				if old.closed.Load() {
					delete(flows, id)
				}
			}
			if len(flows) >= maxFlows {
				return
			}
			// Target is operator configuration, never read from a client frame.
			s, err := g.dialPort(int(p.port))
			if err != nil {
				return
			}
			f = remoteFlow{s, p.port, &atomic.Bool{}}
			flows[p.flow] = f
			w.wg.Add(1)
			go func(id uint32, f remoteFlow) {
				defer w.wg.Done()
				defer f.conn.Close()
				defer f.closed.Store(true)
				buffer := make([]byte, MaxPayload+1)
				for {
					_ = f.conn.SetReadDeadline(time.Now().Add(5 * time.Minute))
					n, err := f.conn.Read(buffer)
					if err != nil {
						if e, ok := err.(net.Error); !ok || !e.Timeout() {
							w.close()
						}
						return
					}
					if n == 0 || n > MaxPayload {
						continue
					}
					if err = w.send(packet{f.port, id, buffer[:n]}); err != nil {
						return
					}
				}
			}(p.flow, f)
		}
		_ = f.conn.SetWriteDeadline(time.Now().Add(5 * time.Second))
		if _, err = f.conn.Write(p.data); err != nil {
			return
		}
	}
}

func (g *Gateway) dialPort(port int) (*net.UDPConn, error) {
	if g.dial != nil {
		return g.dial(port)
	}
	destination, err := net.ResolveUDPAddr("udp4", net.JoinHostPort(g.Target, strconv.Itoa(port)))
	if err != nil {
		return nil, err
	}
	return net.DialUDP("udp4", nil, destination)
}

func Prefixes(raw []string) ([]netip.Prefix, error) {
	var result []netip.Prefix
	for _, s := range raw {
		p, err := netip.ParsePrefix(s)
		if err != nil {
			return nil, fmt.Errorf("invalid CIDR: %w", err)
		}
		result = append(result, p.Masked())
	}
	return result, nil
}

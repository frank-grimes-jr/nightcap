package gametunnel

import (
	"fmt"
	"net"
	"net/http"
	"net/netip"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

// Gateway must only be reachable by a trusted reverse proxy on an isolated
// Docker network. The executable requires explicit proxy and player CIDRs.
type Gateway struct {
	Target                      string
	dial                        func(int) (*net.UDPConn, error)
	TrustedProxies, Allow, Deny []netip.Prefix
	mu                          sync.Mutex
	sessions                    map[netip.Addr]int
	total                       int
}

func contains(prefixes []netip.Prefix, ip netip.Addr) bool {
	for _, p := range prefixes {
		if p.Contains(ip) {
			return true
		}
	}
	return false
}
func (g *Gateway) acquire(ip netip.Addr) bool {
	g.mu.Lock()
	defer g.mu.Unlock()
	if g.total >= 20 || g.sessions[ip] >= 10 {
		return false
	}
	if g.sessions == nil {
		g.sessions = map[netip.Addr]int{}
	}
	g.sessions[ip]++
	g.total++
	return true
}
func (g *Gateway) release(ip netip.Addr) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.total--
	g.sessions[ip]--
	if g.sessions[ip] == 0 {
		delete(g.sessions, ip)
	}
}
func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	peer, e := netip.ParseAddr(host)
	ip, e2 := netip.ParseAddr(r.Header.Get("CF-Connecting-IP"))
	if err != nil || e != nil || e2 != nil || !contains(g.TrustedProxies, peer.Unmap()) || contains(g.Deny, ip.Unmap()) || !contains(g.Allow, ip.Unmap()) {
		http.Error(w, "Access unavailable", http.StatusForbidden)
		return
	}
	if r.Method != "GET" || r.URL.Path != "/connect" || r.URL.RawQuery != "" || r.Header.Get("Origin") != "" {
		http.Error(w, "Invalid connection request", http.StatusBadRequest)
		return
	}
	if !g.acquire(ip) {
		http.Error(w, "Connection limit reached", http.StatusTooManyRequests)
		return
	}
	defer g.release(ip)
	u := websocket.Upgrader{HandshakeTimeout: 10 * time.Second, CheckOrigin: func(r *http.Request) bool { return r.Header.Get("Origin") == "" }}
	c, err := u.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	g.serve(c)
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

package gametunnel

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"nightcap/eq-launcher/internal/manifest"
)

type localFlow struct {
	socket  *net.UDPConn
	address *net.UDPAddr
	port    uint16
	last    time.Time
	key     string
}
type Client struct {
	w       *wire
	sockets []*net.UDPConn
	mu      sync.Mutex
	flows   map[uint32]localFlow
	ids     map[string]uint32
	next    uint32
	done    chan struct{}
}

// Start accepts only a compiled HTTPS endpoint and uses ordinary certificate
// validation. HTTPS is converted to WSS here; redirects are not followed.
func Start(ctx context.Context, address string, hosts []string) (*Client, error) {
	if err := manifest.ValidateURL(address, hosts); err != nil {
		return nil, err
	}
	u, _ := url.Parse(address)
	u.Scheme = "wss"
	d := websocket.Dialer{HandshakeTimeout: 15 * time.Second, TLSClientConfig: &tls.Config{MinVersion: tls.VersionTLS12}, Proxy: http.ProxyFromEnvironment}
	c, response, err := d.DialContext(ctx, u.String(), nil)
	if err != nil {
		if response != nil {
			response.Body.Close()
		}
		return nil, fmt.Errorf("secure Nightcap connection unavailable; check your Internet connection and approved IP: %w", err)
	}
	return startClient(c, Loopback, Ports())
}

func startClient(conn *websocket.Conn, address string, ports []int) (*Client, error) {
	return startClientListening(conn, ports, func(port int) (*net.UDPConn, error) {
		return net.ListenUDP("udp4", &net.UDPAddr{IP: net.ParseIP(address), Port: port})
	})
}

func startClientListening(conn *websocket.Conn, ports []int, listen func(int) (*net.UDPConn, error)) (*Client, error) {
	c := &Client{w: newWire(conn), flows: map[uint32]localFlow{}, ids: map[string]uint32{}, done: make(chan struct{})}
	for _, port := range ports {
		s, err := listen(port)
		if err != nil {
			for _, s := range c.sockets {
				s.Close()
			}
			c.w.close()
			c.w.wg.Wait()
			return nil, fmt.Errorf("Nightcap local port %d is in use: %w", port, err)
		}
		c.sockets = append(c.sockets, s)
	}
	for i, s := range c.sockets {
		c.w.wg.Add(1)
		go c.readLocal(s, uint16(ports[i]))
	}
	go func() {
		defer close(c.done)
		defer c.w.wg.Wait()
		defer func() {
			c.w.close()
			for _, s := range c.sockets {
				s.Close()
			}
		}()
		q := quota{}
		for {
			p, err := c.w.read()
			if err != nil || !q.accept(len(p.data)) {
				return
			}
			c.mu.Lock()
			f, ok := c.flows[p.flow]
			if ok {
				f.last = time.Now()
				c.flows[p.flow] = f
			}
			c.mu.Unlock()
			if !ok {
				continue
			}
			if f.port != p.port {
				return
			}
			if _, err = f.socket.WriteToUDP(p.data, f.address); err != nil {
				return
			}
		}
	}()
	return c, nil
}
func (c *Client) readLocal(s *net.UDPConn, port uint16) {
	defer c.w.wg.Done()
	buffer := make([]byte, MaxPayload+1)
	for {
		n, from, err := s.ReadFromUDP(buffer)
		if err != nil {
			c.w.close()
			return
		}
		if !from.IP.IsLoopback() || n == 0 || n > MaxPayload {
			continue
		}
		key := fmt.Sprintf("%d/%s", port, from.String())
		c.mu.Lock()
		for id, f := range c.flows {
			if time.Since(f.last) > 5*time.Minute {
				delete(c.ids, f.key)
				delete(c.flows, id)
			}
		}
		id := c.ids[key]
		if id == 0 && len(c.flows) < maxFlows {
			c.next++
			id = c.next
			c.ids[key] = id
			c.flows[id] = localFlow{s, from, port, time.Now(), key}
		}
		if id != 0 {
			f := c.flows[id]
			f.last = time.Now()
			c.flows[id] = f
		}
		c.mu.Unlock()
		if id == 0 {
			c.w.close()
			return
		}
		if err = c.w.send(packet{port, id, buffer[:n]}); err != nil {
			return
		}
	}
}
func (c *Client) Done() <-chan struct{} { return c.done }
func (c *Client) Close()                { c.w.close(); <-c.done }

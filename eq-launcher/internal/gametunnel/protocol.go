// Package gametunnel carries a fixed set of native game UDP services over WSS.
// It is not a general proxy: clients cannot select a host or an arbitrary port.
package gametunnel

import (
	"encoding/binary"
	"fmt"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const Loopback = "127.77.0.1"
const MaxPayload = 65507
const maxFlows = 128

func Ports() []int {
	p := []int{5998, 9000, 7778}
	for n := 7000; n <= 7030; n++ {
		p = append(p, n)
	}
	return p
}
func allowed(port int) bool {
	return port == 5998 || port == 9000 || port == 7778 || port >= 7000 && port <= 7030
}

type packet struct {
	port uint16
	flow uint32
	data []byte
}

func decode(raw []byte) (packet, error) {
	if len(raw) < 7 || len(raw) > MaxPayload+6 {
		return packet{}, fmt.Errorf("invalid datagram length")
	}
	p := packet{binary.BigEndian.Uint16(raw), binary.BigEndian.Uint32(raw[2:]), raw[6:]}
	if p.flow == 0 || !allowed(int(p.port)) {
		return packet{}, fmt.Errorf("invalid datagram destination")
	}
	return p, nil
}
func encode(p packet) []byte {
	b := make([]byte, 6+len(p.data))
	binary.BigEndian.PutUint16(b, p.port)
	binary.BigEndian.PutUint32(b[2:], p.flow)
	copy(b[6:], p.data)
	return b
}

type wire struct {
	conn    *websocket.Conn
	writeMu sync.Mutex
	stop    chan struct{}
	once    sync.Once
	wg      sync.WaitGroup
}

func newWire(c *websocket.Conn) *wire {
	w := &wire{conn: c, stop: make(chan struct{})}
	c.SetReadLimit(MaxPayload + 6)
	_ = c.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.SetPongHandler(func(string) error { return c.SetReadDeadline(time.Now().Add(60 * time.Second)) })
	w.wg.Add(1)
	go func() {
		defer w.wg.Done()
		timer := time.NewTicker(20 * time.Second)
		defer timer.Stop()
		for {
			select {
			case <-w.stop:
				return
			case <-timer.C:
				if err := c.WriteControl(websocket.PingMessage, nil, time.Now().Add(5*time.Second)); err != nil {
					w.close()
					return
				}
			}
		}
	}()
	return w
}
func (w *wire) close() { w.once.Do(func() { close(w.stop); _ = w.conn.Close() }) }
func (w *wire) send(p packet) error {
	w.writeMu.Lock()
	defer w.writeMu.Unlock()
	_ = w.conn.SetWriteDeadline(time.Now().Add(5 * time.Second))
	err := w.conn.WriteMessage(websocket.BinaryMessage, encode(p))
	if err != nil {
		w.close()
	}
	return err
}
func (w *wire) read() (packet, error) {
	k, raw, err := w.conn.ReadMessage()
	if err != nil {
		return packet{}, err
	}
	if k != websocket.BinaryMessage {
		return packet{}, fmt.Errorf("binary datagram required")
	}
	return decode(raw)
}

// A per-session fixed-window ceiling bounds traffic even after the WAF upgrade.
type quota struct {
	start        time.Time
	count, bytes int
}

func (q *quota) accept(n int) bool {
	now := time.Now()
	if now.Sub(q.start) >= time.Second {
		q.start = now
		q.count = 0
		q.bytes = 0
	}
	q.count++
	q.bytes += n
	return q.count <= 2000 && q.bytes <= 4<<20
}

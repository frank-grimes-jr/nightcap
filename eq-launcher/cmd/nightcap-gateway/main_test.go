package main

import (
	"bufio"
	"net"
	"net/http"
	"strings"
	"testing"
	"time"
)

func TestRejectedSlowBodyIsBoundedBeforeAuthentication(t *testing.T) {
	s := newServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "Access unavailable", http.StatusForbidden)
	}))
	if s.ReadTimeout <= 0 || s.ReadTimeout > 10*time.Second || s.WriteTimeout <= 0 || s.WriteTimeout > 15*time.Second {
		t.Fatal("public HTTP request deadlines are missing or excessive")
	}
	// Accelerate only the already-validated production duration for this test.
	s.ReadTimeout = 100 * time.Millisecond
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	go s.Serve(l)
	c, err := net.Dial("tcp", l.Addr().String())
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	c.SetDeadline(time.Now().Add(time.Second))
	_, err = c.Write([]byte("GET /connect HTTP/1.1\r\nHost: test\r\nContent-Length: 1\r\n\r\n"))
	if err != nil {
		t.Fatal(err)
	}
	line, err := bufio.NewReader(c).ReadString('\n')
	if err != nil || !strings.Contains(line, "403") {
		t.Fatal("incomplete unauthenticated body held response", err)
	}
}

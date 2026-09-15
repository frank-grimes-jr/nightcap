package session

import (
	"context"
	"errors"
	"testing"
)

func TestClosePreservesCleanupFailure(t *testing.T) {
	cleanupErr := errors.New("lock release failed")
	s := &Session{stop: make(chan struct{}), done: make(chan struct{}), err: errors.Join(ErrStopped, cleanupErr)}
	close(s.done)
	if err := s.Close(context.Background()); !errors.Is(err, cleanupErr) {
		t.Fatalf("cleanup failure hidden: %v", err)
	}
}
func TestCloseAcceptsCleanStop(t *testing.T) {
	s := &Session{stop: make(chan struct{}), done: make(chan struct{}), err: ErrStopped}
	close(s.done)
	if err := s.Close(context.Background()); err != nil {
		t.Fatal(err)
	}
}

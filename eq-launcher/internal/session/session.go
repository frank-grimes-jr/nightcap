// Package session owns one verified helper/client session. It does not expose
// Play in the UI or replace the complete multiclass acceptance/release gates.
package session

import (
	"context"
	"errors"
	"sync"
)

var ErrStopped = errors.New("client session stopped")

type Identity struct {
	PID     uint32
	Created uint64
}
type Exit struct {
	Identity Identity
	Code     uint32
}

// Session may already be completed when Start returns (a client can exit fast).
// Done closes only after all owned processes exited and installation locks closed.
type Session struct {
	identity Identity
	stop     chan struct{}
	once     sync.Once
	done     chan struct{}
	exit     Exit
	err      error
}

func (s *Session) Identity() Identity    { return s.identity }
func (s *Session) Done() <-chan struct{} { return s.done }
func (s *Session) Wait(ctx context.Context) (Exit, error) {
	select {
	case <-s.done:
		return s.exit, s.err
	case <-ctx.Done():
		return Exit{}, ctx.Err()
	}
}

// Close is idempotent and safe concurrently with Wait. A timed-out caller leaves
// the owner cleaning up with all file locks retained; it never releases live files.
func (s *Session) Close(ctx context.Context) error {
	s.once.Do(func() { close(s.stop) })
	_, err := s.Wait(ctx)
	if err == ErrStopped {
		return nil
	}
	return err
}

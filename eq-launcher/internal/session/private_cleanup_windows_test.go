package session

import (
	"context"
	"errors"
	"testing"
)

func TestFailedStartupPreservesLoginRestoreError(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	restoreErr := errors.New("fixture eqhost restore conflict")
	_, err := startPrepared(ctx, launchInputs{close: func() error { return restoreErr }})
	if !errors.Is(err, context.Canceled) || !errors.Is(err, restoreErr) {
		t.Fatalf("cleanup error lost: %v", err)
	}
}

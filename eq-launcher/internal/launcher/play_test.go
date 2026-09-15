package launcher

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
	"nightcap/eq-launcher/internal/session"
)

type testSession struct {
	done     chan struct{}
	closing  chan struct{}
	release  chan struct{}
	once     sync.Once
	exit     session.Exit
	err      error
	closeErr error
}

func (s *testSession) Done() <-chan struct{} { return s.done }
func (s *testSession) Wait(ctx context.Context) (session.Exit, error) {
	select {
	case <-s.done:
		return s.exit, s.err
	case <-ctx.Done():
		return session.Exit{}, ctx.Err()
	}
}
func (s *testSession) Close(ctx context.Context) error {
	s.once.Do(func() { close(s.closing) })
	select {
	case <-s.release:
		close(s.done)
		return s.closeErr
	case <-ctx.Done():
		return ctx.Err()
	}
}
func playFixture(t *testing.T) (*Controller, *testSession) {
	c, _, _ := fixture(t)
	c.policy.EnablePlay = true
	for _, name := range []string{installer.HelperPath, "dinput8.dll", preflight.ConfigPath, preflight.CatalogPath} {
		c.policy.Trust.Inventory[name] = true
	}
	s := &testSession{done: make(chan struct{}), closing: make(chan struct{}), release: make(chan struct{})}
	c.start = func(context.Context, string, manifest.Trust) (gameSession, error) { return s, nil }
	return c, s
}
func awaitPhase(t *testing.T, c *Controller, phase string) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if c.Snapshot().Phase == phase {
			return
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatalf("phase %s not reached: %+v", phase, c.Snapshot())
}
func TestPlayRejectsPreviewAndIncompletePolicy(t *testing.T) {
	for _, missing := range []string{"enable", installer.HelperPath, preflight.ConfigPath, preflight.CatalogPath, "dinput8.dll"} {
		t.Run(missing, func(t *testing.T) {
			c, _ := playFixture(t)
			if missing == "enable" {
				c.policy.EnablePlay = false
			} else {
				delete(c.policy.Trust.Inventory, missing)
			}
			c.start = func(context.Context, string, manifest.Trust) (gameSession, error) {
				t.Fatal("unauthorized start")
				return nil, nil
			}
			if err := c.Play(context.Background()); err == nil {
				t.Fatal("disabled policy accepted")
			}
			if c.Snapshot().Busy || c.Snapshot().CanPlay {
				t.Fatal("unsafe policy state")
			}
		})
	}
}
func TestPlayOwnsBusyThroughCancellationCleanup(t *testing.T) {
	c, s := playFixture(t)
	done := make(chan error, 1)
	go func() { done <- c.Play(context.Background()) }()
	awaitPhase(t, c, "playing")
	if !c.Snapshot().Busy || c.Snapshot().CanUpdate || c.Snapshot().CanPlay {
		t.Fatal("running session not serialized")
	}
	for _, action := range []func() error{func() error { return c.Play(context.Background()) }, func() error { return c.Check(context.Background()) }, func() error { return c.Update(context.Background()) }, func() error { return c.Recover(context.Background()) }, func() error { return c.SelectClient(context.Background(), "other") }} {
		if err := action(); !errors.Is(err, ErrBusy) {
			t.Fatal("concurrent operation admitted", err)
		}
	}
	c.Cancel()
	<-s.closing
	if !c.Snapshot().Busy {
		t.Fatal("cleanup released controller early")
	}
	close(s.release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	if c.Snapshot().Busy || c.Snapshot().Phase != "stopped" {
		t.Fatal("stop state missing")
	}
}
func TestPlayUsesFreshOfflineTrustAndReportsExit(t *testing.T) {
	c, s := playFixture(t)
	c.policy.Trust.Now = time.Time{}
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) {
		t.Fatal("Play fetched network metadata")
		return nil, manifest.Signature{}, nil
	}
	c.start = func(ctx context.Context, dir string, trust manifest.Trust) (gameSession, error) {
		if trust.Now.IsZero() || time.Since(trust.Now) > time.Second || dir != c.Snapshot().ClientDir {
			t.Fatal("stale trust/directory")
		}
		return s, nil
	}
	s.exit.Code = 17
	close(s.done)
	if err := c.Play(context.Background()); err == nil {
		t.Fatal("abnormal exit hidden")
	}
	if c.Snapshot().Busy || c.Snapshot().Phase != "error" {
		t.Fatal("exit failure missing")
	}
}
func TestPlayPropagatesCleanupFailure(t *testing.T) {
	c, s := playFixture(t)
	s.closeErr = errors.New("cleanup failure")
	done := make(chan error, 1)
	go func() { done <- c.Play(context.Background()) }()
	awaitPhase(t, c, "playing")
	c.Cancel()
	<-s.closing
	close(s.release)
	if err := <-done; !errors.Is(err, s.closeErr) {
		t.Fatal("cleanup error hidden", err)
	}
}
func TestPlayStartupCancellationAndFailure(t *testing.T) {
	c, _ := playFixture(t)
	entered := make(chan struct{})
	c.start = func(ctx context.Context, _ string, _ manifest.Trust) (gameSession, error) {
		close(entered)
		<-ctx.Done()
		return nil, ctx.Err()
	}
	done := make(chan error, 1)
	go func() { done <- c.Play(context.Background()) }()
	<-entered
	c.Cancel()
	if err := <-done; !errors.Is(err, context.Canceled) {
		t.Fatal(err)
	}
	if c.Snapshot().Busy {
		t.Fatal("cancel left busy")
	}
	c.start = func(context.Context, string, manifest.Trust) (gameSession, error) {
		return nil, errors.New("changed release rejected")
	}
	if err := c.Play(context.Background()); err == nil {
		t.Fatal("failed startup hidden")
	}
}
func TestSelectionFindsCachedOfflineCandidate(t *testing.T) {
	c, _ := playFixture(t)
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{Present: true, Current: true, Release: 2}, nil
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	if !c.Snapshot().CanPlay {
		t.Fatal("cached candidate not offered")
	}
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) {
		return nil, manifest.Signature{}, errors.New("offline")
	}
	if err := c.Check(context.Background()); err == nil {
		t.Fatal("expected network failure")
	}
	if !c.Snapshot().CanPlay {
		t.Fatal("network failure blocked cached candidate")
	}
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{RecoveryRequired: true}, nil
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	if c.Snapshot().CanPlay || !c.Snapshot().CanRecover {
		t.Fatal("recovery not gated")
	}
}

func TestCancelAtStartReturnStillWaitsForCleanup(t *testing.T) {
	c, s := playFixture(t)
	c.start = func(context.Context, string, manifest.Trust) (gameSession, error) { c.Cancel(); return s, nil }
	done := make(chan error, 1)
	go func() { done <- c.Play(context.Background()) }()
	<-s.closing
	if !c.Snapshot().Busy || c.Snapshot().Phase != "stopping" {
		t.Fatal("startup race lost session ownership")
	}
	close(s.release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}
func TestExpiredPolicyAndNewFolderClearPlayEligibility(t *testing.T) {
	c, _ := playFixture(t)
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{Present: true, Current: true, Release: 2}, nil
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	if !c.Snapshot().CanPlay {
		t.Fatal("valid fixture disabled")
	}
	c.policy.Trust.Keys[0].NotAfter = time.Now().Add(-time.Second)
	if c.Snapshot().CanPlay {
		t.Fatal("expired policy enabled")
	}
	c.policy.Trust.Keys[0].NotAfter = time.Now().Add(time.Hour)
	c.local = func(context.Context, string, manifest.Trust) (installer.Inspection, error) {
		return installer.Inspection{}, errors.New("invalid local state")
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); err == nil {
		t.Fatal("inspection failure ignored")
	}
	if c.Snapshot().CanPlay || c.Snapshot().InstalledRelease != 0 {
		t.Fatal("previous folder lent launch eligibility")
	}
}
func TestPlayFastSuccessfulExit(t *testing.T) {
	c, s := playFixture(t)
	close(s.done)
	if err := c.Play(context.Background()); err != nil {
		t.Fatal(err)
	}
	if c.Snapshot().Busy || c.Snapshot().Phase != "stopped" {
		t.Fatal("fast exit lost")
	}
}

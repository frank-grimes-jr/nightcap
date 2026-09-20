package launcher

import (
	"context"
	"errors"
	"fmt"
	"time"

	"nightcap/eq-launcher/internal/gametunnel"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/session"
)

// This private seam lets controller tests own disposable sessions. Wails never
// accepts an implementation, policy, nonce, PID or bootstrap address from callers.
type gameSession interface {
	Done() <-chan struct{}
	Wait(context.Context) (session.Exit, error)
	Close(context.Context) error
}

func (c *Controller) inspectLocal(ctx context.Context, dir string, trust manifest.Trust) (installer.Inspection, error) {
	local, err := c.local(ctx, dir, trust)
	c.mu.Lock()
	c.state.RecoveryRequired = local.RecoveryRequired
	c.state.InstalledRelease = local.Release
	c.locallyCurrent = err == nil && local.Present && local.Current && !local.RecoveryRequired
	c.mu.Unlock()
	return local, err
}

// Play remains pending for the complete session. Busy excludes updates and folder
// changes until all owned processes exit and their verified lease is released.
// Start freshly verifies the cached signed release; production also opens its relay.
func (c *Controller) Play(ctx context.Context) (err error) {
	ctx, dir, err := c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	if !c.policy.playConfigured() {
		return fmt.Errorf("game launch is unavailable in this preview")
	}
	if dir == "" {
		return fmt.Errorf("choose your EverQuest folder first")
	}
	trust := c.policy.Trust
	trust.Now = time.Now().UTC()
	if c.policy.AutomaticUpdates {
		trust, err = c.updatePrepared(ctx, dir, true)
		if err != nil {
			return err
		}
	}
	if err = ctx.Err(); err != nil {
		return err
	}
	c.show("launching", "Verifying your installed release and starting Nightcap…")
	var disconnected <-chan struct{}
	if c.policy.RelayURL != "" {
		tunnel, e := gametunnel.Start(ctx, c.policy.RelayURL, c.policy.Trust.Hosts)
		if e != nil {
			return e
		}
		defer tunnel.Close()
		disconnected = tunnel.Done()
	}
	trust.Now = time.Now().UTC()
	active, err := c.start(ctx, dir, trust)
	if err != nil {
		return err
	}
	c.show("playing", "Nightcap is running. Keep this launcher open while playing.")
	select {
	case <-disconnected:
		return errors.Join(fmt.Errorf("secure Nightcap connection closed; reconnect with Play"), active.Close(context.Background()))
	case <-ctx.Done():
		c.show("stopping", "Stopping Nightcap. Keep the launcher open until cleanup finishes.")
		// A UI/request timeout must not release the controller while cleanup owns files.
		if err = active.Close(context.Background()); err != nil {
			return err
		}
	case <-active.Done():
		var outcome session.Exit
		outcome, err = active.Wait(context.Background())
		if err != nil {
			return err
		}
		if outcome.Code != 0 {
			return fmt.Errorf("Nightcap exited unexpectedly (code %d)", outcome.Code)
		}
	}
	c.show("stopped", "Nightcap closed. You can launch again or close the launcher.")
	return nil
}

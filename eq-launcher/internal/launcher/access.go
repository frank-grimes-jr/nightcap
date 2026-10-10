package launcher

import (
	"context"
	"fmt"
	"strings"

	"nightcap/eq-launcher/internal/playeraccess"
)

// SetAccessCode never places a credential in the status/event payload exposed to
// Wails. The code is checked by the gateway on Play; saving is not authorization.
func (c *Controller) SetAccessCode(ctx context.Context, code string) (err error) {
	ctx, _, err = c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	if c.policy.RelayURL == "" {
		return fmt.Errorf("player access is not required in this launcher")
	}
	if err = ctx.Err(); err != nil {
		return err
	}
	if err = playeraccess.SaveCredential(c.home, strings.TrimSpace(code)); err != nil {
		return err
	}
	c.mu.Lock()
	c.state.AccessSaved = true
	c.eventLocked("Access code saved securely for this Windows account.")
	c.mu.Unlock()
	return nil
}

func (c *Controller) ForgetAccessCode(ctx context.Context) (err error) {
	ctx, _, err = c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	if err = ctx.Err(); err != nil {
		return err
	}
	if err = playeraccess.ForgetCredential(c.home); err != nil {
		return err
	}
	c.mu.Lock()
	c.state.AccessSaved = false
	c.eventLocked("Access code removed from this Windows account.")
	c.mu.Unlock()
	return nil
}

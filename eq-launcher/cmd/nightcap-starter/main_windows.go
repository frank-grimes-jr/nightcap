// Nightcap's stable entry point. Trust comes only from the compiled production policy.
package main

import (
	"context"
	"fmt"
	"nightcap/eq-launcher/internal/launcher"
	"nightcap/eq-launcher/internal/selfupdate"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	p := launcher.DefaultPolicy()
	if !p.EnablePlay || p.EnvelopeURL == "" {
		showError("This starter has no production update configuration.")
		return
	}
	home, err := os.UserCacheDir()
	if err != nil {
		showError(err.Error())
		return
	}
	cache := filepath.Join(home, "NightcapLauncher", "applications")
	lock, err := selfupdate.Lock(cache)
	if err != nil {
		showError(err.Error())
		return
	}
	defer lock.Close()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	err = progressWindow(cancel, func(status func(string), hide func()) error {
		lease, err := selfupdate.Prepare(ctx, cache, strings.TrimSuffix(p.EnvelopeURL, "/channel.json")+"/launcher-channel.json", p.Trust, status)
		if err != nil {
			return err
		}
		defer lease.Close()
		if err = ctx.Err(); err != nil {
			return err
		}
		cmd, err := selfupdate.StartDesktop(lease)
		if err != nil {
			return fmt.Errorf("cannot start Nightcap: %w", err)
		}
		hide()
		return cmd.Wait()
	})
	if err != nil && ctx.Err() == nil {
		showError("Nightcap could not open. Your game files have not been changed by the starter.\n\n" + err.Error() + "\n\nTry opening Nightcap again. If this continues, contact the server owner.")
	}
}

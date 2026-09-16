//go:build qacandidate

// Runs the same controller as the desktop UI, against an explicit QA client.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"nightcap/eq-launcher/internal/launcher"
	"os"
	"path/filepath"
	"time"
)

func main() {
	client := flag.String("client", "", "absolute QA client copy")
	home := flag.String("home", "", "absolute QA launcher-state directory")
	action := flag.String("action", "check", "check, update or play")
	hold := flag.Duration("hold", 20*time.Second, "time to observe a running game before owned cleanup")
	flag.Parse()
	if !filepath.IsAbs(*client) || !filepath.IsAbs(*home) {
		fmt.Fprintln(os.Stderr, "absolute QA paths required")
		os.Exit(1)
	}
	c, err := launcher.New(*home, launcher.DefaultPolicy())
	if err == nil {
		err = c.SelectClient(context.Background(), *client)
	}
	emit := func() { raw, _ := json.Marshal(c.Snapshot()); fmt.Println(string(raw)) }
	if err == nil {
		switch *action {
		case "check":
			err = c.Check(context.Background())
		case "update":
			err = c.Update(context.Background())
		case "play":
			done := make(chan error, 1)
			go func() { done <- c.Play(context.Background()) }()
			ticker := time.NewTicker(250 * time.Millisecond)
			defer ticker.Stop()
			deadline := time.NewTimer(60 * time.Second)
			defer deadline.Stop()
			phase := ""
			finished := false
			for !finished {
				select {
				case err = <-done:
					finished = true
				case <-ticker.C:
					s := c.Snapshot()
					if s.Phase != phase {
						phase = s.Phase
						emit()
						if phase == "playing" {
							deadline.Reset(*hold)
						}
					}
				case <-deadline.C:
					c.Cancel()
					err = <-done
					finished = true
				}
			}
		default:
			err = fmt.Errorf("unknown action")
		}
	}
	if c != nil {
		emit()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

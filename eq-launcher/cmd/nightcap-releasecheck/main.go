// Verifies channel files against the same compiled policy as the shipped starter.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"nightcap/eq-launcher/internal/launcher"
	"nightcap/eq-launcher/internal/selfupdate"
	"os"
	"time"
)

func main() {
	name := flag.String("launcher-channel", "", "local launcher-channel.json")
	flag.Parse()
	raw, err := os.ReadFile(*name)
	p := launcher.DefaultPolicy()
	p.Trust.Now = time.Now().UTC()
	var c selfupdate.Channel
	if err == nil {
		c, err = selfupdate.Verify(raw, p.Trust, selfupdate.Checkpoint{})
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	json.NewEncoder(os.Stdout).Encode(c)
}

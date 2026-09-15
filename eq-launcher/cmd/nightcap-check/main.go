// nightcap-check is a read-only development preflight, not the finished launcher.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"nightcap/eq-launcher/internal/client"
	"os"
)

func main() {
	filename := flag.String("client", "", "Path to the player's existing eqgame.exe (read-only)")
	flag.Parse()
	if *filename == "" {
		flag.Usage()
		os.Exit(2)
	}
	report, err := client.Inspect(*filename)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := json.NewEncoder(os.Stdout).Encode(report); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if !report.Supported {
		os.Exit(2)
	}
}

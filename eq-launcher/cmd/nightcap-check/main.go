// nightcap-check is a read-only development preflight, not the finished launcher.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/preflight"
	"os"
)

func main() {
	filename := flag.String("client", "", "Path to the player's existing eqgame.exe (read-only)")
	configPath := flag.String("config", "", "Optional Nightcap patch configuration (requires -catalog)")
	catalogPath := flag.String("catalog", "", "Optional exact patch metadata (requires -config)")
	flag.Parse()
	if *filename == "" {
		flag.Usage()
		os.Exit(2)
	}
	if *configPath != "" || *catalogPath != "" {
		if *configPath == "" || *catalogPath == "" {
			fmt.Fprintln(os.Stderr, "-config and -catalog must be supplied together")
			os.Exit(2)
		}
		config, err := readLimited(*configPath, preflight.MaxConfigBytes)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		metadata, err := readLimited(*catalogPath, preflight.MaxCatalogBytes)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		file, err := os.Open(*filename)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		report, err := preflight.CheckOpen(file, config, metadata)
		closeErr := file.Close()
		if encodeErr := json.NewEncoder(os.Stdout).Encode(report); encodeErr != nil {
			fmt.Fprintln(os.Stderr, encodeErr)
			os.Exit(1)
		}
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		if closeErr != nil {
			fmt.Fprintln(os.Stderr, closeErr)
			os.Exit(1)
		}
		return
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

func readLimited(path string, limit int64) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("preflight input is not a bounded regular file: %s", path)
	}
	data, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("preflight input too large: %s", path)
	}
	return data, nil
}

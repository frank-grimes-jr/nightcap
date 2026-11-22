// Package hailstone runs the optional client distributed inside the signed desktop launcher.
package hailstone

import (
	"archive/zip"
	"bytes"
	"context"
	"embed"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

//go:embed payload/*
var bundle embed.FS

const archive = "payload/nightcap-hailstone.zip"

func Available() bool {
	_, err := fs.Stat(bundle, archive)
	return err == nil
}

func extract(data []byte, dir string) error {
	reader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return err
	}
	for _, entry := range reader.File {
		if !fs.ValidPath(entry.Name) || strings.ContainsAny(entry.Name, "\\:") || !entry.Mode().IsRegular() {
			return fmt.Errorf("invalid client bundle entry %q", entry.Name)
		}
		path := filepath.Join(dir, filepath.FromSlash(entry.Name))
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			return err
		}
		src, err := entry.Open()
		if err != nil {
			return err
		}
		dst, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			src.Close()
			return err
		}
		_, writeErr := io.Copy(dst, src)
		if err := errors.Join(writeErr, dst.Close(), src.Close()); err != nil {
			return err
		}
	}
	return nil
}

func Run(ctx context.Context, home, gameDir string, disconnected <-chan struct{}) error {
	data, err := bundle.ReadFile(archive)
	if err != nil {
		return err
	}
	dir, err := os.MkdirTemp(home, "hailstone-session-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(dir)
	if err := extract(data, dir); err != nil {
		return err
	}
	state := filepath.Join(home, "hailstone")
	server := filepath.Join(state, "servers", "nightcap")
	if err := os.MkdirAll(server, 0700); err != nil {
		return err
	}
	if err := installSpellOverlay(gameDir, server); err != nil {
		return err
	}
	const profile = "[Server]\nname=Nightcap\nhost=127.77.0.1\nport=5998\nui=modern\nremember=0\n"
	if err := os.WriteFile(filepath.Join(server, "server.ini"), []byte(profile), 0600); err != nil {
		return err
	}
	child, cancel := context.WithCancel(ctx)
	defer cancel()
	cmd := exec.CommandContext(child, filepath.Join(dir, "hailstone.exe"), "--game-dir", gameDir, "--server", "nightcap")
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "HAILSTONE_DATA_DIR="+state)
	if err := cmd.Start(); err != nil {
		return err
	}
	done := make(chan error, 1)
	go func() { done <- cmd.Wait() }()
	select {
	case err := <-done:
		if ctx.Err() != nil {
			return ctx.Err()
		}
		return err
	case <-disconnected:
		cancel()
		<-done
		return fmt.Errorf("Nightcap connection closed; reconnect with Play")
	}
}

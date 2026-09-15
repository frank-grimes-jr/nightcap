// Package assets inspects and stages signed releases without activating them.
package assets

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"

	"nightcap/eq-launcher/internal/manifest"
)

type State string

const (
	Current State = "current"
	Changed State = "changed"
	Missing State = "missing"
)

type FileStatus struct {
	Path  string
	State State
}
type Diff struct {
	Files  []FileStatus
	Remove []string
}

// Inspect verifies metadata before accessing disk. A current file is only a
// hash/size match; this is not executable, installed-generation or Play health.
func Inspect(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir string) (Diff, error) {
	m, err := manifest.Verify(raw, sig, trust)
	if err != nil {
		return Diff{}, err
	}
	root, err := os.OpenRoot(clientDir)
	if err != nil {
		return Diff{}, err
	}
	defer root.Close()
	return inspect(ctx, m, root)
}
func inspect(ctx context.Context, m manifest.Manifest, root *os.Root) (Diff, error) {
	d := Diff{Files: make([]FileStatus, 0, len(m.Files)), Remove: []string{}}
	for _, f := range m.Files {
		if err := ctx.Err(); err != nil {
			return Diff{}, err
		}
		file, err := openRegular(root, f.Path)
		state := Missing
		if err == nil {
			info, statErr := file.Stat()
			if statErr != nil {
				file.Close()
				return Diff{}, statErr
			}
			state = Changed
			if info.Size() == f.Size {
				err = verifyCopy(ctx, io.Discard, file, f)
				if err == nil {
					state = Current
				} else if !errors.Is(err, errContent) {
					file.Close()
					return Diff{}, err
				}
			}
			if closeErr := file.Close(); closeErr != nil {
				return Diff{}, closeErr
			}
		} else if !errors.Is(err, os.ErrNotExist) {
			return Diff{}, fmt.Errorf("inspect %s: %w", f.Path, err)
		}
		d.Files = append(d.Files, FileStatus{Path: f.Path, State: state})
	}
	for _, name := range m.Tombstones {
		if err := ctx.Err(); err != nil {
			return Diff{}, err
		}
		file, err := openRegular(root, name)
		if err == nil {
			if err = file.Close(); err != nil {
				return Diff{}, err
			}
			d.Remove = append(d.Remove, name)
		} else if !errors.Is(err, os.ErrNotExist) {
			return Diff{}, fmt.Errorf("inspect retired %s: %w", name, err)
		}
	}
	return d, nil
}

// Reject existing symlinks/junctions and nonregular assets. Root additionally
// confines all subsequent opens against path replacement races on Windows.
// Reads within the root are hash checked; this does not authorize installation.
func openRegular(root *os.Root, name string) (*os.File, error) {
	parts := strings.Split(name, "/")
	for i := range parts {
		info, err := root.Lstat(strings.Join(parts[:i+1], "/"))
		if err != nil {
			return nil, err
		}
		if i < len(parts)-1 {
			if !info.IsDir() || info.Mode()&(os.ModeSymlink|os.ModeIrregular) != 0 {
				return nil, fmt.Errorf("unsafe parent for %s", name)
			}
		} else if !info.Mode().IsRegular() {
			return nil, fmt.Errorf("nonregular asset %s", name)
		}
	}
	f, err := root.Open(name)
	if err != nil {
		return nil, err
	}
	info, err := f.Stat()
	if err != nil {
		f.Close()
		return nil, err
	}
	if !info.Mode().IsRegular() {
		f.Close()
		return nil, fmt.Errorf("nonregular opened asset %s", name)
	}
	return f, nil
}

var errContent = errors.New("asset size or SHA256 mismatch")

type contextReader struct {
	ctx context.Context
	r   io.Reader
}

func (r contextReader) Read(b []byte) (int, error) {
	if err := r.ctx.Err(); err != nil {
		return 0, err
	}
	return r.r.Read(b)
}
func verifyCopy(ctx context.Context, dst io.Writer, src io.Reader, f manifest.File) error {
	hash := sha256.New()
	n, err := io.Copy(io.MultiWriter(dst, hash), io.LimitReader(contextReader{ctx, src}, f.Size+1))
	if err != nil {
		return err
	}
	if n != f.Size || hex.EncodeToString(hash.Sum(nil)) != f.SHA256 {
		return fmt.Errorf("%s: %w", f.Path, errContent)
	}
	return ctx.Err()
}

// Package launchlock holds read-only installation handles for a launch session.
// A lock protects bytes and path identity; it does not verify a release or permit Play.
package launchlock

import (
	"errors"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// File exposes only reads and identity. Its lifetime belongs to the Set.
type File interface {
	io.Reader
	io.ReaderAt
	io.Seeker
	Stat() (os.FileInfo, error)
	Fd() uintptr
}

// Set is single-owner and not safe for concurrent Open/Close. Keep it alive until
// the owned game exits, or transfer equivalent locks before releasing it.
type Set struct {
	directory string
	files     map[string]*os.File
	dirs      map[string]*os.File
	handles   []*os.File
	closed    bool
}

func (s *Set) Directory() string { return s.directory }
func (s *Set) Close() error {
	if s == nil || s.closed {
		return nil
	}
	s.closed = true
	var err error
	for i := len(s.handles) - 1; i >= 0; i-- {
		err = errors.Join(err, s.handles[i].Close())
	}
	s.handles = nil
	return err
}

func validName(name string) bool {
	if !fs.ValidPath(name) || name == "." || !filepath.IsLocal(name) || strings.ContainsAny(name, `\:<>"|?*`) {
		return false
	}
	for _, part := range strings.Split(name, "/") {
		if strings.HasSuffix(part, ".") || strings.HasSuffix(part, " ") {
			return false
		}
	}
	return true
}

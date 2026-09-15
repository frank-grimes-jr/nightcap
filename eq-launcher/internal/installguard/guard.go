// Package installguard excludes game execution and concurrent client updates.
package installguard

import (
	"errors"
	"io"
	"os"
)

// Executable provides read-only access through the exclusive handle.
type Executable interface {
	io.Reader
	io.Seeker
	Stat() (os.FileInfo, error)
}
type Guard struct {
	file *os.File
	root *os.Root
}

func (g *Guard) Executable() Executable { return g.file }
func (g *Guard) Root() *os.Root         { return g.root }
func (g *Guard) Close() error           { return errors.Join(g.file.Close(), g.root.Close()) }

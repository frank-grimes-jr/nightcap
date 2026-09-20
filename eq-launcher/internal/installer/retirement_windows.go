//go:build windows

package installer

import (
	"errors"
	"fmt"
	"io"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"syscall"
	"unsafe"
)

// Keep write/delete sharing denied from preimage verification through deletion.
// The opened file identity is checked against the confined root before use.
type retirementLock struct{ file *os.File }

func lockRetirement(root *os.Root, name, expected string) (*retirementLock, error) {
	before, err := root.Lstat(name)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !before.Mode().IsRegular() {
		return nil, fmt.Errorf("nonregular retirement: %s", name)
	}
	full, err := filepath.Abs(filepath.Join(root.Name(), filepath.FromSlash(name)))
	if err != nil {
		return nil, err
	}
	wide, err := syscall.UTF16PtrFromString(full)
	if err != nil {
		return nil, err
	}
	h, err := syscall.CreateFile(wide, syscall.GENERIC_READ|0x00010000, syscall.FILE_SHARE_READ, nil, syscall.OPEN_EXISTING, syscall.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, err
	}
	f := os.NewFile(uintptr(h), full)
	after, err := f.Stat()
	if err != nil || !after.Mode().IsRegular() || !os.SameFile(before, after) {
		f.Close()
		return nil, fmt.Errorf("retirement path changed: %s", name)
	}
	if after.Size() > manifest.MaxFileBytes {
		f.Close()
		return nil, fmt.Errorf("oversized retirement")
	}
	sha, err := copyHash(io.Discard, f, after.Size())
	if err != nil || sha != expected {
		f.Close()
		return nil, fmt.Errorf("retired file %s differs from supported original", name)
	}
	return &retirementLock{f}, nil
}
func (l *retirementLock) close() {
	if l != nil && l.file != nil {
		l.file.Close()
		l.file = nil
	}
}
func (l *retirementLock) remove() error {
	var disposition uint32 = 1
	proc := syscall.NewLazyDLL("kernel32.dll").NewProc("SetFileInformationByHandle")
	ok, _, err := proc.Call(l.file.Fd(), 4, uintptr(unsafe.Pointer(&disposition)), unsafe.Sizeof(disposition))
	if ok == 0 {
		return err
	}
	err = l.file.Close()
	l.file = nil
	return err
}

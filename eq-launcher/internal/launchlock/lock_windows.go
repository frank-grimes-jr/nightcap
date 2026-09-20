package launchlock

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
)

// Acquire pins every ancestor and opens eqgame.exe for read, sharing only read.
// Windows may execute the image, but the updater's writable guard cannot open it.
// Only ordinary absolute drive paths are supported; junctions and UNC/device
// namespaces fail closed. Drive remapping by the same user is outside this lease.
func Acquire(directory string) (*Set, error) {
	return AcquireImage(directory, "eqgame.exe")
}

// AcquireImage pins a fixed caller-selected executable and its ancestors.
func AcquireImage(directory, image string) (*Set, error) {
	dir, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	volume := filepath.VolumeName(dir)
	if len(volume) != 2 || volume[1] != ':' {
		return nil, fmt.Errorf("launch requires a local drive path")
	}
	s := &Set{directory: dir, files: make(map[string]*os.File), dirs: make(map[string]*os.File)}
	keep := false
	defer func() {
		if !keep {
			s.Close()
		}
	}()
	current := volume + `\`
	if err = s.pinDirectory(current); err != nil {
		return nil, err
	}
	for _, part := range strings.Split(strings.TrimPrefix(dir, current), `\`) {
		if part == "" {
			continue
		}
		if !validName(part) {
			return nil, fmt.Errorf("unsafe launch directory")
		}
		current = filepath.Join(current, part)
		if err = s.pinDirectory(current); err != nil {
			return nil, err
		}
	}
	if _, err = s.Open(image); err != nil {
		return nil, err
	}
	keep = true
	return s, nil
}

// openPinned inspects the object reached by the handle, never follows a leaf
// reparse point, and retains sharing restrictions for the entire Set lifetime.
func (s *Set) openPinned(name string, directory bool) (*os.File, error) {
	wide, err := syscall.UTF16PtrFromString(name)
	if err != nil {
		return nil, err
	}
	access, flags := uint32(syscall.GENERIC_READ), uint32(syscall.FILE_FLAG_OPEN_REPARSE_POINT)
	if directory {
		access = 0
		flags |= syscall.FILE_FLAG_BACKUP_SEMANTICS
	}
	h, err := syscall.CreateFile(wide, access, syscall.FILE_SHARE_READ, nil, syscall.OPEN_EXISTING, flags, 0)
	if err != nil {
		return nil, fmt.Errorf("cannot hold launch path %s: %w", name, err)
	}
	f := os.NewFile(uintptr(h), name)
	var info syscall.ByHandleFileInformation
	err = syscall.GetFileInformationByHandle(h, &info)
	if err == nil && (info.FileAttributes&syscall.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&syscall.FILE_ATTRIBUTE_DIRECTORY != 0) != directory) {
		err = fmt.Errorf("nonregular or reparse launch path: %s", name)
	}
	if err != nil {
		f.Close()
		return nil, err
	}
	s.handles = append(s.handles, f)
	return f, nil
}

func (s *Set) pinDirectory(name string) error {
	if _, ok := s.dirs[name]; ok {
		return nil
	}
	f, err := s.openPinned(name, true)
	if err == nil {
		s.dirs[name] = f
	}
	return err
}
func (s *Set) parent(name string) (string, error) {
	if s.closed {
		return "", os.ErrClosed
	}
	if !validName(name) {
		return "", fmt.Errorf("unsafe relative launch path: %q", name)
	}
	parts := strings.Split(name, "/")
	current := s.directory
	for _, part := range parts[:len(parts)-1] {
		current = filepath.Join(current, part)
		if err := s.pinDirectory(current); err != nil {
			return "", err
		}
	}
	return filepath.Join(current, parts[len(parts)-1]), nil
}
func (s *Set) Open(name string) (File, error) {
	if s.closed {
		return nil, os.ErrClosed
	}
	if f, ok := s.files[name]; ok {
		return f, nil
	}
	full, err := s.parent(name)
	if err != nil {
		return nil, err
	}
	f, err := s.openPinned(full, false)
	if err == nil {
		s.files[name] = f
	}
	return f, err
}

// Absent checks a tombstone or pending journal without following links. Missing
// files cannot be locked: the executable lock excludes cooperating installers,
// not arbitrary same-user creation of new files during a running session.
func (s *Set) Absent(name string) error {
	full, err := s.parent(name)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	_, err = os.Lstat(full)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	return fmt.Errorf("launch path must be absent: %s", name)
}

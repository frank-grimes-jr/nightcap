package installguard

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

// Acquire holds a non-shared writable handle to this client's executable.
// Windows refuses that handle while the image is running, including through an
// alias, and refuses launches while it is held. Other installations are unrelated.
// No executable writes are performed.
func Acquire(clientDir string) (*Guard, error) {
	root, err := os.OpenRoot(clientDir)
	if err != nil {
		return nil, err
	}
	keep := false
	defer func() {
		if !keep {
			root.Close()
		}
	}()
	before, err := root.Lstat("eqgame.exe")
	if err != nil {
		return nil, err
	}
	if !before.Mode().IsRegular() {
		return nil, fmt.Errorf("client executable is not regular")
	}
	name, err := filepath.Abs(filepath.Join(clientDir, "eqgame.exe"))
	if err != nil {
		return nil, err
	}
	wide, err := syscall.UTF16PtrFromString(name)
	if err != nil {
		return nil, err
	}
	handle, err := syscall.CreateFile(wide, syscall.GENERIC_READ|syscall.GENERIC_WRITE, 0, nil, syscall.OPEN_EXISTING, syscall.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, fmt.Errorf("cannot exclusively lock executable; close the game and check write access: %w", err)
	}
	file := os.NewFile(uintptr(handle), name)
	after, err := file.Stat()
	if err != nil {
		file.Close()
		return nil, err
	}
	if !after.Mode().IsRegular() || !os.SameFile(before, after) {
		file.Close()
		return nil, fmt.Errorf("executable changed while acquiring update guard")
	}
	keep = true
	return &Guard{file: file, root: root}, nil
}

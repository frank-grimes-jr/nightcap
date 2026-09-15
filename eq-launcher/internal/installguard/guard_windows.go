package installguard

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"unsafe"
)

// Acquire refuses any running eqgame.exe, then holds a non-shared writable
// executable handle for the transaction. No executable writes are performed.
// The handle also prevents launches that race the process snapshot and excludes
// another updater, including one reaching this client through a directory alias.
func Acquire(clientDir string) (*Guard, error) { return acquire(clientDir, "eqgame.exe") }
func acquire(clientDir, processName string) (*Guard, error) {
	running, err := Running(processName)
	if err != nil {
		return nil, err
	}
	if running {
		return nil, fmt.Errorf("close %s before updating", processName)
	}
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

// Running fails closed when a process snapshot cannot be read completely.
func Running(imageName string) (bool, error) {
	handle, err := syscall.CreateToolhelp32Snapshot(syscall.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return false, err
	}
	defer syscall.CloseHandle(handle)
	entry := syscall.ProcessEntry32{Size: uint32(unsafe.Sizeof(syscall.ProcessEntry32{}))}
	err = syscall.Process32First(handle, &entry)
	for err == nil {
		if strings.EqualFold(syscall.UTF16ToString(entry.ExeFile[:]), imageName) {
			return true, nil
		}
		err = syscall.Process32Next(handle, &entry)
	}
	if errors.Is(err, syscall.ERROR_NO_MORE_FILES) {
		return false, nil
	}
	return false, fmt.Errorf("cannot inspect running processes: %w", err)
}

package selfupdate

import (
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
)

// Lock serializes starter instances for the entire desktop lifetime.
func Lock(cache string) (*os.File, error) {
	if err := os.MkdirAll(cache, 0700); err != nil {
		return nil, err
	}
	name := filepath.Join(cache, "starter.lock")
	wide, err := windows.UTF16PtrFromString(name)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_ALWAYS, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, fmt.Errorf("Nightcap is already open, or its update folder is unavailable: %w", err)
	}
	f := os.NewFile(uintptr(h), name)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 {
		f.Close()
		return nil, fmt.Errorf("invalid starter lock")
	}
	return f, nil
}

// StartDesktop uses the explicit verified path, no shell or downloaded arguments.
// Caller retains Lease until the returned process exits.
func StartDesktop(l *Lease) (*exec.Cmd, error) {
	cmd := exec.Command(l.Path)
	cmd.Dir = filepath.Dir(l.Path)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	return cmd, nil
}

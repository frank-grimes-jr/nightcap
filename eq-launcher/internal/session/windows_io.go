//go:build windows

package session

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"unsafe"

	"golang.org/x/sys/windows"
	"nightcap/eq-launcher/internal/runtimehealth"
)

var peekPipe = windows.NewLazySystemDLL("kernel32.dll").NewProc("PeekNamedPipe")

func availableBytes(file *os.File) (uint32, error) {
	var available uint32
	result, _, err := peekPipe.Call(file.Fd(), 0, 0, 0, uintptr(unsafe.Pointer(&available)), 0)
	if result == 0 {
		if errors.Is(err, windows.ERROR_BROKEN_PIPE) {
			return 0, io.EOF
		}
		return 0, err
	}
	return available, nil
}
func privatePipe(capacity uint32) (*os.File, *os.File, error) {
	var read, write windows.Handle
	if err := windows.CreatePipe(&read, &write, nil, capacity); err != nil {
		return nil, nil, err
	}
	var flags, outSize, inSize, instances uint32
	err := windows.GetNamedPipeInfo(read, &flags, &outSize, &inSize, &instances)
	if err == nil && inSize < capacity {
		err = fmt.Errorf("pipe capacity %d below required %d", inSize, capacity)
	}
	if err != nil {
		windows.CloseHandle(read)
		windows.CloseHandle(write)
		return nil, nil, err
	}
	return os.NewFile(uintptr(read), "bootstrap-read"), os.NewFile(uintptr(write), "bootstrap-write"), nil
}
func duplicateInherited(handle windows.Handle, access, options uint32) (windows.Handle, error) {
	var duplicate windows.Handle
	err := windows.DuplicateHandle(windows.CurrentProcess(), handle, windows.CurrentProcess(), &duplicate, access, true, options)
	if err == nil && uint64(duplicate) > 0xffffffff {
		windows.CloseHandle(duplicate)
		return 0, fmt.Errorf("inherited handle exceeds x86 range")
	}
	return duplicate, err
}
func processCreated(process windows.Handle) (uint64, error) {
	var created, exited, kernel, user windows.Filetime
	if err := windows.GetProcessTimes(process, &created, &exited, &kernel, &user); err != nil {
		return 0, err
	}
	return uint64(created.HighDateTime)<<32 | uint64(created.LowDateTime), nil
}
func openChild(identity Identity) (windows.Handle, error) {
	process, err := windows.OpenProcess(windows.SYNCHRONIZE|windows.PROCESS_QUERY_LIMITED_INFORMATION, false, identity.PID)
	if err != nil {
		return 0, err
	}
	created, err := processCreated(process)
	if err == nil && created != identity.Created {
		err = fmt.Errorf("helper process creation mismatch")
	}
	if err == nil {
		var state uint32
		state, err = windows.WaitForSingleObject(process, 0)
		if err == nil && state != uint32(windows.WAIT_TIMEOUT) {
			err = fmt.Errorf("client exited before health approval")
		}
	}
	if err != nil {
		windows.CloseHandle(process)
		return 0, err
	}
	return process, nil
}
func childExit(process windows.Handle, expected uint32) error {
	state, err := windows.WaitForSingleObject(process, 0)
	if err != nil {
		return err
	}
	if state != windows.WAIT_OBJECT_0 {
		return fmt.Errorf("helper reported exit before client termination")
	}
	var code uint32
	if err := windows.GetExitCodeProcess(process, &code); err != nil {
		return err
	}
	if code != expected {
		return fmt.Errorf("helper exit code differs from process handle")
	}
	return nil
}
func readHealth(directory string, pid uint32) (data []byte, err error) {
	name := filepath.Join(directory, fmt.Sprintf("nightcap_health_%d.json", pid))
	wide, err := windows.UTF16PtrFromString(name)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, err
	}
	file := os.NewFile(uintptr(h), name)
	defer func() { err = errors.Join(err, file.Close()) }()
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil {
		return nil, err
	}
	if info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 || info.FileSizeHigh != 0 || info.FileSizeLow > runtimehealth.MaxBytes {
		return nil, fmt.Errorf("unsafe or oversized runtime health")
	}
	data, err = io.ReadAll(io.LimitReader(file, runtimehealth.MaxBytes+1))
	if err == nil && len(data) > runtimehealth.MaxBytes {
		err = fmt.Errorf("oversized runtime health")
	}
	return data, err
}

type jobAccounting struct {
	TotalUser, TotalKernel, PeriodUser, PeriodKernel                 int64
	PageFaults, TotalProcesses, ActiveProcesses, TerminatedProcesses uint32
}

func createJob() (windows.Handle, error) {
	job, err := windows.CreateJobObject(nil, nil)
	if err != nil {
		return 0, err
	}
	var limits windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
	_, err = windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits)))
	if err != nil {
		windows.CloseHandle(job)
		return 0, err
	}
	return job, nil
}
func jobEmpty(job windows.Handle) (bool, error) {
	var info jobAccounting
	err := windows.QueryInformationJobObject(job, windows.JobObjectBasicAccountingInformation, uintptr(unsafe.Pointer(&info)), uint32(unsafe.Sizeof(info)), nil)
	return info.ActiveProcesses == 0, err
}

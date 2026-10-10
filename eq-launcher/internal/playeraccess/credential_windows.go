package playeraccess

import (
	"runtime"
	"unsafe"

	"golang.org/x/sys/windows"
)

func protect(raw []byte) ([]byte, error)   { return crypt(raw, true) }
func unprotect(raw []byte) ([]byte, error) { return crypt(raw, false) }

func crypt(raw []byte, encrypt bool) ([]byte, error) {
	if len(raw) == 0 {
		return nil, ErrSavedCode
	}
	purpose := []byte("NightcapLauncher/player-access/v1")
	in := windows.DataBlob{Size: uint32(len(raw)), Data: &raw[0]}
	entropy := windows.DataBlob{Size: uint32(len(purpose)), Data: &purpose[0]}
	var out windows.DataBlob
	var err error
	// No LOCAL_MACHINE flag: another Windows user cannot decrypt this credential.
	if encrypt {
		err = windows.CryptProtectData(&in, nil, &entropy, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out)
	} else {
		err = windows.CryptUnprotectData(&in, nil, &entropy, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out)
	}
	runtime.KeepAlive(raw)
	runtime.KeepAlive(purpose)
	if err != nil {
		return nil, ErrSavedCode
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	return append([]byte(nil), unsafe.Slice(out.Data, out.Size)...), nil
}

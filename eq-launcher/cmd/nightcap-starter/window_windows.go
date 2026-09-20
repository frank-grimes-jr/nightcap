package main

import (
	"golang.org/x/sys/windows"
	"runtime"
	"time"
	"unsafe"
)

var user32 = windows.NewLazySystemDLL("user32.dll")

var createWindow = user32.NewProc("CreateWindowExW")

var setText = user32.NewProc("SetWindowTextW")

var destroyWindow = user32.NewProc("DestroyWindow")

var showWindow = user32.NewProc("ShowWindow")

var isWindow = user32.NewProc("IsWindow")

var peekMessage = user32.NewProc("PeekMessageW")

var translateMessage = user32.NewProc("TranslateMessage")

var dispatchMessage = user32.NewProc("DispatchMessageW")

func wide(s string) *uint16 { p, _ := windows.UTF16PtrFromString(s); return p }

func showError(s string) {
	user32.NewProc("MessageBoxW").Call(0, uintptr(unsafe.Pointer(wide(s))), uintptr(unsafe.Pointer(wide("Nightcap"))), 0x10)
}

type message struct {
	Window  uintptr
	ID      uint32
	WParam  uintptr
	LParam  uintptr
	Time    uint32
	X, Y    int32
	Private uint32
}

func progressWindow(cancel func(), work func(func(string), func()) error) error {

	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	hwnd, _, err := createWindow.Call(0, uintptr(unsafe.Pointer(wide("STATIC"))), uintptr(unsafe.Pointer(wide("Nightcap — checking for updates"))), 0x10ca0000, 0x80000000, 0x80000000, 480, 130, 0, 0, 0, 0)

	if hwnd == 0 {
		return err
	}
	defer destroyWindow.Call(hwnd)

	label, _, _ := createWindow.Call(0, uintptr(unsafe.Pointer(wide("STATIC"))), uintptr(unsafe.Pointer(wide("Checking for launcher updates…"))), 0x50000000, 22, 28, 430, 50, hwnd, 0, 0, 0)

	updates := make(chan string, 8)
	hide := make(chan struct{}, 1)
	done := make(chan error, 1)

	go func() {
		done <- work(func(s string) {
			select {
			case updates <- s:
			default:
			}
		}, func() { hide <- struct{}{} })
	}()

	tick := time.NewTicker(20 * time.Millisecond)
	defer tick.Stop()
	hidden := false

	for {
		select {

		case err := <-done:
			return err

		case s := <-updates:
			setText.Call(label, uintptr(unsafe.Pointer(wide(s))))

		case <-hide:
			showWindow.Call(hwnd, 0)
			hidden = true

		case <-tick.C:

			var m message
			for {
				ok, _, _ := peekMessage.Call(uintptr(unsafe.Pointer(&m)), 0, 0, 0, 1)
				if ok == 0 {
					break
				}
				translateMessage.Call(uintptr(unsafe.Pointer(&m)))
				dispatchMessage.Call(uintptr(unsafe.Pointer(&m)))
			}

			if !hidden {
				exists, _, _ := isWindow.Call(hwnd)
				if exists == 0 {
					cancel()
					hidden = true
				}
			}

		}
	}

}

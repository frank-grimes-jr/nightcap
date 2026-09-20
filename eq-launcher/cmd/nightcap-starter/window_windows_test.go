package main

import (
	"context"
	"errors"
	"testing"
	"time"
	"unsafe"
)

func TestProgressWindowCloseCancelsDownload(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	err := progressWindow(cancel, func(status func(string), hide func()) error {
		status("Testing update cancellation")
		hwnd, _, _ := user32.NewProc("FindWindowW").Call(uintptr(unsafe.Pointer(wide("STATIC"))), uintptr(unsafe.Pointer(wide("Nightcap — checking for updates"))))
		if hwnd == 0 {
			return errors.New("progress window not created")
		}
		user32.NewProc("PostMessageW").Call(hwnd, 0x10, 0, 0)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(2 * time.Second):
			return errors.New("close failed to cancel")
		}
	})
	if !errors.Is(err, context.Canceled) {
		t.Fatal(err)
	}
}
func TestProgressWindowHidesWhileDesktopLives(t *testing.T) {
	err := progressWindow(func() { t.Error("unexpected cancellation") }, func(status func(string), hide func()) error {
		status("Opening fixture")
		hwnd, _, _ := user32.NewProc("FindWindowW").Call(uintptr(unsafe.Pointer(wide("STATIC"))), uintptr(unsafe.Pointer(wide("Nightcap — checking for updates"))))
		hide()
		deadline := time.Now().Add(2 * time.Second)
		for time.Now().Before(deadline) {
			visible, _, _ := user32.NewProc("IsWindowVisible").Call(hwnd)
			if visible == 0 {
				return nil
			}
			time.Sleep(time.Millisecond)
		}
		return errors.New("progress remains visible")
	})
	if err != nil {
		t.Fatal(err)
	}
}

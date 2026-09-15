//go:build desktop || bindings

package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/wailsapp/wails/v2/pkg/runtime"
	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/launcher"
)

type App struct {
	ctx          context.Context
	controller   *launcher.Controller
	startupError error
}

func NewApp() *App { return &App{} }
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	home, err := os.UserConfigDir()
	if err == nil {
		a.controller, err = launcher.New(filepath.Join(home, "NightcapLauncher"), launcher.DefaultPolicy())
	}
	a.startupError = err
}
func (a *App) available() error {
	if a.startupError != nil {
		return fmt.Errorf("cannot load launcher settings: %w", a.startupError)
	}
	if a.controller == nil {
		return fmt.Errorf("launcher is starting")
	}
	return nil
}
func (a *App) GetStatus() launcher.Status {
	if err := a.available(); err != nil {
		return launcher.Status{Phase: "error", Message: err.Error(), Files: []assets.FileStatus{}, Remove: []string{}, Events: []launcher.Event{}}
	}
	return a.controller.Snapshot()
}
func (a *App) ChooseClient() error {
	if err := a.available(); err != nil {
		return err
	}
	if a.controller.Snapshot().Busy {
		return launcher.ErrBusy
	}
	folder, err := runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{Title: "Choose your EverQuest RoF2 folder"})
	if err != nil {
		return err
	}
	if folder == "" {
		return nil
	}
	return a.controller.SelectClient(a.ctx, folder)
}
func (a *App) CheckForUpdates() error {
	if err := a.available(); err != nil {
		return err
	}
	return a.controller.Check(a.ctx)
}
func (a *App) Update() error {
	if err := a.available(); err != nil {
		return err
	}
	return a.controller.Update(a.ctx)
}
func (a *App) Recover() error {
	if err := a.available(); err != nil {
		return err
	}
	return a.controller.Recover(a.ctx)
}
func (a *App) Play() error {
	if err := a.available(); err != nil {
		return err
	}
	return a.controller.Play(a.ctx)
}
func (a *App) Cancel() {
	if a.controller != nil {
		a.controller.Cancel()
	}
}
func (a *App) OpenGuide() {
	runtime.BrowserOpenURL(a.ctx, "https://github.com/frank-grimes-jr/nightcap/blob/main/README.md")
}
func (a *App) beforeClose(context.Context) bool {
	if a.controller != nil && a.controller.Snapshot().Busy {
		a.controller.Cancel()
		return true
	}
	return false
}
func (a *App) shutdown(context.Context) {
	if a.controller != nil {
		a.controller.Cancel()
	}
}

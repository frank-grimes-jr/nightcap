//go:build desktop || bindings

package main

import (
	"embed"
	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	"github.com/wailsapp/wails/v2/pkg/options/windows"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

//go:embed all:frontend/dist
var webAssets embed.FS

func main() {
	app := NewApp()
	err := wails.Run(&options.App{
		Title: "Nightcap Launcher", Width: 1120, Height: 820, MinWidth: 780, MinHeight: 620,
		BackgroundColour: &options.RGBA{R: 17, G: 25, B: 23, A: 255},
		AssetServer:      &assetserver.Options{Assets: webAssets},
		OnStartup:        app.startup, OnBeforeClose: app.beforeClose, OnShutdown: app.shutdown,
		Windows: &windows.Options{Theme: windows.Dark},
		SingleInstanceLock: &options.SingleInstanceLock{UniqueId: "48d3adf9-55e2-4e85-a5a7-61f3bbc05dde", OnSecondInstanceLaunch: func(options.SecondInstanceData) {
			if app.ctx != nil {
				runtime.WindowShow(app.ctx)
				runtime.WindowUnminimise(app.ctx)
			}
		}},
		Bind: []interface{}{app},
	})
	if err != nil {
		println("Nightcap Launcher:", err.Error())
	}
}

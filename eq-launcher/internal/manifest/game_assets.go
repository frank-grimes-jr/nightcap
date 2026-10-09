package manifest

import (
	"path"
	"strings"
)

// CoreAssets are required even when the signed release supplies its inventory.
var CoreAssets = [...]string{"dinput8.dll", "nightcap-bootstrap.exe", "nightcap-patches.cfg", "nightcap-patch-sites.json"}

// GameAssetPath is an installation boundary, not deletion authority. Settings,
// stock executables, other DLLs and foreign UI folders are never in this scope.
func GameAssetPath(name string) bool {
	if ValidatePath(name) != nil {
		return false
	}
	for _, core := range CoreAssets {
		if name == core {
			return true
		}
	}
	if loadingScreenPath(name) {
		return true
	}
	if !strings.Contains(name, "/") {
		switch name {
		case "spells_us.txt", "dbstr_us.txt", "ecommons_assets.txt":
			return true
		}
		return path.Ext(name) == ".s3d" || path.Ext(name) == ".eqg" || strings.HasSuffix(name, "_chr.txt")
	}
	if path.Dir(name) == "maps" {
		return path.Ext(name) == ".txt"
	}
	if strings.HasPrefix(name, "uifiles/nightcap/") {
		switch path.Ext(name) {
		case ".xml", ".tga", ".dds", ".bmp":
			return true
		}
	}
	return false
}

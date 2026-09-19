package launcher

import (
	"fmt"
	"path/filepath"
)

// StateHome keeps offline QA settings and staging beside its executable. Errors
// never fall back to another launcher's configuration directory.
func StateHome(p Policy, executable, userConfig func() (string, error)) (string, error) {
	if p.Bundle != nil {
		path, err := executable()
		if err != nil {
			return "", err
		}
		if !filepath.IsAbs(path) {
			return "", fmt.Errorf("QA executable path must be absolute")
		}
		return filepath.Join(filepath.Dir(path), "launcher-state"), nil
	}
	home, err := userConfig()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, "NightcapLauncher"), nil
}

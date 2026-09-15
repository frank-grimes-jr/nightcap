package launcher

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

type settings struct {
	ClientDir string `json:"client_dir"`
}

func loadSettings(home string) (settings, error) {
	root, err := os.OpenRoot(home)
	if err != nil {
		return settings{}, err
	}
	defer root.Close()
	f, err := root.Open("settings.json")
	if errors.Is(err, os.ErrNotExist) {
		return settings{}, nil
	}
	if err != nil {
		return settings{}, err
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, 8193))
	if err != nil {
		return settings{}, err
	}
	if len(data) > 8192 {
		return settings{}, fmt.Errorf("launcher settings too large")
	}
	var s settings
	if err = json.Unmarshal(data, &s); err != nil {
		return s, err
	}
	if s.ClientDir != "" && !filepath.IsAbs(s.ClientDir) {
		return s, fmt.Errorf("client path in settings must be absolute")
	}
	return s, nil
}
func saveSettings(home, folder string) error {
	root, err := os.OpenRoot(home)
	if err != nil {
		return err
	}
	defer root.Close()
	data, err := json.Marshal(settings{ClientDir: folder})
	if err != nil {
		return err
	}
	// The settings directory is launcher-owned local state, not an asset path.
	if info, e := root.Lstat("settings.next"); e == nil {
		if !info.Mode().IsRegular() {
			return fmt.Errorf("unsafe settings temporary")
		}
		if err = root.Remove("settings.next"); err != nil {
			return err
		}
	} else if !errors.Is(e, os.ErrNotExist) {
		return e
	}
	f, err := root.OpenFile("settings.next", os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	_, err = f.Write(data)
	if err == nil {
		err = f.Sync()
	}
	err = errors.Join(err, f.Close())
	if err != nil {
		return err
	}
	return root.Rename("settings.next", "settings.json")
}

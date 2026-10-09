package manifest

import "fmt"

// LoadingScreenPaths is the exact gallery shipped with the pinned RoF2 client.
// Keep this exception separate from general UI assets: it grants no XML,
// executable, settings, arbitrary Resources file, or deletion authority.
func LoadingScreenPaths() []string {
	paths := []string{"resources/loadscreen.jpg"}
	for slot := 1; slot <= 55; slot++ {
		paths = append(paths, fmt.Sprintf("uifiles/default/loadscreens/loadscreen%02d.jpg", slot))
	}
	return paths
}

func loadingScreenPath(name string) bool {
	for _, allowed := range LoadingScreenPaths() {
		if name == allowed {
			return true
		}
	}
	return false
}

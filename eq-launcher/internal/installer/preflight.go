package installer

import (
	"fmt"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
	"os"
)

// patchAssets reads only explicit required entries, binding the exact parsed
// bytes to the verified manifest. Paths and limits are compiled policy.
func patchAssets(stage *os.Root, m manifest.Manifest) ([]byte, []byte, error) {
	read := func(name string, limit int64) ([]byte, error) {
		var entry *manifest.File
		for i := range m.Files {
			if m.Files[i].Path == name {
				entry = &m.Files[i]
				break
			}
		}
		if entry == nil || !entry.Required || entry.Size > limit {
			return nil, fmt.Errorf("missing/invalid required preflight asset: %s", name)
		}
		data, err := readBounded(stage, "files/"+name, limit)
		if err != nil {
			return nil, err
		}
		if int64(len(data)) != entry.Size || manifest.Digest(data) != entry.SHA256 {
			return nil, fmt.Errorf("preflight asset differs from signed manifest: %s", name)
		}
		return data, nil
	}
	config, err := read(preflight.ConfigPath, preflight.MaxConfigBytes)
	if err != nil {
		return nil, nil, err
	}
	metadata, err := read(preflight.CatalogPath, preflight.MaxCatalogBytes)
	if err != nil {
		return nil, nil, err
	}
	return config, metadata, nil
}

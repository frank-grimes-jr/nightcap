package main

import (
	"encoding/json"
	"fmt"
	"path/filepath"

	"nightcap/eq-launcher/internal/manifest"
)

var gameplayNames = []string{
	"spells_us.txt", "uifiles/nightcap/equi_inventory.xml", "uifiles/nightcap/equi_aawindow.xml",
	"poknowledge_chr.txt", "mur.eqg", "scu.eqg", "frd.eqg", "ddv.eqg", "srn.eqg",
}

type gameplayFile struct {
	Size   int64  `json:"size"`
	SHA256 string `json:"sha256"`
}

type gameplayAudit struct {
	Schema             int                     `json:"schema"`
	Status             string                  `json:"status"`
	SourceSpellsSHA256 string                  `json:"source_spells_sha256"`
	Files              map[string]gameplayFile `json:"files"`
}

// Bind a complete, immutable asset generation to the selected client's spells.
// The manifest subsequently signs the exact bytes returned here.
func loadGameplayAssets(root, clientExe string) (map[string][]byte, error) {
	if root == "" {
		return nil, fmt.Errorf("generated gameplay assets are required")
	}
	raw, err := readBounded(filepath.Join(root, "audit.json"), 1024*1024)
	if err != nil {
		return nil, err
	}
	var audit gameplayAudit
	if err = json.Unmarshal(raw, &audit); err != nil {
		return nil, err
	}
	if audit.Schema != 1 || audit.Status != "generated_not_installed" || len(audit.Files) != len(gameplayNames) {
		return nil, fmt.Errorf("unsupported or incomplete gameplay generation")
	}
	source, err := readBounded(filepath.Join(filepath.Dir(clientExe), "spells_us.txt"), manifest.MaxFileBytes)
	if err != nil {
		return nil, err
	}
	if manifest.Digest(source) != audit.SourceSpellsSHA256 {
		return nil, fmt.Errorf("gameplay generation belongs to different source spells")
	}
	files := make(map[string][]byte, len(gameplayNames))
	for _, name := range gameplayNames {
		entry, exists := audit.Files[name]
		if !exists {
			return nil, fmt.Errorf("missing gameplay asset %s", name)
		}
		data, err := readBounded(filepath.Join(root, filepath.FromSlash(name)), manifest.MaxFileBytes)
		if err != nil {
			return nil, err
		}
		if int64(len(data)) != entry.Size || manifest.Digest(data) != entry.SHA256 {
			return nil, fmt.Errorf("gameplay asset changed: %s", name)
		}
		files[name] = data
	}
	return files, nil
}

package main

import (
	"bytes"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"io"
	"path/filepath"
	"strings"

	"nightcap/eq-launcher/internal/manifest"
)

var gameplayNames = append(append([]string{
	"spells_us.txt", "uifiles/nightcap/equi_inventory.xml", "uifiles/nightcap/equi_aawindow.xml",
	"uifiles/nightcap/equi_petinfowindow.xml",
	"uifiles/nightcap/equi_merchantwnd.xml",
	"uifiles/nightcap/equi_tradeskillwnd.xml",
	"ecommons_chr.txt", "ecommons_assets.txt", "poknowledge_obj.s3d", "nektulos.s3d", "nektulos_obj.s3d", "dbstr_us.txt", "maps/ecommons_3.txt",
	"lavastorm.s3d", "lavastorm_obj.s3d",
	"global_chr.s3d", "global4_chr.s3d",
	"poknowledge_chr.txt", "mur.eqg", "scu.eqg", "frd.eqg", "ddv.eqg", "srn.eqg",
}, classicModelNames...), manifest.LoadingScreenPaths()...)

type gameplayFile struct {
	Size   int64  `json:"size"`
	SHA256 string `json:"sha256"`
}

// The proxy embeds these hashes too. Catch a mismatched generation before
// signing a release that would fail the mandatory startup asset gate.
func validateClassicModels(files map[string][]byte) error {
	for name, expected := range classicModelDigests {
		data, exists := files[name]
		if !exists || manifest.Digest(data) != expected {
			return fmt.Errorf("classic model contract mismatch: %s", name)
		}
	}
	return nil
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
		if strings.HasPrefix(name, "uifiles/nightcap/") && strings.HasSuffix(name, ".xml") {
			if err := validateNativeSkin(data); err != nil {
				return nil, fmt.Errorf("%s: %w", name, err)
			}
		}
		files[name] = data
	}
	return files, nil
}

// The pinned native parser reads literal Schema/xmlns/xmlns:dt names rather
// than resolving namespace aliases. Valid generic XML can still be rejected.
func validateNativeSkin(data []byte) error {
	decoder := xml.NewDecoder(bytes.NewReader(data))
	decoder.CharsetReader = func(charset string, input io.Reader) (io.Reader, error) {
		if strings.EqualFold(charset, "us-ascii") {
			for _, value := range data {
				if value >= 128 {
					return nil, fmt.Errorf("non-ASCII byte in ASCII skin")
				}
			}
			return input, nil
		}
		return nil, fmt.Errorf("unsupported skin encoding %q", charset)
	}
	var stack []xml.Name
	roots, schemas := 0, 0
	for {
		token, err := decoder.RawToken() // Preserve lexical prefixes used by RoF2.
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("invalid skin XML: %w", err)
		}
		switch value := token.(type) {
		case xml.StartElement:
			if len(stack) == 0 {
				roots++
				if roots != 1 || value.Name.Space != "" || value.Name.Local != "XML" {
					return fmt.Errorf("invalid skin root")
				}
			}
			if len(stack) == 1 && value.Name.Local == "Schema" {
				schemas++
				if value.Name.Space != "" {
					return fmt.Errorf("native Schema must be unprefixed")
				}
				xmlns, dt := 0, 0
				for _, attribute := range value.Attr {
					if attribute.Name.Space == "" && attribute.Name.Local == "xmlns" && attribute.Value == "EverQuestData" {
						xmlns++
					}
					if attribute.Name.Space == "xmlns" && attribute.Name.Local == "dt" && attribute.Value == "EverQuestDataTypes" {
						dt++
					}
				}
				if xmlns != 1 || dt != 1 {
					return fmt.Errorf("native Schema requires both literal namespace declarations")
				}
			}
			stack = append(stack, value.Name)
		case xml.EndElement:
			if len(stack) == 0 || stack[len(stack)-1] != value.Name {
				return fmt.Errorf("mismatched skin element")
			}
			stack = stack[:len(stack)-1]
		case xml.CharData:
			if len(stack) == 0 && strings.TrimSpace(string(value)) != "" {
				return fmt.Errorf("text outside skin root")
			}
		}
	}
	if len(stack) != 0 || roots != 1 || schemas != 1 {
		return fmt.Errorf("skin requires one complete root and native Schema child")
	}
	return nil
}

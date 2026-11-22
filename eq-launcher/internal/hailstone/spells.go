package hailstone

import (
	"bytes"
	_ "embed"
	"fmt"
	"os"
	"path/filepath"
)

//go:embed starters.txt
var starterRows []byte

// Compose an overlay from the player's installed catalog and the three Nightcap
// records. An existing record must agree exactly before it can be reused.
func spellOverlay(base, additions []byte) ([]byte, error) {
	wanted := map[string][]byte{}
	for _, row := range bytes.Split(bytes.TrimSpace(additions), []byte("\n")) {
		row = bytes.TrimSuffix(row, []byte("\r"))
		id, _, ok := bytes.Cut(row, []byte("^"))
		if !ok {
			return nil, fmt.Errorf("invalid starter spell")
		}
		wanted[string(id)] = row
	}
	seen := map[string]bool{}
	for _, row := range bytes.Split(base, []byte("\n")) {
		row = bytes.TrimSuffix(row, []byte("\r"))
		id, _, _ := bytes.Cut(row, []byte("^"))
		if expected, ok := wanted[string(id)]; ok {
			if seen[string(id)] || !bytes.Equal(expected, row) {
				return nil, fmt.Errorf("conflicting spell %s", id)
			}
			seen[string(id)] = true
		}
	}
	for _, row := range bytes.Split(bytes.TrimSpace(additions), []byte("\n")) {
		id, _, _ := bytes.Cut(row, []byte("^"))
		if !seen[string(id)] {
			if len(base) > 0 && base[len(base)-1] != '\n' {
				base = append(base, '\n')
			}
			base = append(base, bytes.TrimSuffix(row, []byte("\r"))...)
			base = append(base, '\n')
		}
	}
	return base, nil
}

func installSpellOverlay(gameDir, server string) error {
	base, err := os.ReadFile(filepath.Join(gameDir, "spells_us.txt"))
	if err != nil {
		return err
	}
	rows, err := spellOverlay(base, starterRows)
	if err != nil {
		return err
	}
	dir := filepath.Join(server, "assets")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}
	temp, err := os.CreateTemp(dir, "spells-")
	if err != nil {
		return err
	}
	defer os.Remove(temp.Name())
	_, writeErr := temp.Write(rows)
	closeErr := temp.Close()
	if writeErr != nil {
		return writeErr
	}
	if closeErr != nil {
		return closeErr
	}
	return os.Rename(temp.Name(), filepath.Join(dir, "spells_us.txt"))
}

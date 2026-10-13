package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"nightcap/eq-launcher/internal/manifest"
)

func loadPatchNotes(path string, release uint64) ([]manifest.PatchNote, error) {
	if path == "" {
		return nil, nil
	}
	raw, err := readBounded(path, 512<<10)
	if err != nil {
		return nil, err
	}
	var notes []manifest.PatchNote
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&notes); err != nil {
		return nil, err
	}
	var extra any
	if decoder.Decode(&extra) != io.EOF {
		return nil, fmt.Errorf("trailing patch note data")
	}
	if len(notes) == 0 {
		return nil, fmt.Errorf("patch history must not be empty")
	}
	if err = manifest.ValidatePatchNotes(notes, release); err != nil {
		return nil, err
	}
	return notes, nil
}

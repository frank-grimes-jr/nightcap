package installer

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/manifest"
)

// Inspection is read-only evidence, never permission to launch.
type Inspection struct {
	Present           bool
	Release           uint64
	ManifestDigest    string
	RecoveryRequired  bool
	Current           bool
	ValidationMessage string
}

func Inspect(ctx context.Context, clientDir string, trust manifest.Trust) (Inspection, error) {
	root, err := os.OpenRoot(clientDir)
	if err != nil {
		return Inspection{}, err
	}
	defer root.Close()
	if _, err := readPending(root); err == nil {
		return Inspection{RecoveryRequired: true}, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return Inspection{RecoveryRequired: true}, err
	}
	data, err := readBounded(root, ".nightcap/active.json", maxStateBytes)
	if errors.Is(err, os.ErrNotExist) {
		return Inspection{}, nil
	}
	if err != nil {
		return Inspection{}, err
	}
	a, err := decodeActive(data)
	if err != nil {
		return Inspection{}, err
	}
	report := Inspection{Present: true, Release: a.Release, ManifestDigest: a.ManifestDigest}
	if a.Release > trust.HighestRelease {
		trust.HighestRelease = a.Release
		trust.HighestDigest = a.ManifestDigest
	}
	if _, err = manifest.Verify(a.Manifest, a.Signature, trust); err != nil {
		report.ValidationMessage = err.Error()
		return report, nil
	}
	diff, err := assets.Inspect(ctx, a.Manifest, a.Signature, trust, clientDir)
	if err != nil {
		return report, err
	}
	report.Current = len(diff.Remove) == 0
	for _, f := range diff.Files {
		if f.State != assets.Current {
			report.Current = false
		}
	}
	return report, nil
}

// decodeActive checks checkpoint integrity before using its release floor.
func decodeActive(data []byte) (activeRecord, error) {
	var a activeRecord
	if err := decode(data, &a); err != nil {
		return a, err
	}
	var m manifest.Manifest
	if json.Unmarshal(a.Manifest, &m) != nil || m.Release != a.Release || a.Release == 0 || manifest.Digest(a.Manifest) != a.ManifestDigest {
		return a, fmt.Errorf("invalid active checkpoint")
	}
	return a, nil
}

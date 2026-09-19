package assets

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"nightcap/eq-launcher/internal/manifest"
	"os"
)

// BundleMetadata reads a compiled local source. The caller must authenticate it
// with launcher-owned trust before it can supply update or launch authority.
func BundleMetadata(bundle fs.FS) ([]byte, manifest.Signature, error) {
	raw, err := readBundleFile(bundle, "manifest.json", manifest.MaxManifestBytes)
	if err != nil {
		return nil, manifest.Signature{}, err
	}
	encoded, err := readBundleFile(bundle, "signature.json", 4096)
	if err != nil {
		return nil, manifest.Signature{}, err
	}
	var sig manifest.Signature
	if err = json.Unmarshal(encoded, &sig); err != nil {
		return nil, sig, err
	}
	canonical, err := json.Marshal(sig)
	if err != nil || !bytes.Equal(canonical, encoded) {
		return nil, sig, fmt.Errorf("noncanonical bundle signature")
	}
	return raw, sig, nil
}
func readBundleFile(bundle fs.FS, name string, limit int64) (data []byte, err error) {
	file, err := bundle.Open(name)
	if err != nil {
		return nil, err
	}
	defer func() { err = errors.Join(err, file.Close()) }()
	info, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("invalid bundle metadata size/type")
	}
	data, err = io.ReadAll(io.LimitReader(file, limit+1))
	if err == nil && int64(len(data)) > limit {
		err = fmt.Errorf("bundle metadata too large")
	}
	return data, err
}

// StageBundle reads only the trusted caller's compiled FS and never uses HTTP.
// Signed paths select assets; URL fields are not used as filesystem paths.
func StageBundle(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir, stagingParent string, bundle fs.FS) (Generation, error) {
	return stageFrom(ctx, raw, sig, trust, clientDir, stagingParent, func(ctx context.Context, out *os.File, entry manifest.File) (err error) {
		file, err := bundle.Open("files/" + entry.Path)
		if err != nil {
			return err
		}
		defer func() { err = errors.Join(err, file.Close()) }()
		info, err := file.Stat()
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() || info.Size() != entry.Size {
			return fmt.Errorf("invalid bundle asset size/type")
		}
		return verifyCopy(ctx, out, file, entry)
	}, func(root *os.Root, name string) error { return root.RemoveAll(name) })
}

package preflight

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"regexp"

	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/manifest"
)

var featureName = regexp.MustCompile(`^[a-z][a-z0-9_]{0,63}$`)

// signedCatalog validates syntax and immutable compatibility boundaries. Callers
// must first authenticate these exact bytes using the signed generation hash.
func signedCatalog(raw []byte) (catalog, error) {
	var c catalog
	if len(raw) == 0 || len(raw) > MaxCatalogBytes {
		return c, fmt.Errorf("catalog size invalid")
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&c); err != nil {
		return c, err
	}
	canonical, err := json.Marshal(c)
	if err != nil || !bytes.Equal(raw, canonical) {
		return c, fmt.Errorf("noncanonical catalog")
	}
	if c.Schema != 1 || c.RuntimeSchema != 1 || c.ClientSize != client.SupportedSize || c.ClientSHA256 != client.SupportedSHA256 || c.ImageBase != 0x400000 || len(c.Required) < 1 || len(c.Required) > 31 || len(c.Optional) > 31 || len(c.Sites) < 1 || len(c.Sites) > 256 || c.ProxyVersion == "" || len(c.ProxyVersion) > 64 {
		return c, fmt.Errorf("unsupported catalog contract")
	}
	features := map[string]bool{"schema": true}
	for _, name := range append(append([]string{}, c.Required...), c.Optional...) {
		if features[name] || !featureName.MatchString(name) {
			return c, fmt.Errorf("invalid or duplicate feature")
		}
		features[name] = true
	}
	names := map[string]bool{}
	sites := map[uint32]bool{}
	for _, site := range c.Sites {
		original, err := hex.DecodeString(site.Original)
		if err != nil || len(original) < 1 || len(original) > 64 || hex.EncodeToString(original) != site.Original || site.Name == "" || len(site.Name) > 128 || names[site.Name] || sites[site.RVA] || uint64(site.RVA)+uint64(len(original)) > 1<<32 {
			return c, fmt.Errorf("invalid or duplicate catalog site")
		}
		names[site.Name] = true
		sites[site.RVA] = true
	}
	return c, nil
}

// CheckSignedOpen is used only after the manifest and catalog file hash have
// passed verification. It retains the pinned executable and every site check.
func CheckSignedOpen(file interface {
	io.Reader
	io.Seeker
	Stat() (os.FileInfo, error)
}, config, metadata []byte) (Report, error) {
	c, err := signedCatalog(metadata)
	if err != nil {
		return Report{}, err
	}
	return checkOpen(file, config, c)
}

func RuntimeForCatalog(metadata []byte) (RuntimePolicy, error) {
	c, err := signedCatalog(metadata)
	if err != nil {
		return RuntimePolicy{}, err
	}
	return RuntimePolicy{Schema: c.RuntimeSchema, ProxyVersion: c.ProxyVersion, CatalogSHA256: manifest.Digest(metadata), RequiredMask: (uint32(1) << len(c.Required)) - 1}, nil
}

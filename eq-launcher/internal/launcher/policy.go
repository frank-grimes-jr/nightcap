package launcher

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"time"

	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

// Policy is compiled release configuration, never supplied through the UI or
// downloaded metadata. Preview builds intentionally have no production keys.
type Policy struct {
	// Bundle is a compiled, signed offline source. There is no network fallback.
	Bundle fs.FS
	Label  string
	// EnablePlay is release-owned and stays false in development previews.
	EnablePlay   bool
	ManifestURL  string
	SignatureURL string
	Trust        manifest.Trust
}

func (p Policy) configured() bool {
	return len(p.Trust.Keys) > 0 && len(p.Trust.Inventory) > 0 && (p.Bundle != nil || (p.ManifestURL != "" && p.SignatureURL != ""))
}
func (p Policy) playConfigured() bool {
	if !p.EnablePlay || !p.configured() || p.Trust.LauncherVersion == "" {
		return false
	}
	for _, name := range []string{"dinput8.dll", installer.HelperPath, preflight.ConfigPath, preflight.CatalogPath} {
		if !p.Trust.Inventory[name] {
			return false
		}
	}
	now := time.Now().UTC()
	for _, key := range p.Trust.Keys {
		if len(key.Public) == ed25519.PublicKeySize && !now.Before(key.NotBefore) && now.Before(key.NotAfter) {
			return true
		}
	}
	return false
}
func fetchRelease(ctx context.Context, p Policy) ([]byte, manifest.Signature, error) {
	if err := ctx.Err(); err != nil {
		return nil, manifest.Signature{}, err
	}
	if p.Bundle != nil {
		return assets.BundleMetadata(p.Bundle)
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.DisableCompression = true
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: 30 * time.Second, CheckRedirect: func(req *http.Request, via []*http.Request) error {
		if len(via) >= 5 {
			return fmt.Errorf("release redirect limit exceeded")
		}
		return manifest.ValidateURL(req.URL.String(), p.Trust.Hosts)
	}}
	return fetchWithClient(ctx, p, client)
}
func fetchWithClient(ctx context.Context, p Policy, client *http.Client) ([]byte, manifest.Signature, error) {
	get := func(address string, limit int64) ([]byte, error) {
		if err := manifest.ValidateURL(address, p.Trust.Hosts); err != nil {
			return nil, err
		}
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, address, nil)
		if err != nil {
			return nil, err
		}
		req.Header.Set("Accept-Encoding", "identity")
		response, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		defer response.Body.Close()
		if response.StatusCode != 200 {
			return nil, fmt.Errorf("release service returned HTTP %d", response.StatusCode)
		}
		if response.Uncompressed || (response.Header.Get("Content-Encoding") != "" && response.Header.Get("Content-Encoding") != "identity") {
			return nil, fmt.Errorf("encoded release metadata rejected")
		}
		body, err := io.ReadAll(io.LimitReader(response.Body, limit+1))
		if err != nil {
			return nil, err
		}
		if int64(len(body)) > limit {
			return nil, fmt.Errorf("release metadata size limit exceeded")
		}
		return body, nil
	}
	raw, err := get(p.ManifestURL, manifest.MaxManifestBytes)
	if err != nil {
		return nil, manifest.Signature{}, err
	}
	sigBytes, err := get(p.SignatureURL, 4096)
	if err != nil {
		return nil, manifest.Signature{}, err
	}
	var sig manifest.Signature
	d := json.NewDecoder(bytes.NewReader(sigBytes))
	d.DisallowUnknownFields()
	if err = d.Decode(&sig); err != nil {
		return nil, sig, err
	}
	canonical, err := json.Marshal(sig)
	if err != nil || !bytes.Equal(canonical, sigBytes) {
		return nil, sig, fmt.Errorf("noncanonical release signature")
	}
	return raw, sig, nil
}

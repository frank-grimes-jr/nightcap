package launcher

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"strings"
	"testing"

	"nightcap/eq-launcher/internal/manifest"
)

type metadataTransport func(*http.Request) (*http.Response, error)

func (f metadataTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestFetchMetadataBoundaries(t *testing.T) {
	for _, mode := range []string{"valid", "large manifest", "large signature", "encoded", "status", "unknown signature field", "trailing signature", "http"} {
		t.Run(mode, func(t *testing.T) {
			p := Policy{ManifestURL: "https://release.test/manifest.json", SignatureURL: "https://release.test/signature.json", Trust: manifest.Trust{Hosts: []string{"release.test"}}}
			if mode == "http" {
				p.ManifestURL = "http://release.test/manifest.json"
			}
			calls := 0
			client := &http.Client{Transport: metadataTransport(func(r *http.Request) (*http.Response, error) {
				calls++
				if r.Header.Get("Accept-Encoding") != "identity" {
					t.Fatal("compression not disabled")
				}
				body := "{}"
				header := http.Header{}
				status := 200
				if strings.HasSuffix(r.URL.Path, "signature.json") {
					sig, _ := json.Marshal(manifest.Signature{KeyID: "fixture", Bytes: []byte{1, 2, 3}})
					body = string(sig)
					if mode == "large signature" {
						body = strings.Repeat("x", 4097)
					}
					if mode == "unknown signature field" {
						body = strings.TrimSuffix(body, "}") + `,"extra":true}`
					}
					if mode == "trailing signature" {
						body += "{}"
					}
				} else if mode == "large manifest" {
					body = strings.Repeat("x", manifest.MaxManifestBytes+1)
				}
				if mode == "encoded" {
					header.Set("Content-Encoding", "gzip")
				}
				if mode == "status" {
					status = 503
				}
				return &http.Response{StatusCode: status, Header: header, Body: io.NopCloser(strings.NewReader(body)), Request: r}, nil
			})}
			raw, sig, err := fetchWithClient(context.Background(), p, client)
			if mode == "valid" {
				if err != nil || string(raw) != "{}" || sig.KeyID != "fixture" || calls != 2 {
					t.Fatalf("valid fetch failed: %s %+v %v calls=%d", raw, sig, err, calls)
				}
			} else if err == nil {
				t.Fatal("invalid metadata accepted")
			}
			if mode == "http" && calls != 0 {
				t.Fatal("unsafe URL reached transport")
			}
		})
	}
}

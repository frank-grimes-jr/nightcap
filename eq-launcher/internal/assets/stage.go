package assets

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"time"

	"nightcap/eq-launcher/internal/manifest"
)

// Generation is staging evidence, not an activation or Play authorization.
// A future installer must reverify content and metadata under its process lock.
type Generation struct {
	Directory      string
	Release        uint64
	ManifestDigest string
}

// Stage creates a fresh complete candidate under an existing trusted staging
// parent. Current local files are copied and rehashed; missing/changed ones are
// downloaded. No installed files or tombstones are changed. Failure removes only
// the newly created staging directory. Interrupted-process cleanup is separate.
func Stage(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir, stagingParent string) (Generation, error) {
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.DisableCompression = true
	defer transport.CloseIdleConnections()
	return stage(ctx, raw, sig, trust, clientDir, stagingParent, transport)
}
func stage(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir, stagingParent string, transport http.RoundTripper) (Generation, error) {
	return stageWithCleanup(ctx, raw, sig, trust, clientDir, stagingParent, transport, func(root *os.Root, name string) error { return root.RemoveAll(name) })
}
func stageWithCleanup(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir, stagingParent string, transport http.RoundTripper, cleanup func(*os.Root, string) error) (Generation, error) {
	hosts := append([]string(nil), trust.Hosts...)
	downloader := &http.Client{Transport: transport, Timeout: 2 * time.Minute, CheckRedirect: func(req *http.Request, via []*http.Request) error {
		if len(via) >= 5 {
			return fmt.Errorf("release redirect limit exceeded")
		}
		return manifest.ValidateURL(req.URL.String(), hosts)
	}}
	return stageFrom(ctx, raw, sig, trust, clientDir, stagingParent, func(ctx context.Context, out *os.File, f manifest.File) error {
		return download(ctx, downloader, hosts, out, f)
	}, cleanup)
}

// Every source shares signed verification, complete staging and cleanup semantics.
func stageFrom(ctx context.Context, raw []byte, sig manifest.Signature, trust manifest.Trust, clientDir, stagingParent string, source func(context.Context, *os.File, manifest.File) error, cleanup func(*os.Root, string) error) (generation Generation, stageErr error) {
	m, err := manifest.Verify(raw, sig, trust)
	if err != nil {
		return Generation{}, err
	}
	if err = ctx.Err(); err != nil {
		return Generation{}, err
	}
	clientRoot, err := os.OpenRoot(clientDir)
	if err != nil {
		return Generation{}, err
	}
	defer clientRoot.Close()
	diff, err := inspect(ctx, m, clientRoot)
	if err != nil {
		return Generation{}, err
	}
	parentPath, err := filepath.Abs(stagingParent)
	if err != nil {
		return Generation{}, err
	}
	parent, err := os.OpenRoot(parentPath)
	if err != nil {
		return Generation{}, err
	}
	defer parent.Close()
	if err = outsideClient(clientRoot, parent, parentPath); err != nil {
		return Generation{}, err
	}
	name := fmt.Sprintf("release-%d-%s", m.Release, rand.Text())
	if err = parent.Mkdir(name, 0700); err != nil {
		return Generation{}, err
	}
	complete := false
	defer func() {
		if !complete {
			if cleanupErr := cleanup(parent, name); cleanupErr != nil {
				stageErr = errors.Join(stageErr, fmt.Errorf("cleanup incomplete staging %s: %w", filepath.Join(parentPath, name), cleanupErr))
				generation = Generation{}
			}
		}
	}()
	candidate, err := parent.OpenRoot(name)
	if err != nil {
		return Generation{}, err
	}
	defer candidate.Close()
	if err = candidate.Mkdir("files", 0700); err != nil {
		return Generation{}, err
	}
	files, err := candidate.OpenRoot("files")
	if err != nil {
		return Generation{}, err
	}
	defer files.Close()

	for i, f := range m.Files {
		if err = ctx.Err(); err != nil {
			return Generation{}, err
		}
		if err = files.MkdirAll(path.Dir(f.Path), 0700); err != nil {
			return Generation{}, err
		}
		out, err := files.OpenFile(f.Path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			return Generation{}, err
		}
		if diff.Files[i].State == Current {
			in, openErr := openRegular(clientRoot, f.Path)
			if openErr != nil {
				out.Close()
				return Generation{}, openErr
			}
			err = verifyCopy(ctx, out, in, f)
			if closeErr := in.Close(); err == nil {
				err = closeErr
			}
		} else {
			err = source(ctx, out, f)
		}
		if err == nil {
			err = out.Sync()
		}
		if closeErr := out.Close(); err == nil {
			err = closeErr
		}
		if err != nil {
			return Generation{}, fmt.Errorf("stage %s: %w", f.Path, err)
		}
	}
	signature, err := json.Marshal(sig)
	if err != nil {
		return Generation{}, err
	}
	for name, data := range map[string][]byte{"manifest.json": raw, "signature.json": signature} {
		file, err := candidate.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			return Generation{}, err
		}
		_, err = file.Write(data)
		if err == nil {
			err = file.Sync()
		}
		if closeErr := file.Close(); err == nil {
			err = closeErr
		}
		if err != nil {
			return Generation{}, err
		}
	}
	if err = ctx.Err(); err != nil {
		return Generation{}, err
	}
	generation = Generation{Directory: filepath.Join(parentPath, name), Release: m.Release, ManifestDigest: manifest.Digest(raw)}
	marker, err := json.Marshal(generation)
	if err != nil {
		return Generation{}, err
	}
	markerFile, err := candidate.OpenFile("complete.json", os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return Generation{}, err
	}
	_, err = markerFile.Write(marker)
	if err == nil {
		err = markerFile.Sync()
	}
	if closeErr := markerFile.Close(); err == nil {
		err = closeErr
	}
	if err != nil {
		return Generation{}, err
	}
	complete = true
	return generation, nil
}
func download(ctx context.Context, client *http.Client, hosts []string, out *os.File, f manifest.File) error {
	if err := manifest.ValidateURL(f.URL, hosts); err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, f.URL, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Accept-Encoding", "identity")
	response, err := client.Do(req)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return fmt.Errorf("release HTTP status %d", response.StatusCode)
	}
	if response.Uncompressed || (response.Header.Get("Content-Encoding") != "" && response.Header.Get("Content-Encoding") != "identity") {
		return fmt.Errorf("encoded release body rejected")
	}
	if response.ContentLength >= 0 && response.ContentLength != f.Size {
		return errContent
	}
	return verifyCopy(ctx, out, response.Body, f)
}

// Compare physical directory identities, not string prefixes. EvalSymlinks
// resolves Windows junction aliases; each ancestor is compared to the pinned
// client root. Verify the resolved parent still names our pinned parent handle.
// Staging roots are app/user-selected trusted locations, not manifest input.
func outsideClient(client, parent *os.Root, parentPath string) error {
	resolved, err := filepath.EvalSymlinks(parentPath)
	if err != nil {
		return err
	}
	pinned, err := parent.Stat(".")
	if err != nil {
		return err
	}
	actual, err := os.Stat(resolved)
	if err != nil {
		return err
	}
	if !os.SameFile(pinned, actual) {
		return fmt.Errorf("staging parent changed during resolution")
	}
	clientInfo, err := client.Stat(".")
	if err != nil {
		return err
	}
	for {
		info, err := os.Stat(resolved)
		if err != nil {
			return err
		}
		if os.SameFile(clientInfo, info) {
			return fmt.Errorf("staging directory must be outside client directory")
		}
		next := filepath.Dir(resolved)
		if next == resolved {
			return nil
		}
		resolved = next
	}
}

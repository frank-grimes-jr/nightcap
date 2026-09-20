package selfupdate

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"nightcap/eq-launcher/internal/launchlock"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"time"
)

const ImageName = "nightcap-desktop.exe"

type Lease struct {
	Channel Channel
	Path    string
	locks   *launchlock.Set
}

func (l *Lease) Close() error { return l.locks.Close() }

// Fetch is private to the caller's compiled HTTPS/host policy; redirects are checked too.
func fetch(ctx context.Context, address string, limit int64, hosts []string) ([]byte, error) {
	if err := manifest.ValidateURL(address, hosts); err != nil {
		return nil, err
	}
	tr := http.DefaultTransport.(*http.Transport).Clone()
	tr.DisableCompression = true
	defer tr.CloseIdleConnections()
	client := &http.Client{Transport: tr, Timeout: 5 * time.Minute, CheckRedirect: func(r *http.Request, via []*http.Request) error {
		if len(via) >= 5 {
			return fmt.Errorf("launcher redirect limit")
		}
		return manifest.ValidateURL(r.URL.String(), hosts)
	}}
	req, err := http.NewRequestWithContext(ctx, "GET", address, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept-Encoding", "identity")
	response, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	if response.StatusCode != 200 || response.Uncompressed || (response.Header.Get("Content-Encoding") != "" && response.Header.Get("Content-Encoding") != "identity") {
		return nil, fmt.Errorf("launcher service response rejected (HTTP %d)", response.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(response.Body, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("launcher download exceeds size limit")
	}
	return data, nil
}

// Prepare requires the caller's exclusive starter lock for this cache directory.
// It never selects a cached fallback after network/signature failure.
func Prepare(ctx context.Context, cache, address string, trust manifest.Trust, progress func(string)) (*Lease, error) {
	return prepare(ctx, cache, address, trust, progress, func(ctx context.Context, u string, n int64) ([]byte, error) { return fetch(ctx, u, n, trust.Hosts) })
}
func prepare(ctx context.Context, cache, address string, trust manifest.Trust, progress func(string), get func(context.Context, string, int64) ([]byte, error)) (*Lease, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(cache, 0700); err != nil {
		return nil, err
	}
	root, err := os.OpenRoot(cache)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	var floor Checkpoint
	if b, e := read(root, "checkpoint.json", 4096); e == nil {
		if err = strict(b, &floor); err != nil || floor.Release == 0 || !digestPattern.MatchString(floor.Digest) {
			return nil, fmt.Errorf("invalid launcher checkpoint")
		}
	} else if !errors.Is(e, os.ErrNotExist) {
		return nil, e
	}
	progress("Checking for launcher updates…")
	raw, err := get(ctx, address, MaxChannelBytes)
	if err != nil {
		return nil, err
	}
	trust.Now = time.Now().UTC()
	c, err := Verify(raw, trust, floor)
	if err != nil {
		return nil, err
	}
	name := c.SHA256 + "/" + ImageName
	if err = root.MkdirAll(c.SHA256, 0700); err != nil {
		return nil, err
	}
	if err = verify(root, name, c); err != nil {
		progress("Downloading launcher " + c.Version + "…")
		data, err := get(ctx, c.URL, c.Size)
		if err != nil {
			return nil, err
		}
		if int64(len(data)) != c.Size || manifest.Digest(data) != c.SHA256 {
			return nil, fmt.Errorf("launcher download hash mismatch")
		}
		if err = atomic(root, name, data); err != nil {
			return nil, err
		}
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	// Windows deny-write/delete handles pin both the image and ancestors through execution.
	locks, err := launchlock.AcquireImage(filepath.Join(cache, c.SHA256), ImageName)
	if err != nil {
		return nil, err
	}
	keep := false
	defer func() {
		if !keep {
			locks.Close()
		}
	}()
	f, err := locks.Open(ImageName)
	if err != nil {
		return nil, err
	}
	h := sha256.New()
	n, err := io.Copy(h, io.NewSectionReader(f, 0, c.Size+1))
	if err != nil || n != c.Size || hex.EncodeToString(h.Sum(nil)) != c.SHA256 {
		return nil, fmt.Errorf("cached launcher verification failed")
	}
	// Refresh time after the download; no expired metadata may authorize execution.
	trust.Now = time.Now().UTC()
	if _, err = Verify(raw, trust, floor); err != nil {
		return nil, err
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	b, _ := json.Marshal(checkpoint(c))
	if err = atomic(root, "checkpoint.json", b); err != nil {
		return nil, err
	}
	progress("Opening Nightcap…")
	keep = true
	return &Lease{Channel: c, Path: filepath.Join(cache, c.SHA256, ImageName), locks: locks}, nil
}
func read(root *os.Root, name string, limit int64) ([]byte, error) {
	f, err := root.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() {
		return nil, fmt.Errorf("nonregular launcher state")
	}
	b, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(b)) > limit {
		return nil, fmt.Errorf("oversized launcher state")
	}
	return b, nil
}
func verify(root *os.Root, name string, c Channel) error {
	b, err := read(root, name, c.Size)
	if err != nil {
		return err
	}
	if int64(len(b)) != c.Size || manifest.Digest(b) != c.SHA256 {
		return fmt.Errorf("cached launcher mismatch")
	}
	return nil
}
func atomic(root *os.Root, name string, data []byte) error {
	temp := name + ".partial"
	if err := root.Remove(temp); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	f, err := root.OpenFile(temp, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0700)
	if err != nil {
		return err
	}
	_, err = f.Write(data)
	err = errors.Join(err, f.Sync(), f.Close())
	if err != nil {
		return err
	}
	return root.Rename(temp, name)
}

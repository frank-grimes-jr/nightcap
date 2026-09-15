package installer

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path"
	"strings"

	"nightcap/eq-launcher/internal/manifest"
)

const maxStateBytes = 2 << 20

// Pin each directory separately. Reject links/junctions and check that opening
// the child still refers to the directory inspected before the open.
func parentOf(root *os.Root, name string, create bool) (*os.Root, string, error) {
	current, err := root.OpenRoot(".")
	if err != nil {
		return nil, "", err
	}
	dirs := path.Dir(name)
	if dirs != "." {
		for _, part := range strings.Split(dirs, "/") {
			info, err := current.Lstat(part)
			if errors.Is(err, os.ErrNotExist) && create {
				err = current.Mkdir(part, 0700)
				if err == nil || errors.Is(err, os.ErrExist) {
					info, err = current.Lstat(part)
				}
			}
			if err != nil {
				current.Close()
				return nil, "", err
			}
			if !info.IsDir() || info.Mode()&(os.ModeSymlink|os.ModeIrregular) != 0 {
				current.Close()
				return nil, "", fmt.Errorf("unsafe directory in %s", name)
			}
			next, err := current.OpenRoot(part)
			if err != nil {
				current.Close()
				return nil, "", err
			}
			opened, err := next.Stat(".")
			if err != nil || !os.SameFile(info, opened) {
				next.Close()
				current.Close()
				return nil, "", fmt.Errorf("directory changed in %s", name)
			}
			current.Close()
			current = next
		}
	}
	return current, path.Base(name), nil
}
func regular(root *os.Root, name string) (*os.File, error) {
	p, base, err := parentOf(root, name, false)
	if err != nil {
		return nil, err
	}
	defer p.Close()
	info, err := p.Lstat(base)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() {
		return nil, fmt.Errorf("nonregular file %s", name)
	}
	f, err := p.Open(base)
	if err != nil {
		return nil, err
	}
	opened, err := f.Stat()
	if err != nil || !opened.Mode().IsRegular() || !os.SameFile(info, opened) {
		f.Close()
		return nil, fmt.Errorf("file changed in %s", name)
	}
	return f, nil
}
func readBounded(root *os.Root, name string, limit int64) ([]byte, error) {
	f, err := regular(root, name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("oversized state %s", name)
	}
	return data, nil
}
func decode(data []byte, target any) error {
	d := json.NewDecoder(bytes.NewReader(data))
	d.DisallowUnknownFields()
	if err := d.Decode(target); err != nil {
		return err
	}
	canonical, err := json.Marshal(target)
	if err != nil || !bytes.Equal(canonical, data) {
		return fmt.Errorf("noncanonical recovery state")
	}
	return nil
}
func copyHash(dst io.Writer, src io.Reader, size int64) (string, error) {
	hash := sha256.New()
	n, err := io.Copy(io.MultiWriter(dst, hash), io.LimitReader(src, size+1))
	if err != nil {
		return "", err
	}
	if n != size {
		return "", fmt.Errorf("file size changed")
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}
func verify(root *os.Root, name string, size int64, digest string) error {
	f, err := regular(root, name)
	if err != nil {
		return err
	}
	defer f.Close()
	got, err := copyHash(io.Discard, f, size)
	if err != nil {
		return err
	}
	if got != digest {
		return fmt.Errorf("hash mismatch: %s", name)
	}
	return nil
}
func newBlob(root *os.Root, name string, data []byte) error {
	p, base, err := parentOf(root, name, true)
	if err != nil {
		return err
	}
	defer p.Close()
	f, err := p.OpenFile(base, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	_, err = f.Write(data)
	if err == nil {
		err = f.Sync()
	}
	return errors.Join(err, f.Close())
}
func removeRegular(root *os.Root, name string) error {
	p, base, err := parentOf(root, name, false)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	defer p.Close()
	info, err := p.Lstat(base)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("refuse removing nonregular %s", name)
	}
	return p.Remove(base)
}
func temporary(id string, index int) string { return fmt.Sprintf(".nightcap-%s-%d.tmp", id, index) }

// All replacements stay in one pinned parent directory and filesystem. The
// immutable backup remains intact until recovery is no longer required.
func replace(root *os.Root, name string, src io.Reader, size int64, digest, id string, index int) error {
	p, base, err := parentOf(root, name, true)
	if err != nil {
		return err
	}
	defer p.Close()
	if info, e := p.Lstat(base); e == nil && !info.Mode().IsRegular() {
		return fmt.Errorf("nonregular destination %s", name)
	} else if e != nil && !errors.Is(e, os.ErrNotExist) {
		return e
	}
	temp := temporary(id, index)
	// Only a transaction-derived private temporary name is eligible for reuse
	// during recovery after a process stopped before rename.
	if err = removeRegular(p, temp); err != nil {
		return err
	}
	f, err := p.OpenFile(temp, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	got, err := copyHash(f, src, size)
	if err == nil && got != digest {
		err = fmt.Errorf("replacement hash mismatch: %s", name)
	}
	if err == nil {
		err = f.Sync()
	}
	err = errors.Join(err, f.Close())
	if err != nil {
		return err
	}
	return p.Rename(temp, base)
}
func replaceBlob(root *os.Root, name string, data []byte, id string, index int) error {
	return replace(root, name, bytes.NewReader(data), int64(len(data)), manifest.Digest(data), id, index)
}
func verifyStage(ctx context.Context, root *os.Root, m manifest.Manifest) error {
	for _, f := range m.Files {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := verify(root, "files/"+f.Path, f.Size, f.SHA256); err != nil {
			return err
		}
	}
	return nil
}

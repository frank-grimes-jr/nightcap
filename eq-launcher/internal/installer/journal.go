package installer

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path"
	"regexp"

	"nightcap/eq-launcher/internal/manifest"
)

type pendingRecord struct {
	ID     string
	SHA256 string
}
type entry struct {
	Path    string
	Existed bool
	Size    int64
	SHA256  string
}
type journal struct {
	Schema    int
	ID        string
	Entries   []entry
	Manifest  []byte             `json:",omitempty"`
	Signature manifest.Signature `json:",omitzero"`
}

var transactionID = regexp.MustCompile(`^[0-9a-f]{32}$`)
var hashID = regexp.MustCompile(`^[0-9a-f]{64}$`)

func txPath(id string) string                { return ".nightcap/tx/" + id }
func backupPath(id string, index int) string { return fmt.Sprintf("%s/backup/%d", txPath(id), index) }
func readPending(root *os.Root) (pendingRecord, error) {
	var p pendingRecord
	b, err := readBounded(root, ".nightcap/pending.json", 1024)
	if err != nil {
		return p, err
	}
	if err = decode(b, &p); err != nil {
		return p, err
	}
	if !transactionID.MatchString(p.ID) || !hashID.MatchString(p.SHA256) {
		return p, fmt.Errorf("invalid pending transaction")
	}
	return p, nil
}
func readJournal(root *os.Root, p pendingRecord) (journal, error) {
	var j journal
	b, err := readBounded(root, txPath(p.ID)+"/journal.json", maxStateBytes)
	if err != nil {
		return j, err
	}
	if manifest.Digest(b) != p.SHA256 {
		return j, fmt.Errorf("journal digest mismatch")
	}
	err = decode(b, &j)
	return j, err
}
func validateJournal(j journal, p pendingRecord, trust manifest.Trust) error {
	if (j.Schema != 1 && j.Schema != 2) || j.ID != p.ID || len(j.Entries) < 1 || len(j.Entries) > 2*manifest.MaxFiles+1 {
		return fmt.Errorf("invalid recovery journal")
	}
	allowed := map[string]bool{}
	if j.Schema == 2 {
		m, err := manifest.VerifyRecovery(j.Manifest, j.Signature, trust)
		if err != nil {
			return fmt.Errorf("recovery authority: %w", err)
		}
		for _, f := range m.Files {
			allowed[f.Path] = true
		}
		for _, name := range m.Tombstones {
			allowed[name] = true
		}
		if len(j.Entries) != len(allowed)+1 {
			return fmt.Errorf("incomplete recovery inventory")
		}
	} else {
		if len(j.Manifest) != 0 || j.Signature.KeyID != "" || len(j.Signature.Bytes) != 0 {
			return fmt.Errorf("unexpected legacy recovery proof")
		}
		for name := range trust.Inventory {
			allowed[name] = true
		}
		for name, retired := range trust.Retired {
			if retired {
				allowed[name] = true
			}
		}
	}
	seen := map[string]bool{}
	var total int64
	for i, e := range j.Entries {
		if seen[e.Path] {
			return fmt.Errorf("duplicate recovery path")
		}
		seen[e.Path] = true
		if e.Path == ".nightcap/active.json" {
			if i != len(j.Entries)-1 {
				return fmt.Errorf("misplaced active record")
			}
		} else {
			if err := manifest.ValidatePath(e.Path); err != nil {
				return err
			}
			if !allowed[e.Path] {
				return fmt.Errorf("unowned recovery path %s", e.Path)
			}
		}
		if e.Existed {
			if e.Size < 0 || e.Size > manifest.MaxFileBytes || !hashID.MatchString(e.SHA256) {
				return fmt.Errorf("invalid backup metadata")
			}
			total += e.Size
		} else if e.Size != 0 || e.SHA256 != "" {
			return fmt.Errorf("invalid absent backup")
		}
	}
	if j.Entries[len(j.Entries)-1].Path != ".nightcap/active.json" || total > manifest.MaxReleaseBytes+maxStateBytes {
		return fmt.Errorf("invalid recovery inventory")
	}
	return nil
}
func snapshot(root *os.Root, id string, paths []string) (journal, error) {
	j := journal{Schema: 1, ID: id, Entries: []entry{}}
	var total int64
	for i, name := range paths {
		e := entry{Path: name}
		in, err := regular(root, name)
		if errors.Is(err, os.ErrNotExist) {
			j.Entries = append(j.Entries, e)
			continue
		}
		if err != nil {
			return j, err
		}
		info, err := in.Stat()
		if err != nil {
			in.Close()
			return j, err
		}
		e.Existed = true
		e.Size = info.Size()
		total += e.Size
		if e.Size > manifest.MaxFileBytes || total > manifest.MaxReleaseBytes+maxStateBytes {
			in.Close()
			return j, fmt.Errorf("backup size limit exceeded")
		}
		p, base, err := parentOf(root, backupPath(id, i), true)
		if err != nil {
			in.Close()
			return j, err
		}
		out, err := p.OpenFile(base, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		p.Close()
		if err != nil {
			in.Close()
			return j, err
		}
		e.SHA256, err = copyHash(out, in, e.Size)
		if err == nil {
			err = out.Sync()
		}
		err = errors.Join(err, out.Close(), in.Close())
		if err != nil {
			return j, err
		}
		j.Entries = append(j.Entries, e)
	}
	return j, nil
}
func recoverLocked(root *os.Root, trust manifest.Trust) error {
	return recoverWithFault(root, trust, nil)
}
func recoverWithFault(root *os.Root, trust manifest.Trust, fault func(string)) error {
	p, err := readPending(root)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	j, err := readJournal(root, p)
	if err != nil {
		return err
	}
	if err = validateJournal(j, p, trust); err != nil {
		return err
	}
	// Validate ALL backups before the first restoration. Keep originals immutable
	// so interrupted or failed recovery can be retried from the same journal.
	for i, e := range j.Entries {
		if e.Existed {
			if err = verify(root, backupPath(p.ID, i), e.Size, e.SHA256); err != nil {
				return fmt.Errorf("recovery backup %s: %w", e.Path, err)
			}
		}
	}
	for _, e := range j.Entries {
		if _, pinned := trust.RetiredSHA256[e.Path]; pinned {
			current, readErr := readBounded(root, e.Path, manifest.MaxFileBytes)
			if readErr != nil && !errors.Is(readErr, os.ErrNotExist) {
				return readErr
			}
			if readErr == nil && (!e.Existed || manifest.Digest(current) != e.SHA256) {
				return fmt.Errorf("recovery conflict: preserve changed retired file %s", e.Path)
			}
		}
	}
	for i, e := range j.Entries {
		// A failed Windows replacement can leave the original intact but held
		// open without delete sharing. Avoid rewriting a verified original;
		// final full-generation verification still gates pending removal.
		if e.Existed && verify(root, e.Path, e.Size, e.SHA256) != nil {
			in, err := regular(root, backupPath(p.ID, i))
			if err != nil {
				return err
			}
			if _, pinned := trust.RetiredSHA256[e.Path]; pinned {
				err = restoreRetired(root, e.Path, in, e.Size, e.SHA256, p.ID, i, fault)
			} else {
				err = replace(root, e.Path, in, e.Size, e.SHA256, p.ID, i)
			}
			err = errors.Join(err, in.Close())
			if err != nil {
				return err
			}
		} else if !e.Existed {
			if _, pinned := trust.RetiredSHA256[e.Path]; pinned {
				if _, e2 := root.Lstat(e.Path); !errors.Is(e2, os.ErrNotExist) {
					return fmt.Errorf("recovery conflict: preserve appeared retired file %s", e.Path)
				}
				continue
			}
			if err = removeRegular(root, e.Path); err != nil {
				return err
			}
		}
		if err = removeRegular(root, pathTemp(e.Path, p.ID, i)); err != nil {
			return err
		}
		if fault != nil {
			fault(fmt.Sprintf("restore:%d", i))
		}
	}
	// Prove the entire prior file generation before clearing the pending marker.
	for _, e := range j.Entries {
		if e.Existed {
			if err = verify(root, e.Path, e.Size, e.SHA256); err != nil {
				return err
			}
		} else {
			f, err := regular(root, e.Path)
			if err == nil {
				f.Close()
				return fmt.Errorf("recovery left new file %s", e.Path)
			}
			if !errors.Is(err, os.ErrNotExist) {
				return err
			}
		}
	}
	return removeRegular(root, ".nightcap/pending.json")
}
func pathTemp(name, id string, index int) string {
	parent := path.Dir(name)
	if parent == "." {
		return temporary(id, index)
	}
	return parent + "/" + temporary(id, index)
}

// Keep JSON helpers here so journal layout remains explicit and canonical.
func encode(value any) ([]byte, error) { return json.Marshal(value) }

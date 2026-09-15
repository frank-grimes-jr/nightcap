// Package installer applies and recovers one complete signed asset generation.
// Installed asset evidence never grants Play without the remaining runtime gates.
package installer

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/installguard"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

type Result struct {
	Release        uint64
	ManifestDigest string
	ReadyToPlay    bool
}
type activeRecord struct {
	Release        uint64
	ManifestDigest string
	Manifest       []byte
	Signature      manifest.Signature
}

var errInterrupted = errors.New("simulated process interruption")
var ErrRecoveryRequired = errors.New("unfinished client update requires recovery")

// Install requires caller-owned trust and revalidates staged content under the
// exclusive Windows executable guard. No binary executable writes are performed.
func Install(ctx context.Context, clientDir, candidateDir string, trust manifest.Trust) (Result, error) {
	stage, err := os.OpenRoot(candidateDir)
	if err != nil {
		return Result{}, err
	}
	defer stage.Close()
	raw, err := readBounded(stage, "manifest.json", manifest.MaxManifestBytes)
	if err != nil {
		return Result{}, err
	}
	signature, err := readBounded(stage, "signature.json", 4096)
	if err != nil {
		return Result{}, err
	}
	var sig manifest.Signature
	if err = decode(signature, &sig); err != nil {
		return Result{}, err
	}
	m, err := manifest.Verify(raw, sig, trust)
	if err != nil {
		return Result{}, err
	}
	config, metadata, err := patchAssets(stage, m)
	if err != nil {
		return Result{}, err
	}
	guard, err := installguard.Acquire(clientDir)
	if err != nil {
		return Result{}, err
	}
	defer guard.Close()
	_, err = preflight.CheckOpen(guard.Executable(), config, metadata)
	if err != nil {
		return Result{}, err
	}
	return installLocked(ctx, guard.Root(), stage, raw, sig, trust, nil)
}

// Recover runs without network or a candidate. The trusted inventory/retired set
// bounds every recovery destination. A corrupt journal/backup blocks recovery.
func Recover(clientDir string, trust manifest.Trust) error {
	guard, err := installguard.Acquire(clientDir)
	if err != nil {
		return err
	}
	defer guard.Close()
	report, err := client.InspectOpen(guard.Executable())
	if err != nil {
		return err
	}
	if !report.Supported {
		return fmt.Errorf("unsupported client executable")
	}
	return recoverLocked(guard.Root(), trust)
}
func installLocked(ctx context.Context, root, stage *os.Root, raw []byte, sig manifest.Signature, trust manifest.Trust, fault func(string) error) (result Result, err error) {
	if _, e := readPending(root); e == nil {
		return Result{}, ErrRecoveryRequired
	} else if !errors.Is(e, os.ErrNotExist) {
		return Result{}, e
	}
	// The local active record is a durable monotonic checkpoint under the same
	// user-owned state boundary as Trust.HighestRelease. Corruption fails closed.
	if b, e := readBounded(root, ".nightcap/active.json", maxStateBytes); e == nil {
		var old activeRecord
		if e = decode(b, &old); e != nil {
			return Result{}, e
		}
		var oldManifest manifest.Manifest
		if json.Unmarshal(old.Manifest, &oldManifest) != nil || oldManifest.Release != old.Release || old.Release == 0 || manifest.Digest(old.Manifest) != old.ManifestDigest {
			return Result{}, fmt.Errorf("invalid active checkpoint")
		}
		if old.Release > trust.HighestRelease {
			trust.HighestRelease = old.Release
			trust.HighestDigest = old.ManifestDigest
		} else if old.Release == trust.HighestRelease && trust.HighestDigest != old.ManifestDigest {
			return Result{}, fmt.Errorf("active checkpoint conflicts with trusted release")
		}
	} else if !errors.Is(e, os.ErrNotExist) {
		return Result{}, e
	}
	m, err := manifest.Verify(raw, sig, trust)
	if err != nil {
		return Result{}, err
	}
	if err = verifyStage(ctx, stage, m); err != nil {
		return Result{}, err
	}
	idBytes := make([]byte, 16)
	if _, err = rand.Read(idBytes); err != nil {
		return Result{}, err
	}
	id := hex.EncodeToString(idBytes)
	paths := make([]string, 0, len(m.Files)+len(m.Tombstones)+1)
	for _, f := range m.Files {
		paths = append(paths, f.Path)
	}
	paths = append(paths, m.Tombstones...)
	paths = append(paths, ".nightcap/active.json")
	j, err := snapshot(root, id, paths)
	if err != nil {
		return Result{}, err
	}
	journalBytes, err := encode(j)
	if err != nil {
		return Result{}, err
	}
	if err = newBlob(root, txPath(id)+"/journal.json", journalBytes); err != nil {
		return Result{}, err
	}
	pendingBytes, err := encode(pendingRecord{ID: id, SHA256: manifest.Digest(journalBytes)})
	if err != nil {
		return Result{}, err
	}
	if err = replaceBlob(root, ".nightcap/pending.json", pendingBytes, id, -1); err != nil {
		return Result{}, err
	}
	committed := false
	defer func() {
		if !committed && !errors.Is(err, errInterrupted) {
			rollbackErr := recoverLocked(root, trust)
			if rollbackErr != nil {
				err = errors.Join(err, fmt.Errorf("rollback requires recovery: %w", rollbackErr))
			}
			result = Result{}
		}
	}()
	step := func(name string) error {
		if err := ctx.Err(); err != nil {
			return err
		}
		if fault != nil {
			return fault(name)
		}
		return nil
	}
	if err = step("pending"); err != nil {
		return Result{}, err
	}
	for i, f := range m.Files {
		in, e := regular(stage, "files/"+f.Path)
		if e != nil {
			return Result{}, e
		}
		e = replace(root, f.Path, in, f.Size, f.SHA256, id, i)
		e = errors.Join(e, in.Close())
		if e != nil {
			return Result{}, e
		}
		if err = step(fmt.Sprintf("replace:%d", i)); err != nil {
			return Result{}, err
		}
	}
	for i, name := range m.Tombstones {
		if err = removeRegular(root, name); err != nil {
			return Result{}, err
		}
		if err = step(fmt.Sprintf("remove:%d", len(m.Files)+i)); err != nil {
			return Result{}, err
		}
	}
	for _, f := range m.Files {
		if err = verify(root, f.Path, f.Size, f.SHA256); err != nil {
			return Result{}, err
		}
	}
	active, err := encode(activeRecord{Release: m.Release, ManifestDigest: manifest.Digest(raw), Manifest: raw, Signature: sig})
	if err != nil {
		return Result{}, err
	}
	if err = replaceBlob(root, ".nightcap/active.json", active, id, len(paths)-1); err != nil {
		return Result{}, err
	}
	if err = step("active"); err != nil {
		return Result{}, err
	}
	if err = removeRegular(root, ".nightcap/pending.json"); err != nil {
		return Result{}, err
	}
	committed = true
	return Result{Release: m.Release, ManifestDigest: manifest.Digest(raw)}, nil
}

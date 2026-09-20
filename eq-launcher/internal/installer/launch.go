package installer

import (
	"context"
	"fmt"
	"io"

	"nightcap/eq-launcher/internal/launchlock"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

const HelperPath = "nightcap-bootstrap.exe"

// LaunchLease owns a verified local generation. It is not runtime approval:
// the bootstrap still must initialize the owned child and obtain matching
// health before releasing its entrypoint.
// Keep this single-owner lease alive for the entire game session.
type LaunchLease struct {
	locks        *launchlock.Set
	files        map[string]launchlock.File
	release      uint64
	digest       string
	configDigest string
	bootstrap    preflight.BootstrapMetadata
	runtime      preflight.RuntimePolicy
}

func (l *LaunchLease) Close() error                           { return l.locks.Close() }
func (l *LaunchLease) Directory() string                      { return l.locks.Directory() }
func (l *LaunchLease) Release() uint64                        { return l.release }
func (l *LaunchLease) ManifestDigest() string                 { return l.digest }
func (l *LaunchLease) ConfigDigest() string                   { return l.configDigest }
func (l *LaunchLease) Executable() launchlock.File            { return l.files["eqgame.exe"] }
func (l *LaunchLease) Proxy() launchlock.File                 { return l.files["dinput8.dll"] }
func (l *LaunchLease) Helper() launchlock.File                { return l.files[HelperPath] }
func (l *LaunchLease) Bootstrap() preflight.BootstrapMetadata { return l.bootstrap }
func (l *LaunchLease) Runtime() preflight.RuntimePolicy       { return l.runtime }

// PrepareLaunch performs no network requests or writes. Trust must come from
// compiled launcher policy and its trusted release floor, never the UI. All
// verification reads use handles retained in the returned lease. On any error
// every handle is released and no process is created.
func PrepareLaunch(ctx context.Context, directory string, trust manifest.Trust) (*LaunchLease, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	locks, err := launchlock.Acquire(directory)
	if err != nil {
		return nil, err
	}
	keep := false
	defer func() {
		if !keep {
			locks.Close()
		}
	}()
	lease, m, err := verifyLaunchGeneration(ctx, locks, trust)
	if err != nil {
		return nil, err
	}
	config, catalog, err := requiredPatchAssets(m, func(name string, limit int64) ([]byte, error) {
		return readLocked(lease.files[name], limit)
	})
	if err != nil {
		return nil, err
	}
	requiredProxy, requiredHelper := false, false
	for _, entry := range m.Files {
		if entry.Path == HelperPath && entry.Required {
			requiredHelper = true
		}
		if entry.Path == "dinput8.dll" && entry.Required {
			requiredProxy = true
		}
	}
	if !requiredProxy {
		return nil, fmt.Errorf("missing required proxy")
	}
	if !requiredHelper {
		return nil, fmt.Errorf("missing required bootstrap helper")
	}
	check := preflight.CheckOpen
	if trust.ReleaseInventory {
		check = preflight.CheckSignedOpen
	}
	if _, err = check(lease.Executable(), config, catalog); err != nil {
		return nil, err
	}
	lease.runtime, err = preflight.RuntimeForCatalog(catalog)
	if err != nil {
		return nil, err
	}
	lease.bootstrap, err = preflight.BootstrapOpen(lease.Executable(), lease.Proxy())
	if err != nil {
		return nil, err
	}
	if err = preflight.CheckHelperOpen(lease.Helper()); err != nil {
		return nil, err
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	// The executable lock excludes our installer for the whole preparation. Repeat
	// absent checks after verification to catch pre-existing or externally added
	// pending work/retired content; these are not locks on nonexistent files.
	if err = launchAbsences(locks, m); err != nil {
		return nil, err
	}
	lease.configDigest = manifest.Digest(config)
	keep = true
	return lease, nil
}

func verifyLaunchGeneration(ctx context.Context, locks *launchlock.Set, trust manifest.Trust) (*LaunchLease, manifest.Manifest, error) {
	var m manifest.Manifest
	if err := locks.Absent(".nightcap/pending.json"); err != nil {
		return nil, m, fmt.Errorf("%w: %v", ErrRecoveryRequired, err)
	}
	checkpoint, err := locks.Open(".nightcap/active.json")
	if err != nil {
		return nil, m, err
	}
	data, err := readLocked(checkpoint, maxStateBytes)
	if err != nil {
		return nil, m, err
	}
	a, err := decodeActive(data)
	if err != nil {
		return nil, m, err
	}
	if a.Release > trust.HighestRelease {
		trust.HighestRelease = a.Release
		trust.HighestDigest = a.ManifestDigest
	}
	m, err = manifest.Verify(a.Manifest, a.Signature, trust)
	if err != nil {
		return nil, m, err
	}
	lease := &LaunchLease{locks: locks, files: make(map[string]launchlock.File), release: a.Release, digest: a.ManifestDigest}
	lease.files["eqgame.exe"], err = locks.Open("eqgame.exe")
	if err != nil {
		return nil, m, err
	}
	for _, entry := range m.Files {
		if err := ctx.Err(); err != nil {
			return nil, m, err
		}
		f, err := locks.Open(entry.Path)
		if err != nil {
			return nil, m, err
		}
		got, err := copyHash(io.Discard, contextReader{ctx, io.NewSectionReader(f, 0, entry.Size+1)}, entry.Size)
		if err != nil {
			return nil, m, fmt.Errorf("verify %s: %w", entry.Path, err)
		}
		if got != entry.SHA256 {
			return nil, m, fmt.Errorf("hash mismatch: %s", entry.Path)
		}
		lease.files[entry.Path] = f
	}
	if err := launchAbsences(locks, m); err != nil {
		return nil, m, err
	}
	return lease, m, nil
}
func launchAbsences(locks *launchlock.Set, m manifest.Manifest) error {
	if err := locks.Absent(".nightcap/pending.json"); err != nil {
		return fmt.Errorf("%w: %v", ErrRecoveryRequired, err)
	}
	for _, name := range m.Tombstones {
		if err := locks.Absent(name); err != nil {
			return err
		}
	}
	return nil
}
func readLocked(f launchlock.File, limit int64) ([]byte, error) {
	if f == nil {
		return nil, fmt.Errorf("missing locked file")
	}
	data, err := io.ReadAll(io.NewSectionReader(f, 0, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("oversized locked file")
	}
	return data, nil
}

type contextReader struct {
	ctx    context.Context
	reader io.Reader
}

func (r contextReader) Read(p []byte) (int, error) {
	if err := r.ctx.Err(); err != nil {
		return 0, err
	}
	return r.reader.Read(p)
}

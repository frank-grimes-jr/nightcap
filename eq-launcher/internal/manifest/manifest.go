// Package manifest verifies release metadata before any client-file mutation.
package manifest

import (
	"bytes"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/url"
	"path"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const (
	MaxManifestBytes       = 1 << 20
	MaxFileBytes     int64 = 256 << 20
	MaxReleaseBytes  int64 = 1 << 30
	MaxFiles               = 1024
)

type File struct {
	Path     string `json:"path"`
	SHA256   string `json:"sha256"`
	Size     int64  `json:"size"`
	URL      string `json:"url"`
	Required bool   `json:"required"`
}
type Manifest struct {
	Schema      int       `json:"schema"`
	Release     uint64    `json:"release"`
	MinLauncher string    `json:"minimum_launcher"`
	Expires     time.Time `json:"expires"`
	Files       []File    `json:"files"`
	Tombstones  []string  `json:"tombstones"`
}
type Signature struct {
	KeyID string
	Bytes []byte
}
type Key struct {
	ID                  string
	Public              ed25519.PublicKey
	NotBefore, NotAfter time.Time
}

// Trust is supplied by the launcher, never by the downloaded manifest. Inventory
// maps exact owned paths to their required flag. Retired lists removable paths.
// HighestRelease/Digest come from the trusted, durable anti-rollback state.
type Trust struct {
	Keys            []Key
	Now             time.Time
	LauncherVersion string
	HighestRelease  uint64
	HighestDigest   string
	Inventory       map[string]bool
	Retired         map[string]bool
	Hosts           []string
}

func Digest(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }

// Canonical encodes this schema in field order, compact UTF-8 with Go JSON string
// escaping and no trailing newline. Publishers sign exactly these returned bytes.
func Canonical(m Manifest) ([]byte, error) { return json.Marshal(m) }

func Verify(raw []byte, signature Signature, trust Trust) (Manifest, error) {
	fail := func(message string) (Manifest, error) { return Manifest{}, fmt.Errorf("manifest: %s", message) }
	if len(raw) == 0 || len(raw) > MaxManifestBytes {
		return fail("invalid manifest size")
	}
	if trust.Now.IsZero() {
		return fail("verification time is required")
	}
	var key *Key
	for i := range trust.Keys {
		if trust.Keys[i].ID == signature.KeyID {
			if key != nil {
				return fail("ambiguous signing key")
			}
			key = &trust.Keys[i]
		}
	}
	if key == nil || len(key.Public) != ed25519.PublicKeySize || len(signature.Bytes) != ed25519.SignatureSize {
		return fail("unknown key or invalid signature length")
	}
	if trust.Now.Before(key.NotBefore) || !trust.Now.Before(key.NotAfter) {
		return fail("signing key is not currently valid")
	}
	if !ed25519.Verify(key.Public, raw, signature.Bytes) {
		return fail("signature verification failed")
	}
	var m Manifest
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&m); err != nil {
		return fail("invalid schema encoding")
	}
	canonical, err := Canonical(m)
	// Exact encoding rejects duplicate/case-aliased fields, trailing JSON and
	// parser-dependent spellings even when the supplied bytes were signed.
	if err != nil || !bytes.Equal(canonical, raw) {
		return fail("noncanonical encoding")
	}
	if m.Schema != 1 || m.Release == 0 {
		return fail("unsupported schema or release")
	}
	if !trust.Now.Before(m.Expires) {
		return fail("release metadata expired")
	}
	minimum, err := version(m.MinLauncher)
	if err != nil {
		return fail("invalid minimum launcher version")
	}
	current, err := version(trust.LauncherVersion)
	if err != nil {
		return fail("invalid local launcher version")
	}
	for i := range minimum {
		if current[i] > minimum[i] {
			break
		}
		if current[i] < minimum[i] {
			return fail("launcher upgrade required")
		}
	}
	if m.Release < trust.HighestRelease {
		return fail("release downgrade requires signed rollback authorization")
	}
	if m.Release == trust.HighestRelease && Digest(raw) != trust.HighestDigest {
		return fail("release identifier reused with different metadata")
	}
	if m.Tombstones == nil || len(m.Files) == 0 || len(m.Files) > MaxFiles || len(m.Files) != len(trust.Inventory) || len(m.Tombstones) > MaxFiles {
		return fail("inventory size mismatch")
	}
	seen := map[string]bool{}
	var total int64
	for _, file := range m.Files {
		if err := ValidatePath(file.Path); err != nil {
			return fail(err.Error())
		}
		required, owned := trust.Inventory[file.Path]
		if !owned || required != file.Required || seen[file.Path] {
			return fail("unknown, duplicate or misclassified asset")
		}
		seen[file.Path] = true
		if file.Size <= 0 || file.Size > MaxFileBytes {
			return fail("invalid asset size")
		}
		total += file.Size
		if total > MaxReleaseBytes {
			return fail("release size limit exceeded")
		}
		if !hashPattern.MatchString(file.SHA256) {
			return fail("invalid SHA256")
		}
		if err := ValidateURL(file.URL, trust.Hosts); err != nil {
			return fail(err.Error())
		}
	}
	for _, name := range m.Tombstones {
		if err := ValidatePath(name); err != nil {
			return fail(err.Error())
		}
		if !trust.Retired[name] || seen[name] {
			return fail("unknown or conflicting tombstone")
		}
		seen[name] = true
	}
	return m, nil
}

var hashPattern = regexp.MustCompile(`^[0-9a-f]{64}$`)
var segmentPattern = regexp.MustCompile(`^[a-z0-9_][a-z0-9_.-]*$`)

// ValidatePath rejects unsafe or protected managed-asset paths.
func ValidatePath(name string) error {
	if len(name) == 0 || len(name) > 200 || name != strings.ToLower(name) || path.Clean(name) != name || strings.HasPrefix(name, "/") {
		return fmt.Errorf("invalid asset path")
	}
	for _, segment := range strings.Split(name, "/") {
		if !segmentPattern.MatchString(segment) || strings.HasSuffix(segment, ".") {
			return fmt.Errorf("unsafe Windows path")
		}
		stem := strings.Split(segment, ".")[0]
		if stem == "con" || stem == "prn" || stem == "aux" || stem == "nul" || stem == "conin$" || stem == "conout$" || ((strings.HasPrefix(stem, "com") || strings.HasPrefix(stem, "lpt")) && len(stem) == 4 && stem[3] >= '0' && stem[3] <= '9') {
			return fmt.Errorf("reserved Windows path")
		}
	}
	// Game executables/user files and updater state can never be managed assets.
	if name == "eqgame.exe" || name == "eqclient.ini" || name == "eqhost.txt" || strings.HasPrefix(name, ".nightcap/") {
		return fmt.Errorf("protected client path")
	}
	return nil
}

// ValidateURL applies the same release host/path policy to initial requests and
// every redirect. Hosts must come from launcher trust, never network metadata.
func ValidateURL(raw string, hosts []string) error {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "https" || u.Opaque != "" || u.User != nil || u.Port() != "" || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || u.RawFragment != "" || u.RawPath != "" || u.Host != u.Hostname() || u.Host != strings.ToLower(u.Host) || u.Path == "" || path.Clean(u.Path) != u.Path || strings.ContainsAny(u.Path, "\\%") {
		return fmt.Errorf("invalid release URL")
	}
	for _, host := range hosts {
		if u.Host == host && host != "" {
			return nil
		}
	}
	return fmt.Errorf("release host not allowed")
}
func version(text string) ([3]uint64, error) {
	var value [3]uint64
	parts := strings.Split(text, ".")
	if len(parts) != 3 {
		return value, fmt.Errorf("expected major.minor.patch")
	}
	for i, p := range parts {
		if p == "" || (len(p) > 1 && p[0] == '0') {
			return value, fmt.Errorf("invalid version")
		}
		for _, c := range p {
			if c < '0' || c > '9' {
				return value, fmt.Errorf("invalid version")
			}
		}
		n, err := strconv.ParseUint(p, 10, 32)
		if err != nil {
			return value, err
		}
		value[i] = n
	}
	return value, nil
}

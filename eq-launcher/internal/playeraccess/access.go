// Package playeraccess implements revocable, IP-independent admission credentials.
// Only randomly generated secrets are accepted; these are not user passwords.
package playeraccess

import (
	"bytes"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"regexp"
	"strings"
	"sync/atomic"
	"time"
)

const MaxRegistryBytes = 2 << 20
const MaxCredentials = 10000

var label = regexp.MustCompile(`^[a-z0-9][a-z0-9_-]{0,63}$`)
var ErrRegistry = errors.New("player access registry unavailable or invalid")

type Record struct {
	ID         string `json:"id"`
	Player     string `json:"player"`
	SecretHash string `json:"secret_hash"`
	Created    string `json:"created"`
}
type Registry struct {
	Version     int      `json:"version"`
	Credentials []Record `json:"credentials"`
}

// Generate returns a delivery secret and the safe-to-store registry record.
func Generate(player string) (string, Record, error) {
	if !label.MatchString(player) {
		return "", Record{}, errors.New("invalid player label")
	}
	id, secret := make([]byte, 16), make([]byte, 32)
	if _, err := rand.Read(id); err != nil {
		return "", Record{}, err
	}
	if _, err := rand.Read(secret); err != nil {
		return "", Record{}, err
	}
	token := "nc1." + hex.EncodeToString(id) + "." + base64.RawURLEncoding.EncodeToString(secret)
	hash := sha256.Sum256([]byte(token))
	return token, Record{hex.EncodeToString(id), player, hex.EncodeToString(hash[:]), time.Now().UTC().Format(time.RFC3339)}, nil
}

// ValidToken rejects noncanonical encodings and whitespace before any I/O.
func ValidToken(token string) bool {
	if len(token) != 80 {
		return false
	}
	p := strings.Split(token, ".")
	if len(p) != 3 || p[0] != "nc1" || !validHex(p[1], 16) {
		return false
	}
	b, err := base64.RawURLEncoding.Strict().DecodeString(p[2])
	return err == nil && len(b) == 32 && base64.RawURLEncoding.EncodeToString(b) == p[2]
}
func validHex(s string, size int) bool {
	b, err := hex.DecodeString(s)
	return err == nil && len(b) == size && hex.EncodeToString(b) == s
}

type entry struct {
	player string
	hash   [32]byte
}
type snapshot map[string]entry

// Store has immutable snapshots. Authentication never performs disk I/O, and a
// failed refresh drops authorization instead of preserving revoked/stale access.
type Store struct {
	path    string
	current atomic.Pointer[snapshot]
}

func Open(path string) (*Store, error) {
	s := &Store{path: path}
	if err := s.Refresh(); err != nil {
		return nil, err
	}
	return s, nil
}
func (s *Store) Refresh() error {
	next, err := readRegistry(s.path)
	if err != nil {
		s.current.Store(nil)
		return ErrRegistry
	}
	s.current.Store(&next)
	return nil
}
func (s *Store) Authenticate(token string) (string, bool) {
	if s == nil || !ValidToken(token) {
		return "", false
	}
	state := s.current.Load()
	if state == nil {
		return "", false
	}
	record, ok := (*state)[token[4:36]]
	hash := sha256.Sum256([]byte(token))
	if subtle.ConstantTimeCompare(hash[:], record.hash[:]) != 1 || !ok {
		return "", false
	}
	return record.player, true
}
func readRegistry(path string) (snapshot, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, ErrRegistry
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() > MaxRegistryBytes {
		return nil, ErrRegistry
	}
	b, err := io.ReadAll(io.LimitReader(f, MaxRegistryBytes+1))
	if err != nil || len(b) > MaxRegistryBytes {
		return nil, ErrRegistry
	}
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	var registry Registry
	if d.Decode(&registry) != nil || registry.Version != 1 || len(registry.Credentials) > MaxCredentials {
		return nil, ErrRegistry
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return nil, ErrRegistry
	}
	result := make(snapshot, len(registry.Credentials))
	for _, r := range registry.Credentials {
		if !validHex(r.ID, 16) || !validHex(r.SecretHash, 32) || !label.MatchString(r.Player) {
			return nil, ErrRegistry
		}
		if _, err := time.Parse(time.RFC3339, r.Created); err != nil {
			return nil, ErrRegistry
		}
		if _, exists := result[r.ID]; exists {
			return nil, ErrRegistry
		}
		decoded, _ := hex.DecodeString(r.SecretHash)
		var hash [32]byte
		copy(hash[:], decoded)
		result[r.ID] = entry{r.Player, hash}
	}
	return result, nil
}

// Verify local or hosted release bytes with the public key shipped in launcher 0.3.1.
package main

import (
    "bytes"
    "crypto/ed25519"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "flag"
    "fmt"
    "io"
    "net/http"
    "os"
    "path/filepath"
    "regexp"
    "time"
)

func must(err error) { if err != nil { panic(err) } }
func digest(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }
func main() {
    root := flag.String("root", "", "signed publication directory")
    policy := flag.String("policy", "", "previously shipped public production policy")
    hosted := flag.Bool("hosted", false, "verify public HTTPS bytes")
    flag.Parse()
    trust, err := os.ReadFile(*policy); must(err)
    match := regexp.MustCompile(`hex.DecodeString\("([0-9a-f]{64})"\)`).FindSubmatch(trust)
    if len(match) != 2 { panic("missing shipped public key") }
    public, err := hex.DecodeString(string(match[1])); must(err)
    expected, err := os.ReadFile(filepath.Join(*root, "channel.json")); must(err)
    client := &http.Client{Timeout: 45 * time.Second, CheckRedirect: func(req *http.Request, via []*http.Request) error {
        if req.URL.Scheme != "https" || req.URL.Host != "play.nightcapgame.org" || len(via) > 3 { return fmt.Errorf("unexpected redirect") }; return nil
    }}
    download := func(address string, limit int64) []byte {
        req, err := http.NewRequest("GET", address, nil); must(err)
        req.Header.Set("Accept-Encoding", "identity")
        response, err := client.Do(req); must(err)
        defer response.Body.Close()
        if response.StatusCode != 200 { panic(fmt.Sprintf("HTTP %d: %s", response.StatusCode, address)) }
        raw, err := io.ReadAll(io.LimitReader(response.Body, limit + 1)); must(err)
        if int64(len(raw)) > limit { panic("oversized response") }
        return raw
    }
    raw := expected
    if *hosted { raw = download("https://play.nightcapgame.org/channel.json", 131072) }
    if !bytes.Equal(raw, expected) { panic("public channel differs from signed candidate") }
    var envelope struct { Manifest []byte; Signature struct { KeyID string; Bytes []byte } }
    must(json.Unmarshal(raw, &envelope))
    if envelope.Signature.KeyID != "production-" + digest(public)[:16] || !ed25519.Verify(public, envelope.Manifest, envelope.Signature.Bytes) { panic("invalid production signature") }
    var manifest struct {
        Release uint64
        Expires time.Time
        Files []struct { Path, SHA256, URL string; Size int64; Required bool }
    }
    must(json.Unmarshal(envelope.Manifest, &manifest))
    if manifest.Release != 2026093006 || len(manifest.Files) != 46 || !manifest.Expires.After(time.Now().UTC()) { panic("unexpected release contract") }
    var total int64
    for _, file := range manifest.Files {
        if !filepath.IsLocal(file.Path) || !file.Required || file.Size <= 0 || file.Size > 64*1024*1024 { panic("unsafe asset") }
        expectedURL := fmt.Sprintf("https://play.nightcapgame.org/release/%d/%s", manifest.Release, file.Path)
        if file.URL != expectedURL { panic("unexpected asset URL") }
        var data []byte
        if *hosted { data = download(file.URL, file.Size) } else {
            data, err = os.ReadFile(filepath.Join(*root, "release", fmt.Sprint(manifest.Release), filepath.FromSlash(file.Path))); must(err)
        }
        if int64(len(data)) != file.Size || digest(data) != file.SHA256 { panic("asset mismatch: " + file.Path) }
        total += file.Size
    }
    must(json.NewEncoder(os.Stdout).Encode(map[string]any{"release":manifest.Release,"hosted":*hosted,"verified_files":len(manifest.Files),"total_bytes":total,"expires":manifest.Expires,"channel_sha256":digest(raw),"signature":"valid against shipped production public key"}))
}

package runtimehealth

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"nightcap/eq-launcher/internal/preflight"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestNativeHealthAgreement(t *testing.T) {
	executable := os.Getenv("NIGHTCAP_CPP_HEALTH_TEST")
	if executable == "" {
		t.Skip("set NIGHTCAP_CPP_HEALTH_TEST to the compiled runtime-health.exe")
	}
	dir := t.TempDir()
	cmd := exec.Command(executable, dir+string(os.PathSeparator))
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	pid := uint32(cmd.Process.Pid)
	if err := cmd.Wait(); err != nil {
		t.Fatalf("%v: %s", err, out.String())
	}
	digest := sha256.Sum256([]byte("fixture"))
	policy, err := preflight.RuntimeRequirements()
	if err != nil {
		t.Fatal(err)
	}
	expected := Expected{Runtime: policy, PID: pid, ProcessCreated: 123456789, Nonce: strings.Repeat("0123456789abcdef", 2), ConfigSHA256: hex.EncodeToString(digest[:])}
	raw := bytes.TrimSpace(out.Bytes())
	if _, err := Validate(raw, expected); err != nil {
		t.Fatal(err)
	}
	files, err := filepath.Glob(filepath.Join(dir, "nightcap_health_*.json"))
	if err != nil || len(files) != 1 {
		t.Fatalf("health files: %v %v", files, err)
	}
	actual, err := os.ReadFile(files[0])
	if err != nil || !bytes.Equal(actual, raw) {
		t.Fatalf("atomic file differs: %v", err)
	}
}

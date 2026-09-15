package preflight

import (
	"bytes"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestNativeConfigurationAgreement(t *testing.T) {
	binary := os.Getenv("NIGHTCAP_CPP_CONFIG_TEST")
	if binary == "" {
		t.Skip("set NIGHTCAP_CPP_CONFIG_TEST to native runtime-config test executable")
	}
	good := configFixture(t)
	cases := [][]byte{good, bytes.ReplaceAll(good, []byte("\n"), []byte("\r\n")), bytes.Replace(good, []byte("mq2_survey=0"), []byte("mq2_survey=1"), 1), nil, bytes.Repeat([]byte("x"), 4097), append([]byte{239, 187, 191}, good...)}
	for i := 0; i < len(good); i++ {
		bad := bytes.Clone(good)
		bad[i] ^= 1
		cases = append(cases, bad)
	}
	path := filepath.Join(t.TempDir(), "config.cfg")
	for i, raw := range cases {
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
		output, err := exec.Command(binary, path).CombinedOutput()
		valid := err == nil
		if err != nil {
			exit, ok := err.(*exec.ExitError)
			if !ok || exit.ExitCode() != 2 {
				t.Fatalf("native parser failed: %v %s", err, output)
			}
		}
		if valid != (ValidateConfig(raw) == nil) {
			t.Fatalf("parser mismatch case %d: %q native=%s", i, raw, output)
		}
	}
}

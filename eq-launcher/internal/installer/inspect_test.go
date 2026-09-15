package installer

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestInspectInstalledGeneration(t *testing.T) {
	for _, mode := range []string{"current", "changed", "missing", "retired", "expired", "pending", "corrupt checkpoint"} {
		t.Run(mode, func(t *testing.T) {
			client, stage, raw, sig, trust := fixture(t)
			if _, err := installLocked(context.Background(), client, stage, raw, sig, trust, nil); err != nil {
				t.Fatal(err)
			}
			switch mode {
			case "changed":
				put(t, client.Name(), "dinput8.dll", "bad dll")
			case "missing":
				if err := os.Remove(filepath.Join(client.Name(), "dinput8.dll")); err != nil {
					t.Fatal(err)
				}
			case "retired":
				put(t, client.Name(), "old.dll", "returned old dll")
			case "expired":
				trust.Now = trust.Now.Add(2 * time.Hour)
			case "pending":
				put(t, client.Name(), ".nightcap/pending.json", "corrupt pending journal")
			case "corrupt checkpoint":
				put(t, client.Name(), ".nightcap/active.json", "{}")
			}
			report, err := Inspect(context.Background(), client.Name(), trust)
			if mode == "pending" {
				if err == nil || !report.RecoveryRequired || report.Current {
					t.Fatalf("pending not blocked: %+v %v", report, err)
				}
				return
			}
			if mode == "corrupt checkpoint" {
				if err == nil || report.Current {
					t.Fatalf("corrupt checkpoint accepted: %+v %v", report, err)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if !report.Present || report.Release != 2 || report.Current != (mode == "current") {
				t.Fatalf("unexpected inspection: %+v", report)
			}
			if mode == "expired" && report.ValidationMessage == "" {
				t.Fatal("expiry reason missing")
			}
			assertBytes(t, client, "eqclient.ini", "user settings")
		})
	}
}
func TestInspectNoInstalledGeneration(t *testing.T) {
	_, _, _, _, trust := fixture(t)
	report, err := Inspect(context.Background(), t.TempDir(), trust)
	if err != nil || report.Present || report.Current || report.RecoveryRequired {
		t.Fatalf("empty client: %+v %v", report, err)
	}
}

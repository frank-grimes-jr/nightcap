package manifest

import (
	"testing"
	"time"
)

func TestReleaseInventoryBounds(t *testing.T) {
	for _, scenario := range []string{"new asset", "legacy rejects", "missing core", "optional core", "user ini", "foreign dll", "foreign exe", "other UI", "unknown text", "tampered"} {
		t.Run(scenario, func(t *testing.T) {
			m, trust, key := fixture(t)
			trust.ReleaseInventory = true
			for _, name := range []string{"nightcap-bootstrap.exe", "nightcap-patches.cfg", "nightcap-patch-sites.json", "gfaydark.s3d"} {
				f := m.Files[0]
				f.Path = name
				m.Files = append(m.Files, f)
			}
			switch scenario {
			case "legacy rejects":
				trust.ReleaseInventory = false
			case "missing core":
				m.Files = m.Files[1:]
			case "optional core":
				m.Files[0].Required = false
			case "user ini":
				m.Files[4].Path = "ui_monktest.ini"
			case "foreign dll":
				m.Files[4].Path = "other.dll"
			case "foreign exe":
				m.Files[4].Path = "nightcap-desktop.exe"
			case "other UI":
				m.Files[4].Path = "uifiles/default/equi_inventory.xml"
			case "unknown text":
				m.Files[4].Path = "account.txt"
			}
			raw, sig := signed(t, m, key)
			if scenario == "tampered" {
				raw[len(raw)-1] ^= 1
			}
			_, err := Verify(raw, sig, trust)
			if (err == nil) != (scenario == "new asset") {
				t.Fatalf("accepted=%v: %v", err == nil, err)
			}
		})
	}
}

func TestRecoveryAuthenticatesExpiredCandidateWithoutAuthorizingInstall(t *testing.T) {
	m, trust, key := fixture(t)
	raw, sig := signed(t, m, key)
	trust.Now = trust.Now.Add(365 * 24 * time.Hour)
	trust.HighestRelease = 999
	if _, err := Verify(raw, sig, trust); err == nil {
		t.Fatal("expired install authorized")
	}
	if _, err := VerifyRecovery(raw, sig, trust); err != nil {
		t.Fatal(err)
	}
	raw[len(raw)-1] ^= 1
	if _, err := VerifyRecovery(raw, sig, trust); err == nil {
		t.Fatal("tampered recovery authorized")
	}
}

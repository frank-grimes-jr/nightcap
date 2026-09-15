package runtimehealth

import (
	"encoding/json"
	"nightcap/eq-launcher/internal/preflight"
	"strings"
	"testing"
)

func fixture(t *testing.T) (Record, Expected) {
	p, err := preflight.RuntimeRequirements()
	if err != nil {
		t.Fatal(err)
	}
	e := Expected{PID: 123, ProcessCreated: 456, Nonce: strings.Repeat("a", 32), ConfigSHA256: strings.Repeat("b", 64)}
	r := Record{Schema: p.Schema, ProxyVersion: p.ProxyVersion, CatalogSHA256: p.CatalogSHA256, ConfigSHA256: e.ConfigSHA256, PID: e.PID, ProcessCreated: e.ProcessCreated, Nonce: e.Nonce, State: "ready", RequiredMask: p.RequiredMask, EnabledMask: p.RequiredMask, AppliedMask: p.RequiredMask}
	return r, e
}
func TestExactLaunchHealth(t *testing.T) {
	r, e := fixture(t)
	raw, _ := json.Marshal(r)
	if _, err := Validate(raw, e); err != nil {
		t.Fatal(err)
	}
}
func TestRejectStaleIncompleteOrForeignHealth(t *testing.T) {
	for _, mode := range []string{"pid", "created", "nonce", "standalone", "config", "catalog", "version", "schema", "initializing", "failed", "reason", "required", "enabled", "applied", "extra bits"} {
		t.Run(mode, func(t *testing.T) {
			r, e := fixture(t)
			switch mode {
			case "pid":
				r.PID++
			case "created":
				r.ProcessCreated++
			case "nonce":
				r.Nonce = strings.Repeat("c", 32)
			case "standalone":
				r.Nonce = ""
			case "config":
				r.ConfigSHA256 = strings.Repeat("c", 64)
			case "catalog":
				r.CatalogSHA256 = strings.Repeat("c", 64)
			case "version":
				r.ProxyVersion = "other"
			case "schema":
				r.Schema++
			case "initializing":
				r.State = "initializing"
			case "failed":
				r.State = "failed"
			case "reason":
				r.Reason = "equipment"
			case "required":
				r.RequiredMask = 0
			case "enabled":
				r.EnabledMask = 0
			case "applied":
				r.AppliedMask = 0
			case "extra bits":
				r.AppliedMask |= 1 << 31
			}
			raw, _ := json.Marshal(r)
			if _, err := Validate(raw, e); err == nil {
				t.Fatal("invalid report accepted")
			}
		})
	}
	r, e := fixture(t)
	for bit := uint32(1); bit <= r.RequiredMask; bit <<= 1 {
		copy := r
		copy.AppliedMask &^= bit
		raw, _ := json.Marshal(copy)
		if _, err := Validate(raw, e); err == nil {
			t.Fatalf("missing patch bit %x accepted", bit)
		}
	}
}
func TestHealthEncodingAndExpectedIdentity(t *testing.T) {
	r, e := fixture(t)
	raw, _ := json.Marshal(r)
	for _, bad := range [][]byte{nil, []byte(strings.Repeat("x", MaxBytes+1)), append(append([]byte{}, raw...), raw...), append(append([]byte{}, raw...), '\n'), []byte(strings.Replace(string(raw), `"pid":123`, `"pid":123,"pid":123`, 1)), []byte(strings.Replace(string(raw), `"reason":""`, `"reason":"","extra":true`, 1))} {
		if _, err := Validate(bad, e); err == nil {
			t.Fatal("bad encoding accepted")
		}
	}
	for _, mode := range []string{"pid", "time", "nonce", "config"} {
		bad := e
		switch mode {
		case "pid":
			bad.PID = 0
		case "time":
			bad.ProcessCreated = 0
		case "nonce":
			bad.Nonce = ""
		case "config":
			bad.ConfigSHA256 = ""
		}
		if _, err := Validate(raw, bad); err == nil {
			t.Fatal("untrusted expected identity accepted")
		}
	}
}

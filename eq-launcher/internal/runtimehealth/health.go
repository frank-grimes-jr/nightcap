// Package runtimehealth validates the proxy's process-bound activation report.
// Report validation alone never authorizes Play or proves full client parity.
package runtimehealth

import (
	"bytes"
	"encoding/json"
	"fmt"
	"nightcap/eq-launcher/internal/preflight"
)

const MaxBytes = 4096

type Record struct {
	Schema         uint32 `json:"schema"`
	ProxyVersion   string `json:"proxy_version"`
	CatalogSHA256  string `json:"catalog_sha256"`
	ConfigSHA256   string `json:"config_sha256"`
	PID            uint32 `json:"pid"`
	ProcessCreated uint64 `json:"process_created,string"`
	Nonce          string `json:"nonce"`
	State          string `json:"state"`
	RequiredMask   uint32 `json:"required_mask"`
	EnabledMask    uint32 `json:"enabled_mask"`
	AppliedMask    uint32 `json:"applied_mask"`
	MQ2Survey      bool   `json:"mq2_survey"`
	Reason         string `json:"reason"`
}

// Expected comes from the actual launched process handle, cryptographic launch
// nonce and verified active manifest, never from the record being validated.
type Expected struct {
	PID            uint32
	ProcessCreated uint64
	Nonce          string
	ConfigSHA256   string
}

func lowerHex(value string, size int) bool {
	if len(value) != size {
		return false
	}
	for _, c := range value {
		if !(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}
func Validate(raw []byte, expected Expected) (Record, error) {
	var record Record
	if expected.PID == 0 || expected.ProcessCreated == 0 || !lowerHex(expected.Nonce, 32) || !lowerHex(expected.ConfigSHA256, 64) {
		return record, fmt.Errorf("invalid trusted launch identity")
	}
	if len(raw) == 0 || len(raw) > MaxBytes {
		return record, fmt.Errorf("runtime health size invalid")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&record); err != nil {
		return record, fmt.Errorf("invalid runtime health: %w", err)
	}
	canonical, err := json.Marshal(record)
	if err != nil || !bytes.Equal(canonical, raw) {
		return record, fmt.Errorf("noncanonical runtime health")
	}
	policy, err := preflight.RuntimeRequirements()
	if err != nil {
		return record, err
	}
	if record.Schema != policy.Schema || record.ProxyVersion != policy.ProxyVersion || record.CatalogSHA256 != policy.CatalogSHA256 {
		return record, fmt.Errorf("runtime health contract mismatch")
	}
	if record.PID != expected.PID || record.ProcessCreated != expected.ProcessCreated || record.Nonce != expected.Nonce || record.ConfigSHA256 != expected.ConfigSHA256 {
		return record, fmt.Errorf("runtime health launch identity mismatch")
	}
	if record.State != "ready" || record.Reason != "" {
		return record, fmt.Errorf("required runtime initialization is not ready")
	}
	if record.RequiredMask != policy.RequiredMask || record.EnabledMask != policy.RequiredMask || record.AppliedMask != policy.RequiredMask {
		return record, fmt.Errorf("required runtime patches incomplete or unknown")
	}
	return record, nil
}

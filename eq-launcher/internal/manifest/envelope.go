package manifest

import (
	"bytes"
	"encoding/json"
	"fmt"
)

// Envelope keeps a channel's exact signed bytes and signature in one HTTP object.
// Base64 avoids reserializing the signed manifest while decoding its container.
type Envelope struct {
	Manifest  []byte    `json:"manifest"`
	Signature Signature `json:"signature"`
}

const MaxEnvelopeBytes = 2 * MaxManifestBytes

func DecodeEnvelope(raw []byte) ([]byte, Signature, error) {
	var e Envelope
	if len(raw) == 0 || len(raw) > MaxEnvelopeBytes {
		return nil, e.Signature, fmt.Errorf("invalid envelope size")
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&e); err != nil {
		return nil, e.Signature, err
	}
	canonical, err := json.Marshal(e)
	if err != nil || !bytes.Equal(canonical, raw) || len(e.Manifest) == 0 || len(e.Manifest) > MaxManifestBytes {
		return nil, e.Signature, fmt.Errorf("noncanonical release envelope")
	}
	return e.Manifest, e.Signature, nil
}

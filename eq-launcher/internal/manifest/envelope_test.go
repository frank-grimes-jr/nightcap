package manifest

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestEnvelopePreservesSignedBytesAndRejectsAmbiguity(t *testing.T) {
	e := Envelope{Manifest: []byte(`{"schema":1,"escaped":"\u003c"}`), Signature: Signature{KeyID: "test", Bytes: []byte{1, 2, 3}}}
	raw, _ := json.Marshal(e)
	got, sig, err := DecodeEnvelope(raw)
	if err != nil || !bytes.Equal(got, e.Manifest) || sig.KeyID != "test" {
		t.Fatal("lost signed bytes", err)
	}
	for _, bad := range [][]byte{append(append([]byte{}, raw...), '\n'), []byte(`{"manifest":"","signature":{}}`), append(append([]byte{}, raw...), raw...), bytes.Repeat([]byte("x"), MaxEnvelopeBytes+1)} {
		if _, _, err = DecodeEnvelope(bad); err == nil {
			t.Fatal("ambiguous envelope accepted")
		}
	}
}

package launcher

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"nightcap/eq-launcher/internal/playeraccess"
)

func TestAccessCredentialIsPrivatePersistentAndSerialized(t *testing.T) {
	c, _ := playFixture(t)
	c.policy.RelayURL = "https://relay.test/connect"
	c.state.AccessRequired = true
	c.locallyCurrent = true
	if c.Snapshot().CanPlay {
		t.Fatal("Play offered without credential")
	}
	phase := c.Snapshot().Phase
	token, _, _ := playeraccess.Generate("joe")
	if err := c.SetAccessCode(context.Background(), "  "+token+"\r\n"); err != nil {
		t.Fatal(err)
	}
	if !c.Snapshot().AccessSaved || !c.Snapshot().CanPlay {
		t.Fatal("saved code not reflected in eligibility")
	}
	if c.Snapshot().Phase != phase {
		t.Fatal("credential save changed update/recovery state")
	}
	b, _ := json.Marshal(c.Snapshot())
	if strings.Contains(string(b), token) {
		t.Fatal("secret in UI status/events")
	}
	reopened, err := New(c.home, c.policy)
	if err != nil || !reopened.Snapshot().AccessSaved {
		t.Fatal("credential did not survive restart", err)
	}
	c.state.Busy = true
	if err := c.SetAccessCode(context.Background(), token); !errors.Is(err, ErrBusy) {
		t.Fatal("changed during play")
	}
	if err := c.ForgetAccessCode(context.Background()); !errors.Is(err, ErrBusy) {
		t.Fatal("forgot during play")
	}
	c.state.Busy = false
	if err := c.ForgetAccessCode(context.Background()); err != nil {
		t.Fatal(err)
	}
	if c.Snapshot().AccessSaved || c.Snapshot().CanPlay {
		t.Fatal("forgotten code still enables Play")
	}
	if err := c.Play(context.Background()); !errors.Is(err, playeraccess.ErrCodeRequired) {
		t.Fatal("Play did not require code before network or native launch", err)
	}
}

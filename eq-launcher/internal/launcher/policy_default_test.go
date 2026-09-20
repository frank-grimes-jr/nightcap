//go:build !qacandidate && !production

package launcher

import "testing"

func TestDevelopmentPolicyHasNoReleaseAuthority(t *testing.T) {
	p := DefaultPolicy()
	if p.configured() || p.playConfigured() || p.EnablePlay || p.Bundle != nil || len(p.Trust.Keys) != 0 {
		t.Fatal("development build unexpectedly authorized")
	}
}

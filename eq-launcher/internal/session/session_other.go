//go:build !windows

package session

import (
	"context"
	"fmt"
	"nightcap/eq-launcher/internal/manifest"
)

func Start(context.Context, string, manifest.Trust) (*Session, error) {
	return nil, fmt.Errorf("client sessions require Windows")
}

func StartPrivate(ctx context.Context, dir string, trust manifest.Trust) (*Session, error) {
	return Start(ctx, dir, trust)
}

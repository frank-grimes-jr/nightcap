//go:build !qacandidate

package launcher

import "nightcap/eq-launcher/internal/manifest"

func DefaultPolicy() Policy {
	return Policy{Label: "Development preview", Trust: manifest.Trust{LauncherVersion: "0.1.0"}}
}

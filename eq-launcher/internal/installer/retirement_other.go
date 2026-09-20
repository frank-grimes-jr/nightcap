//go:build !windows

package installer

import (
	"fmt"
	"os"
)

type retirementLock struct{}

func lockRetirement(root *os.Root, name, expected string) (*retirementLock, error) {
	return nil, fmt.Errorf("pinned retirement requires Windows")
}
func (l *retirementLock) close()        {}
func (l *retirementLock) remove() error { return fmt.Errorf("pinned retirement requires Windows") }

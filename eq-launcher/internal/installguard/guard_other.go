//go:build !windows

package installguard

import "fmt"

func Acquire(string) (*Guard, error) { return nil, fmt.Errorf("client installation requires Windows") }

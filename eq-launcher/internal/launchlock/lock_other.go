//go:build !windows

package launchlock

import "fmt"

func Acquire(string) (*Set, error)       { return nil, fmt.Errorf("launch locks require Windows") }
func (s *Set) Open(string) (File, error) { return nil, fmt.Errorf("launch locks require Windows") }
func (s *Set) Absent(string) error       { return fmt.Errorf("launch locks require Windows") }

func AcquireImage(string, string) (*Set, error) {
	return nil, fmt.Errorf("launch locks require Windows")
}

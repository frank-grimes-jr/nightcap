//go:build !windows

package playeraccess

func protect([]byte) ([]byte, error)   { return nil, ErrSavedCode }
func unprotect([]byte) ([]byte, error) { return nil, ErrSavedCode }

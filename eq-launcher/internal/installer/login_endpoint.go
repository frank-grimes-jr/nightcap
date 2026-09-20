package installer

import (
	"bytes"
	"errors"
	"fmt"
	"os"
)

const privateLogin = "[LoginServer]\r\nHost=127.77.0.1:5998\r\n"
const loginBackup = ".nightcap/eqhost.original"

// PrivateLogin temporarily selects the compiled loopback transport under the
// existing installation lease. The immutable original also permits retry after a
// launcher crash. Neither the UI nor downloaded metadata chooses this endpoint.
func (l *LaunchLease) PrivateLogin() (func() error, error) {
	root, err := os.OpenRoot(l.Directory())
	if err != nil {
		return nil, err
	}
	restore, err := privateLoginAt(root)
	if err != nil {
		root.Close()
		return nil, err
	}
	return func() error { defer root.Close(); return restore() }, nil
}
func privateLoginAt(root *os.Root) (func() error, error) {
	current, err := readBounded(root, "eqhost.txt", 8192)
	if err != nil {
		return nil, fmt.Errorf("cannot prepare private login: %w", err)
	}
	original, err := readBounded(root, loginBackup, 8192)
	if errors.Is(err, os.ErrNotExist) {
		original = current
		// Write and sync the backup before replacing user configuration.
		if err = newBlob(root, loginBackup, original); err != nil {
			return nil, err
		}
	} else if err != nil {
		return nil, err
	} else if !bytes.Equal(current, original) && string(current) != privateLogin {
		return nil, fmt.Errorf("eqhost.txt changed since private-login setup; original preserved in %s", loginBackup)
	}
	if err = replaceBlob(root, "eqhost.txt", []byte(privateLogin), "login", 0); err != nil {
		return nil, err
	}
	return func() error {
		current, err := readBounded(root, "eqhost.txt", 8192)
		if err != nil {
			return err
		}
		if string(current) != privateLogin && !bytes.Equal(current, original) {
			return fmt.Errorf("eqhost.txt was edited during play; original preserved in %s", loginBackup)
		}
		if err = replaceBlob(root, "eqhost.txt", original, "login", 1); err != nil {
			return err
		}
		return removeRegular(root, loginBackup)
	}, nil
}

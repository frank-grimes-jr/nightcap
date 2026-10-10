package playeraccess

import (
	"errors"
	"io"
	"os"
)

var ErrCodeRequired = errors.New("enter your private Nightcap access code before playing")
var ErrSavedCode = errors.New("saved Nightcap access could not be opened; enter your access code again")

const credentialFile = "player-access.bin"

// LoadCredential never returns ciphertext, OS diagnostics or secret bytes in an
// error. os.Root confines file operations to the launcher's user-state directory.
func LoadCredential(home string) (string, error) {
	root, err := os.OpenRoot(home)
	if err != nil {
		return "", ErrSavedCode
	}
	defer root.Close()
	f, err := root.Open(credentialFile)
	if errors.Is(err, os.ErrNotExist) {
		return "", ErrCodeRequired
	}
	if err != nil {
		return "", ErrSavedCode
	}
	defer f.Close()
	b, err := io.ReadAll(io.LimitReader(f, 16385))
	if err != nil || len(b) == 0 || len(b) > 16384 {
		return "", ErrSavedCode
	}
	plain, err := unprotect(b)
	if err != nil || !ValidToken(string(plain)) {
		return "", ErrSavedCode
	}
	return string(plain), nil
}

func SaveCredential(home, token string) error {
	if !ValidToken(token) {
		return errors.New("access code is not valid; paste the complete code from the server owner")
	}
	protected, err := protect([]byte(token))
	if err != nil {
		return errors.New("Windows could not securely save your access code")
	}
	root, err := os.OpenRoot(home)
	if err != nil {
		return ErrSavedCode
	}
	defer root.Close()
	// A separate random temporary prevents overwriting another process's write.
	nameToken, _, err := Generate("temporary")
	if err != nil {
		return ErrSavedCode
	}
	name := ".access-" + nameToken[4:36]
	f, err := root.OpenFile(name, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return ErrSavedCode
	}
	defer root.Remove(name)
	_, err = f.Write(protected)
	if err == nil {
		err = f.Sync()
	}
	err = errors.Join(err, f.Close())
	if err == nil {
		err = root.Rename(name, credentialFile)
	}
	if err != nil {
		return ErrSavedCode
	}
	return nil
}

func ForgetCredential(home string) error {
	root, err := os.OpenRoot(home)
	if err != nil {
		return ErrSavedCode
	}
	defer root.Close()
	err = root.Remove(credentialFile)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return ErrSavedCode
	}
	return nil
}

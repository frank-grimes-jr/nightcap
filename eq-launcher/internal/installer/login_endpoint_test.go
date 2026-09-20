package installer

import (
	"os"
	"testing"
)

func TestPrivateLoginRestoresAndRecoversCrash(t *testing.T) {
	for _, crash := range []bool{false, true} {
		t.Run(map[bool]string{false: "normal", true: "crash"}[crash], func(t *testing.T) {
			dir := t.TempDir()
			root, err := os.OpenRoot(dir)
			if err != nil {
				t.Fatal(err)
			}
			defer root.Close()
			original := "[LoginServer]\nHost=previous.example:5998\n"
			put(t, dir, "eqhost.txt", original)
			restore, err := privateLoginAt(root)
			if err != nil {
				t.Fatal(err)
			}
			assertBytes(t, root, "eqhost.txt", privateLogin)
			if crash {
				restore, err = privateLoginAt(root)
				if err != nil {
					t.Fatal(err)
				}
			}
			if err = restore(); err != nil {
				t.Fatal(err)
			}
			assertBytes(t, root, "eqhost.txt", original)
			assertAbsent(t, root, loginBackup)
		})
	}
}
func TestPrivateLoginPreservesConflictingEdits(t *testing.T) {
	dir := t.TempDir()
	root, _ := os.OpenRoot(dir)
	defer root.Close()
	put(t, dir, "eqhost.txt", "original")
	restore, err := privateLoginAt(root)
	if err != nil {
		t.Fatal(err)
	}
	put(t, dir, "eqhost.txt", "user edit")
	if restore() == nil {
		t.Fatal("conflict overwritten")
	}
	assertBytes(t, root, "eqhost.txt", "user edit")
	if _, err = privateLoginAt(root); err == nil {
		t.Fatal("crash recovery conflict overwritten")
	}
}

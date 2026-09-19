package session

import (
	"context"
	"debug/pe"
	"encoding/binary"
	"errors"
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/launchlock"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
)

// Only test-built fixture images enter the internal seam. The public Start API
// always requires signed inventory plus the compiled supported-game identity.
func fixtureInputs(t *testing.T) launchInputs {
	t.Helper()
	helper := os.Getenv("NIGHTCAP_TEST_HELPER")
	if helper == "" {
		t.Skip("set NIGHTCAP_TEST_HELPER after building helper/native fixtures")
	}
	dir := filepath.Join(t.TempDir(), "client é space")
	if err := os.Mkdir(dir, 0700); err != nil {
		t.Fatal(err)
	}
	files := map[string]string{installer.HelperPath: helper, "eqgame.exe": filepath.Join(filepath.Dir(helper), "tests/helper-fixture/eqgame.exe"), "dinput8.dll": filepath.Join(filepath.Dir(helper), "tests/helper-fixture/dinput8.dll"), preflight.ConfigPath: "../../../eq-client-dll/config/nightcap-patches.cfg"}
	for name, source := range files {
		data, err := os.ReadFile(source)
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, name), data, 0700); err != nil {
			t.Fatal(err)
		}
	}
	locks, err := launchlock.Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	// Setup failures close locally; startPrepared takes ownership on return.
	prepared := false
	defer func() {
		if !prepared {
			locks.Close()
		}
	}()
	exe, err := locks.Open("eqgame.exe")
	if err != nil {
		t.Fatal(err)
	}
	proxy, err := locks.Open("dinput8.dll")
	if err != nil {
		t.Fatal(err)
	}
	helperFile, err := locks.Open(installer.HelperPath)
	if err != nil {
		t.Fatal(err)
	}
	if err := preflight.CheckHelperOpen(helperFile); err != nil {
		t.Fatal(err)
	}
	config, err := os.ReadFile(filepath.Join(dir, preflight.ConfigPath))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := locks.Open(preflight.ConfigPath); err != nil {
		t.Fatal(err)
	}
	ep, err := pe.NewFile(exe)
	if err != nil {
		t.Fatal(err)
	}
	defer ep.Close()
	pp, err := pe.NewFile(proxy)
	if err != nil {
		t.Fatal(err)
	}
	defer pp.Close()
	eh, ph := ep.OptionalHeader.(*pe.OptionalHeader32), pp.OptionalHeader.(*pe.OptionalHeader32)
	readRVA := func(image *pe.File, rva uint32, n int) []byte {
		for _, s := range image.Sections {
			if rva >= s.VirtualAddress && uint64(rva)+uint64(n) <= uint64(s.VirtualAddress)+uint64(s.Size) {
				data, err := s.Data()
				if err != nil {
					t.Fatal(err)
				}
				return data[rva-s.VirtualAddress : rva-s.VirtualAddress+uint32(n)]
			}
		}
		t.Fatal("fixture RVA unmapped")
		return nil
	}
	exports := readRVA(pp, ph.DataDirectory[0].VirtualAddress, 40)
	if binary.LittleEndian.Uint32(exports[20:]) != 1 || binary.LittleEndian.Uint32(exports[24:]) != 1 {
		t.Fatal("fixture must export exactly one initializer")
	}
	initializer := binary.LittleEndian.Uint32(readRVA(pp, binary.LittleEndian.Uint32(exports[28:]), 4))
	metadata := preflight.BootstrapMetadata{EntryRVA: eh.AddressOfEntryPoint, EntryOriginal: readRVA(ep, eh.AddressOfEntryPoint, 1)[0], InitializerRVA: initializer, ProxyImageSize: ph.SizeOfImage}
	prepared = true
	return launchInputs{directory: dir, executable: exe, proxy: proxy, helper: helperFile, metadata: metadata, configDigest: manifest.Digest(config), close: locks.Close, timeout: 2000}
}
func assertUnlocked(t *testing.T, input launchInputs) {
	t.Helper()
	for _, name := range []string{"eqgame.exe", "dinput8.dll", installer.HelperPath, preflight.ConfigPath} {
		if err := os.WriteFile(filepath.Join(input.directory, name), []byte("after cleanup"), 0600); err != nil {
			t.Fatalf("locked after cleanup: %s: %v", name, err)
		}
	}
}
func TestNativeSessionSuccessAndPrivateNonce(t *testing.T) {
	t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", "success")
	t.Setenv("NIGHTCAP_HELPER_HOLD", "0")
	t.Setenv("NIGHTCAP_LAUNCH_NONCE", "parent-value")
	input := fixtureInputs(t)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	s, err := startPrepared(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		cleanup, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := s.Close(cleanup); err != nil {
			t.Error(err)
		}
	})
	outcome, err := s.Wait(ctx)
	if err != nil || outcome.Code != 0 || outcome.Identity != s.Identity() || outcome.Identity.PID == 0 {
		t.Fatalf("%+v %v", outcome, err)
	}
	if _, err := os.Stat(filepath.Join(input.directory, "main-entered")); err != nil {
		t.Fatal(err)
	}
	if os.Getenv("NIGHTCAP_LAUNCH_NONCE") != "parent-value" {
		t.Fatal("parent environment changed")
	}
	assertUnlocked(t, input)
}
func TestNativeSessionRejectsHealthAndInitializer(t *testing.T) {
	for _, mode := range []string{"bad_nonce", "bad_mask", "bad_config", "bad_created", "missing_health", "failed_health", "fail", "hang", "crash"} {
		t.Run(mode, func(t *testing.T) {
			t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", mode)
			t.Setenv("NIGHTCAP_HELPER_HOLD", "0")
			input := fixtureInputs(t)
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			s, err := startPrepared(ctx, input)
			if err == nil || s != nil {
				if s != nil {
					s.Close(ctx)
				}
				t.Fatalf("bad fixture accepted: %v", err)
			}
			if _, err := os.Stat(filepath.Join(input.directory, "main-entered")); !errors.Is(err, os.ErrNotExist) {
				t.Fatal("main ran before valid health", err)
			}
			assertUnlocked(t, input)
		})
	}
}
func TestNativeSessionRetainsLocksAndDetachesStartupContext(t *testing.T) {
	t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", "success")
	t.Setenv("NIGHTCAP_HELPER_HOLD", "1")
	input := fixtureInputs(t)
	ctx, cancel := context.WithCancel(context.Background())
	s, err := startPrepared(ctx, input)
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	closeCtx, closeCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer closeCancel()
	defer s.Close(closeCtx)
	cancel()
	select {
	case <-s.Done():
		t.Fatal("startup cancellation killed established session")
	case <-time.After(100 * time.Millisecond):
	}
	if err := os.WriteFile(filepath.Join(input.directory, "dinput8.dll"), []byte("mutation"), 0600); err == nil {
		t.Fatal("running session assets writable")
	}
	ended := make(chan error, 2)
	go func() { ended <- s.Close(closeCtx) }()
	go func() { ended <- s.Close(closeCtx) }()
	for i := 0; i < 2; i++ {
		if err := <-ended; err != nil {
			t.Fatal(err)
		}
	}
	assertUnlocked(t, input)
}
func TestNativeCancelBeforeChildPIDReleasesOnlyAfterJobEmpty(t *testing.T) {
	t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", "hang")
	t.Setenv("NIGHTCAP_HELPER_HOLD", "1")
	input := fixtureInputs(t)
	// Initializer never reports health, so Go has no client PID. The outer job
	// must still terminate the child and all executable mappings before unlocking.
	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer cancel()
	s, err := startPrepared(ctx, input)
	if s != nil || !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("cancel result: %v", err)
	}
	assertUnlocked(t, input)
}

func TestNativeCleanupReportsPersistentExternalImageLock(t *testing.T) {
	t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", "hang")
	t.Setenv("NIGHTCAP_HELPER_HOLD", "1")
	input := fixtureInputs(t)
	path := filepath.Join(input.directory, "eqgame.exe")
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		t.Fatal(err)
	}
	blocker, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer cancel()
	started := time.Now()
	s, err := startPrepared(ctx, input)
	if s != nil || !errors.Is(err, context.DeadlineExceeded) || !strings.Contains(err.Error(), "remained mapped or write-locked") {
		windows.CloseHandle(blocker)
		t.Fatalf("persistent image lock result: %v", err)
	}
	if elapsed := time.Since(started); elapsed < 5*time.Second || elapsed > 8*time.Second {
		windows.CloseHandle(blocker)
		t.Fatalf("cleanup deadline not bounded near five seconds: %v", elapsed)
	}
	if err := windows.CloseHandle(blocker); err != nil {
		t.Fatal(err)
	}
	assertUnlocked(t, input)
}

// This is an owned test executable, not an existing process or installed game.
func TestUnresponsiveHelperProcess(t *testing.T) {
	if os.Getenv("NIGHTCAP_GO_HELPER_FIXTURE") != "1" {
		return
	}
	time.Sleep(time.Minute)
	os.Exit(0)
}
func TestHelperEOFDoesNotStrandWait(t *testing.T) {
	job, err := createJob()
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(job)
	cmd := exec.Command(os.Args[0], "-test.run=^TestUnresponsiveHelperProcess$")
	cmd.Env = append(os.Environ(), "NIGHTCAP_GO_HELPER_FIXTURE=1")
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer cmd.Process.Kill()
	helper, err := windows.OpenProcess(windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE|windows.SYNCHRONIZE, false, uint32(cmd.Process.Pid))
	if err != nil {
		cmd.Process.Kill()
		cmd.Wait()
		t.Fatal(err)
	}
	defer windows.CloseHandle(helper)
	if err := windows.AssignProcessToJobObject(job, helper); err != nil {
		cmd.Process.Kill()
		cmd.Wait()
		t.Fatal(err)
	}
	o := owner{session: &Session{stop: make(chan struct{})}, cmd: cmd, job: job, helper: helper, readySent: true}
	// Terminal EOF is already consumed. Even without Close, helper exit is bounded.
	err = o.waitHelper(nil, time.Now().Add(50*time.Millisecond))
	if err == nil || !strings.Contains(err.Error(), "did not exit") {
		t.Fatalf("unexpected result: %v", err)
	}
	state, err := windows.WaitForSingleObject(helper, 0)
	if err != nil || state != windows.WAIT_OBJECT_0 {
		t.Fatal("helper still alive", err)
	}
}
func TestProtocolRejectsInvalidInitialSequence(t *testing.T) {
	for _, kind := range []uint32{startedKind, exitedKind} {
		t.Run(fmt.Sprintf("kind_%d", kind), func(t *testing.T) {
			read, output, err := privatePipe(4096)
			if err != nil {
				t.Fatal(err)
			}
			defer read.Close()
			input, write, err := privatePipe(4096)
			if err != nil {
				output.Close()
				t.Fatal(err)
			}
			defer input.Close()
			defer write.Close()
			var frame [messageSize]byte
			binary.LittleEndian.PutUint32(frame[:], wireMagic)
			binary.LittleEndian.PutUint32(frame[4:], kind)
			binary.LittleEndian.PutUint32(frame[8:], 42)
			binary.LittleEndian.PutUint64(frame[16:], 1)
			if _, err := output.Write(frame[:]); err != nil {
				t.Fatal(err)
			}
			output.Close()
			o := owner{session: &Session{stop: make(chan struct{})}, read: read, write: write, startup: context.Background(), deadline: time.Now().Add(time.Second)}
			if _, err := o.exchange([]byte{1}); err == nil || !strings.Contains(err.Error(), "unexpected helper message") {
				t.Fatalf("sequence accepted: %v", err)
			}
		})
	}
}

func TestNativeSessionStopReportsLeaseCloseFailure(t *testing.T) {
	t.Setenv("NIGHTCAP_BOOTSTRAP_TEST", "success")
	t.Setenv("NIGHTCAP_HELPER_HOLD", "1")
	input := fixtureInputs(t)
	closeLease := input.close
	cleanupErr := errors.New("fixture lease release error")
	input.close = func() error { return errors.Join(closeLease(), cleanupErr) }
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	s, err := startPrepared(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	if err := s.Close(ctx); !errors.Is(err, cleanupErr) {
		t.Fatalf("cleanup failure hidden: %v", err)
	}
	assertUnlocked(t, input)
}

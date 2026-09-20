package session

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"

	"golang.org/x/sys/windows"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/launchlock"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/preflight"
	"nightcap/eq-launcher/internal/runtimehealth"
)

// Start prepares and owns the complete signed installation. Its context controls
// startup only; after a successful return use Session.Close to end that session.
// Start may return a completed session if the client exits immediately.
func Start(ctx context.Context, directory string, trust manifest.Trust) (*Session, error) {
	return start(ctx, directory, trust, false)
}

func StartPrivate(ctx context.Context, directory string, trust manifest.Trust) (*Session, error) {
	return start(ctx, directory, trust, true)
}

func start(ctx context.Context, directory string, trust manifest.Trust, private bool) (*Session, error) {
	lease, err := installer.PrepareLaunch(ctx, directory, trust)
	if err != nil {
		return nil, err
	}
	closeLease := lease.Close
	if private {
		restore, e := lease.PrivateLogin()
		if e != nil {
			lease.Close()
			return nil, e
		}
		closeLease = func() error { return errors.Join(restore(), lease.Close()) }
	}
	return startPrepared(ctx, launchInputs{directory: lease.Directory(), executable: lease.Executable(), proxy: lease.Proxy(), helper: lease.Helper(), metadata: lease.Bootstrap(), configDigest: lease.ConfigDigest(), close: closeLease, timeout: 20000})
}

type launchInputs struct {
	directory, configDigest   string
	executable, proxy, helper launchlock.File
	metadata                  preflight.BootstrapMetadata
	close                     func() error
	timeout                   uint32
}

type owner struct {
	session            *Session
	input              launchInputs
	cmd                *exec.Cmd
	write, read        *os.File
	job, helper, child windows.Handle
	nonce              string
	ready              chan error
	readySent          bool
	startup            context.Context
	deadline           time.Time
}

func startPrepared(ctx context.Context, input launchInputs) (result *Session, err error) {
	transferred := false
	defer func() {
		if !transferred {
			err = errors.Join(err, input.close())
		}
	}()
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return nil, err
	}
	var inherited []windows.Handle
	defer func() {
		for _, h := range inherited {
			windows.CloseHandle(h)
		}
	}()
	for _, file := range []launchlock.File{input.executable, input.proxy} {
		h, err := duplicateInherited(windows.Handle(file.Fd()), 0, windows.DUPLICATE_SAME_ACCESS)
		if err != nil {
			return nil, err
		}
		inherited = append(inherited, h)
	}
	parent, err := duplicateInherited(windows.CurrentProcess(), windows.SYNCHRONIZE|windows.PROCESS_QUERY_LIMITED_INFORMATION, 0)
	if err != nil {
		return nil, err
	}
	inherited = append(inherited, parent)
	request, err := encodeRequest(input.directory, [3]uint64{uint64(inherited[0]), uint64(inherited[1]), uint64(parent)}, input.metadata, input.timeout)
	if err != nil {
		return nil, err
	}
	childRead, write, err := privatePipe(65536)
	if err != nil {
		return nil, err
	}
	defer childRead.Close()
	read, childWrite, err := privatePipe(4096)
	if err != nil {
		write.Close()
		return nil, err
	}
	defer childWrite.Close()
	defer func() {
		if !transferred {
			write.Close()
			read.Close()
		}
	}()
	job, err := createJob()
	if err != nil {
		return nil, err
	}
	defer func() {
		if !transferred {
			windows.CloseHandle(job)
		}
	}()
	nonceText := hex.EncodeToString(nonce[:])
	cmd := exec.Command(filepath.Join(input.directory, installer.HelperPath))
	cmd.Dir = input.directory
	cmd.Env = nonceEnvironment(os.Environ(), nonceText)
	cmd.Stdin = childRead
	cmd.Stdout = childWrite
	// No io.Copy goroutine or unbounded diagnostic capture. Native fatal-cleanup
	// diagnostics do not participate in the approval protocol.
	cmd.Stderr = nil
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: windows.CREATE_NO_WINDOW}
	for _, h := range inherited {
		cmd.SysProcAttr.AdditionalInheritedHandles = append(cmd.SysProcAttr.AdditionalInheritedHandles, syscall.Handle(h))
	}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	childRead.Close()
	childWrite.Close()
	// Assign before sending any request: the signed helper cannot create a client
	// yet. This outer job covers even a helper crash before it reports a child PID.
	helper, err := windows.OpenProcess(windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE|windows.SYNCHRONIZE|windows.PROCESS_QUERY_LIMITED_INFORMATION, false, uint32(cmd.Process.Pid))
	if err == nil {
		err = windows.AssignProcessToJobObject(job, helper)
	}
	if err != nil {
		if helper != 0 {
			windows.CloseHandle(helper)
		}
		cmd.Process.Kill()
		cmd.Wait()
		return nil, err
	}
	for _, h := range inherited {
		windows.CloseHandle(h)
	}
	inherited = nil
	s := &Session{stop: make(chan struct{}), done: make(chan struct{})}
	o := &owner{session: s, input: input, cmd: cmd, write: write, read: read, job: job, helper: helper, nonce: nonceText, ready: make(chan error, 1), startup: ctx, deadline: time.Now().Add(time.Duration(input.timeout)*time.Millisecond + 5*time.Second)}
	transferred = true
	go o.run(request)
	if err := <-o.ready; err != nil {
		return nil, err
	}
	return s, nil
}
func (o *owner) interrupted() error {
	select {
	case <-o.session.stop:
		return ErrStopped
	default:
	}
	if !o.readySent {
		if err := o.startup.Err(); err != nil {
			return err
		}
		if time.Now().After(o.deadline) {
			return fmt.Errorf("helper startup deadline exceeded")
		}
	}
	return nil
}
func (o *owner) next(deadline time.Time) (message, error) {
	var raw [messageSize]byte
	position := 0
	for position < len(raw) {
		if err := o.interrupted(); err != nil {
			return message{}, err
		}
		if !deadline.IsZero() && time.Now().After(deadline) {
			return message{}, fmt.Errorf("helper exit deadline exceeded")
		}
		available, err := availableBytes(o.read)
		if err != nil {
			if errors.Is(err, io.EOF) && position != 0 {
				err = io.ErrUnexpectedEOF
			}
			return message{}, err
		}
		if available == 0 {
			time.Sleep(10 * time.Millisecond)
			continue
		}
		n, err := o.read.Read(raw[position : position+min(int(available), len(raw)-position)])
		if err != nil {
			return message{}, err
		}
		if n == 0 {
			return message{}, io.ErrNoProgress
		}
		position += n
	}
	return decodeMessage(raw[:])
}
func (o *owner) approve(m message) error {
	child, err := openChild(m.identity)
	if err != nil {
		return err
	}
	o.child = child
	o.session.identity = m.identity
	data, err := readHealth(o.input.directory, m.identity.PID)
	if err != nil {
		return err
	}
	_, err = runtimehealth.Validate(data, runtimehealth.Expected{PID: m.identity.PID, ProcessCreated: m.identity.Created, Nonce: o.nonce, ConfigSHA256: o.input.configDigest})
	if err != nil {
		return err
	}
	if err = o.interrupted(); err != nil {
		return err
	}
	n, err := o.write.Write([]byte{1, 0, 0, 0})
	if err == nil && n != 4 {
		err = io.ErrShortWrite
	}
	return err
}
func (o *owner) exchange(request []byte) (Exit, error) {
	if err := o.interrupted(); err != nil {
		return Exit{}, err
	}
	if n, err := o.write.Write(request); err != nil {
		return Exit{}, err
	} else if n != len(request) {
		return Exit{}, io.ErrShortWrite
	}
	expected := uint32(healthKind)
	for {
		m, err := o.next(time.Time{})
		if err != nil {
			return Exit{}, fmt.Errorf("helper protocol: %w", err)
		}
		if m.kind == failureKind {
			if o.child != 0 && m.identity != o.session.identity {
				return Exit{}, fmt.Errorf("helper failure identity mismatch")
			}
			return Exit{}, fmt.Errorf("helper failed: %s (code %d)", m.reason, m.code)
		}
		if m.kind != expected {
			return Exit{}, fmt.Errorf("unexpected helper message %d; expected %d", m.kind, expected)
		}
		if expected != healthKind && m.identity != o.session.identity {
			return Exit{}, fmt.Errorf("helper session identity mismatch")
		}
		switch m.kind {
		case healthKind:
			if err = o.approve(m); err != nil {
				return Exit{}, err
			}
			expected = startedKind
		case startedKind:
			if err = o.interrupted(); err != nil {
				return Exit{}, err
			}
			o.readySent = true
			o.ready <- nil
			expected = exitedKind
		case exitedKind:
			if err = childExit(o.child, m.code); err != nil {
				return Exit{}, err
			}
			// Require terminal EOF, not trailing messages or a helper that remains alive.
			if _, err = o.next(time.Now().Add(5 * time.Second)); !errors.Is(err, io.EOF) {
				return Exit{}, fmt.Errorf("invalid helper terminal stream: %v", err)
			}
			return Exit{Identity: m.identity, Code: m.code}, nil
		}
	}
}
func (o *owner) run(request []byte) {
	outcome, err := o.exchange(request)
	if errors.Is(err, ErrStopped) {
		err = ErrStopped
	}
	pipeCloseErr := o.write.Close()
	err = o.waitHelper(err, time.Now().Add(5*time.Second))
	// Never release verified files merely because the helper exited. Job accounting
	// also covers an unreported child and any descendants. A rare unconfirmed cleanup
	// keeps locks held; Close(ctx)/Wait(ctx) can time out without abandoning ownership.
	for {
		empty, queryErr := jobEmpty(o.job)
		if queryErr == nil && empty {
			break
		}
		windows.TerminateJobObject(o.job, 0x4e430004)
		time.Sleep(25 * time.Millisecond)
	}
	if o.child != 0 {
		for {
			state, e := windows.WaitForSingleObject(o.child, 100)
			if e == nil && state == windows.WAIT_OBJECT_0 {
				break
			}
		}
	}
	var childCloseErr error
	if o.child != 0 {
		childCloseErr = windows.CloseHandle(o.child)
	}
	cleanupErr := errors.Join(pipeCloseErr, childCloseErr, windows.CloseHandle(o.helper), windows.CloseHandle(o.job), o.read.Close(), o.input.close())
	if cleanupErr == nil {
		cleanupErr = waitImageWritable(filepath.Join(o.input.directory, "eqgame.exe"), time.Now().Add(5*time.Second))
	}
	if cleanupErr != nil {
		err = errors.Join(err, cleanupErr)
	}
	o.session.exit = outcome
	o.session.err = err
	close(o.session.done)
	if !o.readySent {
		o.ready <- err
	}
}

// Wait is called only once the retained process handle is signaled. A helper
// cannot strand cleanup by closing stdout and then continuing to run.
func (o *owner) waitHelper(cause error, deadline time.Time) error {
	terminated := false
	for {
		state, waitErr := windows.WaitForSingleObject(o.helper, 50)
		if waitErr == nil && state == windows.WAIT_OBJECT_0 {
			break
		}
		if cause == nil {
			cause = o.interrupted()
			if cause == nil && waitErr != nil {
				cause = fmt.Errorf("wait for bootstrap helper: %w", waitErr)
			}
			if cause == nil && time.Now().After(deadline) {
				cause = fmt.Errorf("bootstrap helper did not exit after terminal stream")
			}
		}
		if cause != nil {
			windows.TerminateJobObject(o.job, 0x4e430004)
			o.cmd.Process.Kill()
			terminated = true
		}
	}
	// Sole Wait owner; no os/exec pipe readers can discard protocol bytes.
	if err := o.cmd.Wait(); err != nil {
		var exit *exec.ExitError
		// Our termination calls and native stdin-close watchdog use these codes.
		// Preserve other failures even
		// when the protocol already failed, without treating requested kills as faults.
		expectedKill := errors.As(err, &exit) && ((terminated && (exit.ExitCode() == 0x4e430004 || exit.ExitCode() == 1)) || (cause != nil && exit.ExitCode() == 0x4e430003))
		if !expectedKill {
			cause = errors.Join(cause, fmt.Errorf("bootstrap helper exit: %w", err))
		}
	}
	return cause
}

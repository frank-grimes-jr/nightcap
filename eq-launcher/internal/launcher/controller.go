package launcher

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"nightcap/eq-launcher/internal/assets"
	"nightcap/eq-launcher/internal/client"
	"nightcap/eq-launcher/internal/installer"
	"nightcap/eq-launcher/internal/manifest"
	"nightcap/eq-launcher/internal/session"
)

var ErrBusy = errors.New("another launcher operation is in progress")

type Event struct {
	Time    string `json:"time"`
	Message string `json:"message"`
}
type Status struct {
	ClientDir        string              `json:"client_dir"`
	Phase            string              `json:"phase"`
	Message          string              `json:"message"`
	Supported        bool                `json:"supported"`
	Configured       bool                `json:"configured"`
	Busy             bool                `json:"busy"`
	Release          uint64              `json:"release"`
	InstalledRelease uint64              `json:"installed_release"`
	RecoveryRequired bool                `json:"recovery_required"`
	Files            []assets.FileStatus `json:"files"`
	Remove           []string            `json:"remove"`
	Events           []Event             `json:"events"`
	CanCheck         bool                `json:"can_check"`
	CanUpdate        bool                `json:"can_update"`
	CanRecover       bool                `json:"can_recover"`
	CanPlay          bool                `json:"can_play"`
}
type Controller struct {
	locallyCurrent bool
	start          func(context.Context, string, manifest.Trust) (gameSession, error)
	mu             sync.Mutex
	home           string
	policy         Policy
	state          Status
	cancel         context.CancelFunc
	probe          func(string) (client.Report, error)
	fetch          func(context.Context, Policy) ([]byte, manifest.Signature, error)
	local          func(context.Context, string, manifest.Trust) (installer.Inspection, error)
	diff           func(context.Context, []byte, manifest.Signature, manifest.Trust, string) (assets.Diff, error)
	stage          func(context.Context, []byte, manifest.Signature, manifest.Trust, string, string) (assets.Generation, error)
	install        func(context.Context, string, string, manifest.Trust) (installer.Result, error)
	recover        func(string, manifest.Trust) error
}

func New(home string, p Policy) (*Controller, error) {
	if err := os.MkdirAll(home, 0700); err != nil {
		return nil, err
	}
	s, err := loadSettings(home)
	if err != nil {
		return nil, err
	}
	if p.configured() {
		if err := manifest.ValidateURL(p.ManifestURL, p.Trust.Hosts); err != nil {
			return nil, err
		}
		if err := manifest.ValidateURL(p.SignatureURL, p.Trust.Hosts); err != nil {
			return nil, err
		}
	}
	c := &Controller{home: home, policy: p, state: Status{ClientDir: s.ClientDir, Phase: "choose", Message: "Choose your EverQuest folder to begin.", Configured: p.configured(), Files: []assets.FileStatus{}, Remove: []string{}, Events: []Event{}}, fetch: fetchRelease, local: installer.Inspect, diff: assets.Inspect, stage: assets.Stage, install: installer.Install, recover: installer.Recover}
	c.start = func(ctx context.Context, dir string, trust manifest.Trust) (gameSession, error) {
		return session.Start(ctx, dir, trust)
	}
	c.probe = func(dir string) (client.Report, error) { return client.Inspect(filepath.Join(dir, "eqgame.exe")) }
	return c, nil
}
func (c *Controller) Snapshot() Status {
	c.mu.Lock()
	defer c.mu.Unlock()
	s := c.state
	s.Files = append([]assets.FileStatus{}, s.Files...)
	s.Remove = append([]string{}, s.Remove...)
	s.Events = append([]Event{}, s.Events...)
	s.CanCheck = !s.Busy && s.ClientDir != ""
	s.CanUpdate = !s.Busy && s.Supported && s.Configured && !s.RecoveryRequired && (s.Phase == "update" || s.Phase == "health_pending")
	s.CanRecover = !s.Busy && s.Supported && s.Configured && s.RecoveryRequired
	// Eligibility offers an attempt only; Play revalidates everything under a lease.
	s.CanPlay = !s.Busy && s.Supported && c.locallyCurrent && !s.RecoveryRequired && c.policy.playConfigured()
	return s
}
func (c *Controller) begin(ctx context.Context) (context.Context, string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.state.Busy {
		return nil, "", ErrBusy
	}
	ctx, c.cancel = context.WithCancel(ctx)
	c.state.Busy = true
	return ctx, c.state.ClientDir, nil
}
func (c *Controller) finish(err error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.cancel != nil {
		c.cancel()
		c.cancel = nil
	}
	c.state.Busy = false
	if err != nil {
		c.state.Phase = "error"
		c.state.Message = err.Error()
		if errors.Is(err, context.Canceled) {
			c.state.Message = "Operation cancelled."
		}
		c.eventLocked(c.state.Message)
	}
}
func (c *Controller) eventLocked(message string) {
	c.state.Events = append(c.state.Events, Event{Time: time.Now().Format("15:04:05"), Message: message})
	if len(c.state.Events) > 40 {
		c.state.Events = c.state.Events[len(c.state.Events)-40:]
	}
}
func (c *Controller) show(phase, message string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.state.Phase = phase
	c.state.Message = message
	c.eventLocked(message)
}
func (c *Controller) Cancel() {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.cancel != nil {
		c.cancel()
	}
}
func (c *Controller) SelectClient(ctx context.Context, dir string) (err error) {
	ctx, _, err = c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	if err = ctx.Err(); err != nil {
		return err
	}
	if dir == "" {
		return fmt.Errorf("choose your EverQuest folder first")
	}
	dir, err = filepath.Abs(dir)
	if err != nil {
		return err
	}
	if err = saveSettings(c.home, dir); err != nil {
		return err
	}
	c.mu.Lock()
	c.state.ClientDir = dir
	c.state.Release = 0
	c.state.InstalledRelease = 0
	c.state.RecoveryRequired = false
	c.state.Files = []assets.FileStatus{}
	c.state.Remove = []string{}
	c.state.Supported = false
	c.locallyCurrent = false
	c.mu.Unlock()
	if err = c.inspectExecutable(dir); err != nil {
		return err
	}
	if !c.policy.configured() {
		c.show("preview", "Client recognized. Updates are not available in this preview.")
	} else {
		trust := c.policy.Trust
		trust.Now = time.Now().UTC()
		local, e := c.inspectLocal(ctx, dir, trust)
		if e != nil {
			return e
		}
		if local.RecoveryRequired {
			c.show("recovery", "An interrupted update needs recovery before continuing.")
		} else {
			c.show("selected", "Client recognized. Check for updates or launch your verified installed release.")
		}
	}
	return nil
}
func (c *Controller) inspectExecutable(dir string) error {
	if dir == "" {
		return fmt.Errorf("choose your EverQuest folder first")
	}
	report, err := c.probe(dir)
	c.mu.Lock()
	c.state.Supported = err == nil && report.Supported
	c.mu.Unlock()
	if err != nil {
		return err
	}
	if !report.Supported {
		return fmt.Errorf("this client is not supported; select the RoF2 client folder")
	}
	return nil
}
func (c *Controller) prepare(ctx context.Context, dir string) ([]byte, manifest.Signature, manifest.Trust, error) {
	trust := c.policy.Trust
	trust.Now = time.Now().UTC()
	if err := c.inspectExecutable(dir); err != nil {
		return nil, manifest.Signature{}, trust, err
	}
	if !c.policy.configured() {
		c.show("preview", "Client recognized. Updates are not available in this preview.")
		return nil, manifest.Signature{}, trust, nil
	}
	local, err := c.inspectLocal(ctx, dir, trust)
	if err != nil {
		return nil, manifest.Signature{}, trust, err
	}
	if local.RecoveryRequired {
		c.show("recovery", "An interrupted update needs recovery before continuing.")
		return nil, manifest.Signature{}, trust, nil
	}
	if local.Release > trust.HighestRelease {
		trust.HighestRelease = local.Release
		trust.HighestDigest = local.ManifestDigest
	}
	c.show("checking", "Checking the latest signed release…")
	raw, sig, err := c.fetch(ctx, c.policy)
	if err != nil {
		return nil, sig, trust, err
	}
	trust.Now = time.Now().UTC()
	m, err := manifest.Verify(raw, sig, trust)
	if err != nil {
		return nil, sig, trust, err
	}
	diff, err := c.diff(ctx, raw, sig, trust, dir)
	if err != nil {
		return nil, sig, trust, err
	}
	changes := len(diff.Remove)
	for _, f := range diff.Files {
		if f.State != assets.Current {
			changes++
		}
	}
	c.mu.Lock()
	c.state.Release = m.Release
	c.state.Files = diff.Files
	c.state.Remove = diff.Remove
	c.mu.Unlock()
	if changes > 0 || local.Release != m.Release || !local.Present {
		c.show("update", fmt.Sprintf("Release %d is ready. %d file changes to apply.", m.Release, changes))
	} else {
		c.show("health_pending", "Files match this release. Client compatibility checks are still required before Play.")
	}
	return raw, sig, trust, nil
}
func (c *Controller) Check(ctx context.Context) (err error) {
	ctx, dir, err := c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	_, _, _, err = c.prepare(ctx, dir)
	return err
}
func (c *Controller) Update(ctx context.Context) (err error) {
	ctx, dir, err := c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	raw, sig, trust, err := c.prepare(ctx, dir)
	if err != nil {
		return err
	}
	if len(raw) == 0 {
		return fmt.Errorf("a verified release and complete recovery are required before updating")
	}
	parent := filepath.Join(c.home, "staging")
	if err = os.MkdirAll(parent, 0700); err != nil {
		return err
	}
	c.show("staging", "Preparing and verifying all release files…")
	generation, err := c.stage(ctx, raw, sig, trust, dir, parent)
	if err != nil {
		return err
	}
	if err = ctx.Err(); err != nil {
		return err
	}
	trust.Now = time.Now().UTC()
	c.show("installing", "Installing verified files. Keep the game closed.")
	result, err := c.install(ctx, dir, generation.Directory, trust)
	if err != nil {
		return err
	}
	c.mu.Lock()
	c.state.InstalledRelease = result.Release
	c.locallyCurrent = true
	c.state.RecoveryRequired = false
	for i := range c.state.Files {
		c.state.Files[i].State = assets.Current
	}
	c.state.Remove = []string{}
	c.mu.Unlock()
	c.show("health_pending", "Files installed. Client compatibility checks are still required before Play.")
	return nil
}
func (c *Controller) Recover(ctx context.Context) (err error) {
	ctx, dir, err := c.begin(ctx)
	if err != nil {
		return err
	}
	defer func() { c.finish(err) }()
	if err = ctx.Err(); err != nil {
		return err
	}
	if !c.policy.configured() {
		return fmt.Errorf("recovery is unavailable in this preview")
	}
	if err = c.inspectExecutable(dir); err != nil {
		return err
	}
	trust := c.policy.Trust
	trust.Now = time.Now().UTC()
	c.show("recovering", "Restoring the previous client files…")
	if err = c.recover(dir, trust); err != nil {
		return err
	}
	c.mu.Lock()
	c.state.RecoveryRequired = false
	c.mu.Unlock()
	c.show("selected", "Recovery completed. Check for updates to continue.")
	return nil
}

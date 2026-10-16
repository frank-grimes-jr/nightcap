// Run a copy inside eq-launcher so its internal manifest verifier is used.
package main

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"reflect"
	"time"
	"nightcap/eq-launcher/internal/manifest"
)

func must(err error) { if err != nil { panic(err) } }
func read(path string) []byte { b,e:=os.ReadFile(path);must(e);return b }
func main() {
	previous:=flag.String("previous","","verified baseline envelope")
	notes:=flag.String("notes","","reviewed patch notes")
	key:=flag.String("key","","existing private seed; never uploaded")
	output:=flag.String("output","","exclusive new envelope output")
	hosted:=flag.Bool("hosted",false,"verify published envelope and all existing assets")
	flag.Parse()
	public,e:=hex.DecodeString("4e67e8f79caeb41e26106ade37c7bf0f2a5690b8222e4948e92f781821345266");must(e)
	trust:=manifest.Trust{ReleaseInventory:true,LauncherVersion:"0.6.0",Hosts:[]string{"play.nightcapgame.org"},Now:time.Now().UTC(),
		Keys:[]manifest.Key{{ID:"production-4acb02e67aeb0b51",Public:public,NotBefore:time.Unix(1789862400,0),NotAfter:time.Unix(1853020800,0)}},
		Retired:map[string]bool{"nektulos.eqg":true,"lavastorm.eqg":true},
		RetiredSHA256:map[string]string{"nektulos.eqg":"de487c2820595b753ccdb5c38d87769f396dc345cb5699b8b109b949b01b8885","lavastorm.eqg":"86988d368570e218022c420a4fa4e9d67e258356295d6bb4419a2d5834ef0b3a"}}
	raw,sig,e:=manifest.DecodeEnvelope(read(*previous));must(e)
	old,e:=manifest.Verify(raw,sig,trust);must(e)
	if old.Release!=2026101302 || len(old.Files)!=105 {panic("baseline changed")}
	var history []manifest.PatchNote;must(json.Unmarshal(read(*notes),&history))
	if len(history)!=len(old.PatchNotes)+1 || history[0].Release!=2026101303 || !reflect.DeepEqual(history[1:],old.PatchNotes) {panic("patch history drift")}
	m:=old;m.Release=2026101303;m.PatchNotes=history
	candidate,e:=manifest.Canonical(m);must(e);trust.HighestRelease=old.Release
	if !*hosted {
		seed:=read(*key);if len(seed)!=ed25519.SeedSize {panic("invalid seed length")}
		private:=ed25519.NewKeyFromSeed(seed);if !bytes.Equal(private.Public().(ed25519.PublicKey),public) {panic("wrong production signing key")}
		signature:=manifest.Signature{KeyID:trust.Keys[0].ID,Bytes:ed25519.Sign(private,candidate)}
		_,e=manifest.Verify(candidate,signature,trust);must(e)
		envelope,e:=json.Marshal(manifest.Envelope{Manifest:candidate,Signature:signature});must(e)
		f,e:=os.OpenFile(*output,os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600);must(e);_,e=f.Write(envelope);must(e);must(f.Sync());must(f.Close())
		fmt.Printf("Signed notes-only release %d; preserved %d complete file records and prior history\n",m.Release,len(m.Files));return
	}
	client:=&http.Client{Timeout:45*time.Second,CheckRedirect:func(req *http.Request,via []*http.Request)error {
		if req.URL.Scheme!="https" || req.URL.Host!="play.nightcapgame.org" || len(via)>3 {return fmt.Errorf("unexpected redirect")};return nil}}
	download:=func(url string,limit int64)[]byte {
		req,e:=http.NewRequest("GET",url,nil);must(e);req.Header.Set("Accept-Encoding","identity")
		r,e:=client.Do(req);must(e);defer r.Body.Close();if r.StatusCode!=200 {panic("HTTP verification failed")}
		b,e:=io.ReadAll(io.LimitReader(r.Body,limit+1));must(e);if int64(len(b))>limit {panic("oversize response")};return b}
	envelope:=download("https://play.nightcapgame.org/channel.json",manifest.MaxEnvelopeBytes)
	if !bytes.Equal(envelope,read(*output)) {panic("hosted envelope mismatch")}
	raw,sig,e=manifest.DecodeEnvelope(envelope);must(e);verified,e:=manifest.Verify(raw,sig,trust);must(e)
	if !bytes.Equal(raw,candidate) || !reflect.DeepEqual(verified.Files,old.Files) {panic("unexpected metadata change")}
	var total int64
	for _,file:=range verified.Files {
		b:=download(file.URL,file.Size);if int64(len(b))!=file.Size || manifest.Digest(b)!=file.SHA256 {panic("hosted asset mismatch: "+file.Path)};total+=file.Size
	}
	must(json.NewEncoder(os.Stdout).Encode(map[string]any{"release":m.Release,"verified_files":len(m.Files),"bytes":total,"signature":"valid against shipped production key","file_records_unchanged":true,"history_preserved":true,"channel_sha256":manifest.Digest(envelope)}))
}

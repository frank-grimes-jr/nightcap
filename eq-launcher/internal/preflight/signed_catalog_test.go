package preflight

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestSignedCatalogEvolutionAndBounds(t *testing.T) {
	for _, name := range []string{"current", "new feature", "client hash", "base", "schema", "runtime", "empty", "duplicate", "optional collision", "reserved", "too many", "site duplicate", "unknown field", "whitespace"} {
		t.Run(name, func(t *testing.T) {
			var c catalog
			if err := json.Unmarshal(Catalog(), &c); err != nil {
				t.Fatal(err)
			}
			switch name {
			case "new feature":
				c.Required = append(c.Required, "future_feature")
				c.ProxyVersion = "0.6.0"
			case "client hash":
				c.ClientSHA256 = "bad"
			case "base":
				c.ImageBase++
			case "schema":
				c.Schema++
			case "runtime":
				c.RuntimeSchema++
			case "empty":
				c.Required = nil
			case "duplicate":
				c.Required = append(c.Required, c.Required[0])
			case "optional collision":
				c.Optional = append(c.Optional, c.Required[0])
			case "reserved":
				c.Required[0] = "schema"
			case "too many":
				for len(c.Required) < 32 {
					c.Required = append(c.Required, "a")
				}
			case "site duplicate":
				c.Sites = append(c.Sites, c.Sites[0])
			}
			raw, _ := json.Marshal(c)
			if name == "unknown field" {
				raw = append(raw[:len(raw)-1], []byte(`,"extra":1}`)...)
			}
			if name == "whitespace" {
				raw = append(raw, '\n')
			}
			p, err := RuntimeForCatalog(raw)
			good := name == "current" || name == "new feature"
			if (err == nil) != good {
				t.Fatalf("accepted=%v: %v", err == nil, err)
			}
			if good && p.RequiredMask != (uint32(1)<<len(c.Required))-1 {
				t.Fatal("wrong required mask")
			}
		})
	}
}

func TestFutureSignedCatalogOnExactClient(t *testing.T) {
	name := os.Getenv("NIGHTCAP_TEST_EQGAME")
	if name == "" {
		t.Skip("read-only exact-client fixture required")
	}
	f, err := os.Open(name)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	c, _ := policy()
	c.Required = append(c.Required, "future_patch")
	c.ProxyVersion = "0.6.0"
	raw, _ := json.Marshal(c)
	config := append(configFixture(t), []byte("future_patch=1\n")...)
	if _, err = CheckOpen(f, config, raw); err == nil {
		t.Fatal("legacy policy accepted evolving catalog")
	}
	report, err := CheckSignedOpen(f, config, raw)
	if err != nil || !report.StaticValid {
		t.Fatalf("future catalog: %+v %v", report, err)
	}
	bad, _ := hex.DecodeString(c.Sites[0].Original)
	bad[0] ^= 1
	c.Sites[0].Original = hex.EncodeToString(bad)
	raw, _ = json.Marshal(c)
	if _, err = CheckSignedOpen(f, config, raw); err == nil {
		t.Fatal("bad site accepted")
	}
}

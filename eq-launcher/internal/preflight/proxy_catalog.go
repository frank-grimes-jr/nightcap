package preflight

import (
	"bytes"
	"debug/pe"
	"fmt"
)

// CheckProxyCatalog checks the exact proxy/catalog pair before signing a release.
// The generated contract's NUL-terminated hash and version must occur in mapped,
// persistent read-only data. This catches accidental mixed builds; it neither
// authenticates a DLL nor replaces the process-bound runtime health check.
func CheckProxyCatalog(proxy, metadata []byte) error {
	policy, err := RuntimeForCatalog(metadata)
	if err != nil {
		return err
	}
	if len(proxy) == 0 || int64(len(proxy)) > MaxProxyBytes {
		return fmt.Errorf("invalid proxy size")
	}
	file, _, err := bootstrapPE(proxy, true)
	if err != nil {
		return err
	}
	defer file.Close()
	var hashFound, versionFound bool
	for _, section := range file.Sections {
		if section.Size == 0 || section.VirtualSize == 0 || section.Characteristics&pe.IMAGE_SCN_MEM_READ == 0 ||
			section.Characteristics&(pe.IMAGE_SCN_MEM_WRITE|pe.IMAGE_SCN_MEM_EXECUTE|pe.IMAGE_SCN_MEM_DISCARDABLE) != 0 {
			continue
		}
		data := proxy[section.Offset : section.Offset+min(section.Size, section.VirtualSize)]
		hashFound = hashFound || bytes.Contains(data, []byte("\x00"+policy.CatalogSHA256+"\x00"))
		versionFound = versionFound || bytes.Contains(data, []byte("\x00"+policy.ProxyVersion+"\x00"))
	}
	if !hashFound || !versionFound {
		return fmt.Errorf("proxy/catalog contract mismatch: expected version %s, catalog %s", policy.ProxyVersion, policy.CatalogSHA256)
	}
	return nil
}

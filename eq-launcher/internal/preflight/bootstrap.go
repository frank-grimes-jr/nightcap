package preflight

import (
	"bytes"
	"crypto/sha256"
	"debug/pe"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"io"
	"os"

	"nightcap/eq-launcher/internal/client"
)

const MaxProxyBytes int64 = 16 << 20
const initializerExport = "NightcapInitialize"

// BootstrapMetadata contains RVAs, never preferred-base virtual addresses. The
// native bootstrap adds the actual child module base, including ASLR relocation.
type BootstrapMetadata struct {
	EntryRVA       uint32
	EntryOriginal  byte
	InitializerRVA uint32
	ProxyImageSize uint32
}
type ImageFile interface {
	io.ReaderAt
	Stat() (os.FileInfo, error)
}

// BootstrapOpen derives startup addresses from the caller's retained handles.
// The executable identity is compiled; proxy authenticity must already have been
// verified against a trusted signed inventory. PE validity alone is not trust.
func BootstrapOpen(executable, proxy ImageFile) (BootstrapMetadata, error) {
	var result BootstrapMetadata
	data, err := readBootstrapImage(executable, client.SupportedSize)
	if err != nil {
		return result, err
	}
	sum := sha256.Sum256(data)
	if int64(len(data)) != client.SupportedSize || hex.EncodeToString(sum[:]) != client.SupportedSHA256 {
		return result, fmt.Errorf("unsupported bootstrap executable")
	}
	entry, original, err := bootstrapEntry(data)
	if err != nil {
		return result, err
	}
	data, err = readBootstrapImage(proxy, MaxProxyBytes)
	if err != nil {
		return result, err
	}
	initializer, imageSize, err := bootstrapInitializer(data)
	if err != nil {
		return result, err
	}
	return BootstrapMetadata{EntryRVA: entry, EntryOriginal: original, InitializerRVA: initializer, ProxyImageSize: imageSize}, nil
}
func readBootstrapImage(file ImageFile, limit int64) ([]byte, error) {
	info, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > limit {
		return nil, fmt.Errorf("invalid bootstrap image size/type")
	}
	data, err := io.ReadAll(io.NewSectionReader(file, 0, info.Size()+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) != info.Size() {
		return nil, fmt.Errorf("bootstrap image changed while reading")
	}
	return data, nil
}

// Bound fields that debug/pe would otherwise use to allocate COFF symbol,
// relocation or string tables. Release images have no deprecated COFF tables.
func bootstrapPE(data []byte, dll bool) (*pe.File, *pe.OptionalHeader32, error) {
	fail := func() (*pe.File, *pe.OptionalHeader32, error) {
		return nil, nil, fmt.Errorf("invalid bootstrap PE32 image")
	}
	if len(data) < 64 || string(data[:2]) != "MZ" {
		return fail()
	}
	at := uint64(binary.LittleEndian.Uint32(data[60:64]))
	if at < 64 || at > 1<<20 || at+24+224 > uint64(len(data)) {
		return fail()
	}
	header := data[at : at+24]
	count := uint64(binary.LittleEndian.Uint16(header[6:8]))
	flags := binary.LittleEndian.Uint16(header[22:24])
	if string(header[:4]) != "PE\x00\x00" || binary.LittleEndian.Uint16(header[4:6]) != pe.IMAGE_FILE_MACHINE_I386 ||
		count == 0 || count > 96 || binary.LittleEndian.Uint16(header[20:22]) != 224 ||
		binary.LittleEndian.Uint32(header[12:16]) != 0 || binary.LittleEndian.Uint32(header[16:20]) != 0 ||
		flags&pe.IMAGE_FILE_EXECUTABLE_IMAGE == 0 || (flags&pe.IMAGE_FILE_DLL != 0) != dll {
		return fail()
	}
	table := at + 24 + 224
	if table+count*40 > uint64(len(data)) {
		return fail()
	}
	for i := uint64(0); i < count; i++ {
		row := data[table+i*40 : table+(i+1)*40]
		if !bytes.Equal(row[24:36], make([]byte, 12)) {
			return fail()
		}
	}
	file, err := pe.NewFile(bytes.NewReader(data))
	if err != nil {
		return nil, nil, fmt.Errorf("invalid bootstrap PE: %w", err)
	}
	optional, ok := file.OptionalHeader.(*pe.OptionalHeader32)
	if !ok || optional.Magic != 0x10b || optional.NumberOfRvaAndSizes != 16 ||
		optional.FileAlignment < 512 || optional.FileAlignment > 65536 || optional.FileAlignment&(optional.FileAlignment-1) != 0 ||
		optional.SectionAlignment < 4096 || optional.SectionAlignment&(optional.SectionAlignment-1) != 0 || optional.SectionAlignment < optional.FileAlignment ||
		optional.ImageBase%65536 != 0 || optional.SizeOfImage%optional.SectionAlignment != 0 || optional.SizeOfHeaders%optional.FileAlignment != 0 || optional.SizeOfImage == 0 || optional.SizeOfImage > 256<<20 ||
		uint64(optional.ImageBase)+uint64(optional.SizeOfImage) > 1<<32 || optional.SizeOfHeaders < uint32(table+count*40) || uint64(optional.SizeOfHeaders) > uint64(len(data)) {
		file.Close()
		return fail()
	}
	for i, section := range file.Sections {
		start, span := uint64(section.VirtualAddress), uint64(max(section.VirtualSize, section.Size))
		end := start + span
		rawStart, rawEnd := uint64(section.Offset), uint64(section.Offset)+uint64(section.Size)
		if section.VirtualAddress%optional.SectionAlignment != 0 || section.Offset%optional.FileAlignment != 0 || section.Size%optional.FileAlignment != 0 ||
			span == 0 || start < uint64(optional.SizeOfHeaders) || end > uint64(optional.SizeOfImage) ||
			(section.Size != 0 && (rawStart < uint64(optional.SizeOfHeaders) || rawEnd > uint64(len(data)))) {
			file.Close()
			return fail()
		}
		for _, other := range file.Sections[:i] {
			otherStart := uint64(other.VirtualAddress)
			otherEnd := otherStart + uint64(max(other.VirtualSize, other.Size))
			overlapVirtual := start < otherEnd && otherStart < end
			overlapRaw := section.Size != 0 && other.Size != 0 && rawStart < uint64(other.Offset)+uint64(other.Size) && uint64(other.Offset) < rawEnd
			if overlapVirtual || overlapRaw {
				file.Close()
				return fail()
			}
		}
	}
	return file, optional, nil
}
func bootstrapCode(data []byte, file *pe.File, rva uint32) (byte, error) {
	raw, err := siteBytes(data, file.Sections, rva, 1)
	if err != nil {
		return 0, err
	}
	for _, section := range file.Sections {
		if uint64(rva) >= uint64(section.VirtualAddress) && uint64(rva) < uint64(section.VirtualAddress)+uint64(max(section.Size, section.VirtualSize)) {
			required := uint32(pe.IMAGE_SCN_MEM_EXECUTE | pe.IMAGE_SCN_MEM_READ)
			if section.Characteristics&required != required || section.Characteristics&(pe.IMAGE_SCN_MEM_WRITE|pe.IMAGE_SCN_MEM_DISCARDABLE) != 0 {
				return 0, fmt.Errorf("bootstrap target is not persistent read-only executable code")
			}
			return raw[0], nil
		}
	}
	return 0, fmt.Errorf("bootstrap target is unmapped")
}
func bootstrapEntry(data []byte) (uint32, byte, error) {
	file, optional, err := bootstrapPE(data, false)
	if err != nil {
		return 0, 0, err
	}
	defer file.Close()
	// The supported game has no executable TLS callbacks before its entry gate.
	tls := optional.DataDirectory[pe.IMAGE_DIRECTORY_ENTRY_TLS]
	if tls.VirtualAddress != 0 || tls.Size != 0 {
		return 0, 0, fmt.Errorf("bootstrap executable TLS is unsupported")
	}
	first, err := bootstrapCode(data, file, optional.AddressOfEntryPoint)
	if err != nil {
		return 0, 0, err
	}
	if first == 0xcc {
		return 0, 0, fmt.Errorf("bootstrap entry is already a breakpoint")
	}
	return optional.AddressOfEntryPoint, first, nil
}
func bootstrapInitializer(data []byte) (uint32, uint32, error) {
	file, optional, err := bootstrapPE(data, true)
	if err != nil {
		return 0, 0, err
	}
	defer file.Close()
	directory := optional.DataDirectory[pe.IMAGE_DIRECTORY_ENTRY_EXPORT]
	if directory.VirtualAddress == 0 || directory.Size < 40 || directory.Size > 1<<20 {
		return 0, 0, fmt.Errorf("invalid proxy export directory")
	}
	raw, err := siteBytes(data, file.Sections, directory.VirtualAddress, uint64(directory.Size))
	if err != nil {
		return 0, 0, err
	}
	word := func(at int) uint32 { return binary.LittleEndian.Uint32(raw[at : at+4]) }
	functions, names := word(20), word(24)
	if functions == 0 || functions > 512 || names == 0 || names > 512 {
		return 0, 0, fmt.Errorf("invalid proxy export count")
	}
	addresses, err := siteBytes(data, file.Sections, word(28), uint64(functions)*4)
	if err != nil {
		return 0, 0, err
	}
	namePointers, err := siteBytes(data, file.Sections, word(32), uint64(names)*4)
	if err != nil {
		return 0, 0, err
	}
	ordinals, err := siteBytes(data, file.Sections, word(36), uint64(names)*2)
	if err != nil {
		return 0, 0, err
	}
	var target uint32
	previous := ""
	for i := uint32(0); i < names; i++ {
		name, err := exportName(data, file, binary.LittleEndian.Uint32(namePointers[i*4:i*4+4]))
		if err != nil {
			return 0, 0, err
		}
		if name <= previous {
			return 0, 0, fmt.Errorf("duplicate or unsorted proxy exports")
		}
		previous = name
		index := uint32(binary.LittleEndian.Uint16(ordinals[i*2 : i*2+2]))
		if index >= functions {
			return 0, 0, fmt.Errorf("invalid proxy export ordinal")
		}
		if name == initializerExport {
			target = binary.LittleEndian.Uint32(addresses[index*4 : index*4+4])
		}
	}
	if target == 0 {
		return 0, 0, fmt.Errorf("missing proxy initializer export")
	}
	if uint64(target) >= uint64(directory.VirtualAddress) && uint64(target) < uint64(directory.VirtualAddress)+uint64(directory.Size) {
		return 0, 0, fmt.Errorf("forwarded proxy initializer is forbidden")
	}
	if _, err := bootstrapCode(data, file, target); err != nil {
		return 0, 0, err
	}
	return target, optional.SizeOfImage, nil
}
func exportName(data []byte, file *pe.File, rva uint32) (string, error) {
	var name []byte
	for i := uint64(0); i < 128; i++ {
		if uint64(rva)+i >= 1<<32 {
			break
		}
		b, err := siteBytes(data, file.Sections, rva+uint32(i), 1)
		if err != nil {
			return "", err
		}
		if b[0] == 0 && len(name) > 0 {
			return string(name), nil
		}
		if b[0] < 33 || b[0] > 126 {
			break
		}
		name = append(name, b[0])
	}
	return "", fmt.Errorf("invalid or unterminated proxy export name")
}

// CheckHelperOpen checks the signed helper's conventional x86 executable shape.
// The inventory signature/hash, not this shape check, establishes authenticity.
func CheckHelperOpen(file ImageFile) error {
	data, err := readBootstrapImage(file, MaxProxyBytes)
	if err != nil {
		return err
	}
	executable, optional, err := bootstrapPE(data, false)
	if err != nil {
		return err
	}
	defer executable.Close()
	_, err = bootstrapCode(data, executable, optional.AddressOfEntryPoint)
	return err
}

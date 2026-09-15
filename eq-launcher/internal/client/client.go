package client

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
)

const SupportedSize int64 = 8774656
const SupportedSHA256 = "2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e"

type Report struct {
	Size      int64  `json:"size"`
	SHA256    string `json:"sha256"`
	Supported bool   `json:"supported_executable"`
	// A supported executable does not prove installed assets/runtime patch health.
	ReadyToPlay bool   `json:"ready_to_play"`
	Status      string `json:"status"`
}

// Inspect reads eqgame.exe only. It cannot install, modify, inject or launch it.
func Inspect(filename string) (Report, error) {
	file, err := os.Open(filename)
	if err != nil {
		return Report{}, err
	}
	defer file.Close()
	stat, err := file.Stat()
	if err != nil {
		return Report{}, err
	}
	if !stat.Mode().IsRegular() {
		return Report{}, fmt.Errorf("client executable is not a regular file")
	}
	report := Report{Size: stat.Size(), Status: "unsupported client executable"}
	if report.Size != SupportedSize {
		return report, nil
	}
	hash := sha256.New()
	count, err := io.Copy(hash, io.LimitReader(file, SupportedSize+1))
	if err != nil {
		return Report{}, err
	}
	if count != SupportedSize {
		return Report{}, fmt.Errorf("client executable changed while reading")
	}
	report.SHA256 = hex.EncodeToString(hash.Sum(nil))
	report.Supported = report.SHA256 == SupportedSHA256
	if report.Supported {
		report.Status = "supported RoF2 executable; installed asset and required runtime patch checks still pending"
	}
	return report, nil
}

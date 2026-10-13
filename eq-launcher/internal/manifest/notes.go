package manifest

import (
	"fmt"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"
)

const PatchNotesMinimumLauncher = "0.6.0"

type PatchChange struct {
	Kind string `json:"kind"`
	Text string `json:"text"`
}

type PatchNote struct {
	Release uint64        `json:"release"`
	Date    string        `json:"date"`
	Changes []PatchChange `json:"changes"`
}

func SupportsPatchNotes(v string) bool {
	parts, err := version(v)
	return err == nil && (parts[0] > 0 || parts[1] >= 6)
}

// Notes are signed plain text, newest first. Limits keep the patcher readable
// and leave ample space for its file inventory in the bounded envelope.
func ValidatePatchNotes(notes []PatchNote, release uint64) error {
	if len(notes) > 100 {
		return fmt.Errorf("too many patch notes")
	}
	previous := release
	previousDate := "9999-12-31"
	for i, note := range notes {
		if note.Release == 0 || note.Release > release || (i > 0 && note.Release >= previous) {
			return fmt.Errorf("patch notes must have unique releases, newest first, no later than the manifest")
		}
		if _, err := time.Parse("2006-01-02", note.Date); err != nil || note.Date > previousDate {
			return fmt.Errorf("invalid patch note date or date order")
		}
		if len(note.Changes) == 0 || len(note.Changes) > 12 {
			return fmt.Errorf("patch notes require 1 to 12 changes")
		}
		for _, change := range note.Changes {
			if change.Kind != "feature" && change.Kind != "fix" {
				return fmt.Errorf("patch change must be feature or fix")
			}
			if !utf8.ValidString(change.Text) || strings.TrimSpace(change.Text) != change.Text || len(change.Text) == 0 || utf8.RuneCountInString(change.Text) > 240 || strings.ContainsFunc(change.Text, unicode.IsControl) {
				return fmt.Errorf("patch changes require concise single-line text")
			}
		}
		previous, previousDate = note.Release, note.Date
	}
	return nil
}

func ClonePatchNotes(notes []PatchNote) []PatchNote {
	result := append([]PatchNote{}, notes...)
	for i := range result {
		result[i].Changes = append([]PatchChange{}, result[i].Changes...)
	}
	return result
}

<script setup lang="ts">
import { computed } from "vue";
import type { PatchNote } from "./bridge";
const props = defineProps<{ notes: PatchNote[]; release: number }>();
const latest = computed(() => props.notes.find(note => note.release === props.release));
const history = computed(() => props.notes.filter(note => note.release < props.release));
const dateLabel = (date: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
}).format(new Date(`${date}T00:00:00Z`));
const kindLabel = { feature: "Feature", fix: "Bug fix", server: "Server" };
</script>

<template>
  <section class="details patch-notes" aria-labelledby="patch-notes-title">
    <div class="section-heading">
      <h2 id="patch-notes-title">Latest update</h2>
      <time v-if="latest" :datetime="latest.date">{{ dateLabel(latest.date) }}</time>
    </div>
    <template v-if="latest">
      <p class="patch-release">Patch {{ latest.release }}</p>
      <ul class="patch-changes">
        <li v-for="(change, i) in latest.changes" :key="i">
          <span class="change-kind" :class="change.kind">{{ kindLabel[change.kind] }}</span>
          <span>{{ change.text }}<small v-if="change.reason" class="change-reason">Why: {{ change.reason }}</small></span>
        </li>
      </ul>
    </template>
    <p v-else class="notes-empty">{{ release ? 'No summary was published for this patch.' : 'Patch summaries will appear after checking for updates.' }}</p>
    <details v-if="history.length" class="patch-history">
      <summary>Previous patches <span>({{ history.length }})</span></summary>
      <div class="history-scroll" tabindex="0" role="region" aria-label="Previous patch summaries">
        <article v-for="note in history" :key="note.release">
          <h3><time :datetime="note.date">{{ dateLabel(note.date) }}</time><span>Patch {{ note.release }}</span></h3>
          <ul class="patch-changes">
            <li v-for="(change, i) in note.changes" :key="i">
              <span class="change-kind" :class="change.kind">{{ kindLabel[change.kind] }}</span>
              <span>{{ change.text }}<small v-if="change.reason" class="change-reason">Why: {{ change.reason }}</small></span>
            </li>
          </ul>
        </article>
      </div>
    </details>
  </section>
</template>

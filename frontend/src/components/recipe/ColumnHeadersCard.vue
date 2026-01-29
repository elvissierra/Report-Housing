<template>
  <v-card class="mb-6 card-headers" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        <span>Active headers</span>
        <v-tooltip text="These are the column names used throughout the analysis.">
          <template #activator="{ props }">
            <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
          </template>
        </v-tooltip>
      </div>

      <v-btn
        size="x-small"
        variant="text"
        class="text-none"
        prepend-icon="mdi-pencil-outline"
        @click="showManualHeaders = !showManualHeaders"
      >
        {{ showManualHeaders ? 'Hide manual editor' : 'Edit headers manually' }}
      </v-btn>
    </v-card-title>

    <v-card-text class="py-3">
      <div v-if="columnHeaders.length" class="mt-1 d-flex flex-wrap ga-1">
        <v-chip
          v-for="(h, index) in columnHeaders"
          :key="h"
          size="small"
          variant="flat"
          class="ma-1 header-chip"
          :style="headerChipStyle(index)"
        >
          {{ formatHeaderLabel(h) }}
        </v-chip>
      </div>

      <div v-else class="text-caption text-medium-emphasis mt-1">
        No headers detected yet. Use “Import headers” in Utilities or open the manual editor.
      </div>

      <v-expand-transition>
        <div v-show="showManualHeaders" class="mt-4">
          <v-textarea
            v-model="headersText"
            label="Known headers"
            placeholder="One per line or comma-separated"
            variant="outlined"
            rows="1"
            hide-details
            clearable
            density="compact"
            no-resize
            class="my-0 no-resize-ta"
            style="max-height: 48px;"
          />
          <div class="d-flex align-center mt-1">
            <div class="text-caption">
              Paste or type your column headers, then click Apply.
            </div>
            <v-spacer />
            <v-btn variant="tonal" color="primary" size="small" @click="applyHeaders">Apply</v-btn>
          </div>
        </div>
      </v-expand-transition>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ columnHeaders: string[] }>()
const emit = defineEmits<{ (e: 'setHeaders', headers: string[]): void }>()

const headersText = ref((props.columnHeaders || []).join('\n'))
const showManualHeaders = ref(false)

watch(
  () => props.columnHeaders,
  (next) => {
    headersText.value = (next || []).join('\n')
  },
  { deep: true },
)

function normalizeHeaderName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/[^\w]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
}

function formatHeaderLabel(name: string): string {
  const withSpaces = name.replace(/_/g, ' ').trim()
  if (!withSpaces) return ''
  return withSpaces.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
}

const headerChipPalette = ['#fef9c3', '#fef3c7', '#fde68a', '#facc15', '#eab308']
const headerChipStyle = (index: number) => ({
  backgroundColor: headerChipPalette[index % headerChipPalette.length],
  color: '#1f2937',
})

function applyHeaders() {
  const parts = headersText.value
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map(normalizeHeaderName)

  emit('setHeaders', parts)
}
</script>
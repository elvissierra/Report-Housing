

<template>
  <v-dialog v-model="dialog" max-width="900">
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>Logic reference</span>
        <v-btn icon="mdi-close" variant="text" @click="dialog = false" />
      </v-card-title>
      <v-divider />
      <v-card-text style="max-height: 70vh; overflow-y: auto;">
        <pre class="text-caption" style="white-space: pre-wrap;">{{ definitionsText }}</pre>
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="dialog = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  apiBaseUrl: string
}>()

const emit = defineEmits<{
  (e: 'error', message: string): void
}>()

const dialog = ref(false)
const definitionsText = ref<string>('')

async function fetchDefinitions(): Promise<string> {
  const resp = await fetch(`${props.apiBaseUrl}/definitions.txt`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return await resp.text()
}

async function open() {
  try {
    if (!definitionsText.value) {
      definitionsText.value = await fetchDefinitions()
    }
    dialog.value = true
  } catch (err) {
    console.error('Failed to load logic reference:', err)
    emit('error', 'Failed to load logic reference. Please try again.')
  }
}

async function download() {
  try {
    const text = await fetchDefinitions()
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'report_auto_definitions.txt'
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Failed to download definitions:', err)
    emit('error', 'Failed to download definitions. Please try again.')
  }
}

defineExpose({ open, download })
</script>
<template>
  <v-card class="mb-6 card-insights" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center"><span>Correlations</span></v-card-title>
    <v-card-text>
      <v-combobox
        :model-value="sources"
        :items="columnHeaders"
        label="source columns"
        multiple
        chips
        closable-chips
        clearable
        hide-details
        density="compact"
        @update:modelValue="(v) => emit('update:sources', v as string[])"
      />

      <v-combobox
        :model-value="targets"
        :items="columnHeaders"
        label="target columns"
        multiple
        chips
        closable-chips
        clearable
        hide-details
        class="mt-2"
        density="compact"
        @update:modelValue="(v) => emit('update:targets', v as string[])"
      />

      <v-slider
        :model-value="threshold"
        :min="0"
        :max="1"
        :step="0.05"
        :show-ticks="true"
        class="mt-6"
        @update:modelValue="(v) => emit('update:threshold', Number(v))"
      />
      <div class="text-caption">threshold: {{ Number(threshold).toFixed(2) }}</div>

      <div class="d-flex align-center justify-space-between mt-2">
        <span class="text-caption">Correlations enabled</span>
        <v-switch
          :model-value="enabled"
          inset
          density="compact"
          class="switch-sm"
          hide-details
          @update:modelValue="(v) => emit('update:enabled', Boolean(v))"
        />
      </div>

      <v-divider class="my-3" />

      <div class="mt-1">
        <div class="d-flex align-center justify-space-between mb-1">
          <span class="text-caption font-weight-medium">Additional correlation blocks</span>
          <v-btn size="x-small" variant="text" prepend-icon="mdi-plus" @click="addBlock">Add</v-btn>
        </div>

        <v-card
          v-for="block in extraBlocks"
          :key="block.id"
          class="mb-2 pa-2"
          variant="outlined"
          rounded="lg"
        >
          <v-row dense>
            <v-col cols="12">
              <v-combobox
                :model-value="block.sources"
                :items="columnHeaders"
                label="source columns"
                multiple
                chips
                closable-chips
                clearable
                hide-details
                density="compact"
                @update:modelValue="(v) => updateBlock(block.id, { sources: v as string[] })"
              />
            </v-col>
            <v-col cols="12">
              <v-combobox
                :model-value="block.targets"
                :items="columnHeaders"
                label="target columns"
                multiple
                chips
                closable-chips
                clearable
                hide-details
                class="mt-2"
                density="compact"
                @update:modelValue="(v) => updateBlock(block.id, { targets: v as string[] })"
              />
            </v-col>
            <v-col cols="12">
              <v-slider
                :model-value="block.threshold"
                :min="0"
                :max="1"
                :step="0.05"
                class="mt-2"
                @update:modelValue="(v) => updateBlock(block.id, { threshold: Number(v) })"
              />
              <div class="text-caption">threshold: {{ Number(block.threshold).toFixed(2) }}</div>
            </v-col>
            <v-col cols="12" class="d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <span class="text-caption mr-2">Enabled</span>
                <v-switch
                  :model-value="block.enabled"
                  inset
                  density="compact"
                  class="switch-sm"
                  hide-details
                  @update:modelValue="(v) => updateBlock(block.id, { enabled: Boolean(v) })"
                />
              </div>
              <v-btn icon="mdi-delete" variant="text" size="small" @click="removeBlock(block.id)" />
            </v-col>
          </v-row>
        </v-card>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
interface CorrelationBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean
}

const props = defineProps<{
  columnHeaders: string[]
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean
  extraBlocks: CorrelationBlockConfig[]
}>()

const emit = defineEmits<{
  (e: 'update:sources', v: string[]): void
  (e: 'update:targets', v: string[]): void
  (e: 'update:threshold', v: number): void
  (e: 'update:enabled', v: boolean): void
  (e: 'update:extraBlocks', v: CorrelationBlockConfig[]): void
}>()

function makeId() {
  try {
    return crypto.randomUUID().slice(0, 8)
  } catch {
    return Math.random().toString(36).slice(2, 10)
  }
}

function addBlock() {
  emit('update:extraBlocks', [
    ...props.extraBlocks,
    { id: makeId(), sources: [], targets: [], threshold: props.threshold, enabled: true },
  ])
}

function removeBlock(id: string) {
  emit('update:extraBlocks', props.extraBlocks.filter((b) => b.id !== id))
}

function updateBlock(id: string, patch: Partial<CorrelationBlockConfig>) {
  emit('update:extraBlocks', props.extraBlocks.map((b) => (b.id === id ? { ...b, ...patch } : b)))
}
</script>
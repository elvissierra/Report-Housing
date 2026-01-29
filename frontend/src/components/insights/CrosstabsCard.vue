<template>
  <v-card class="mb-6 card-crosstabs" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center"><span>Crosstabs</span></v-card-title>
    <v-card-text>
      <v-combobox
        :model-value="sources"
        :items="columnHeaders"
        label="sources"
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
        label="targets"
        multiple
        chips
        closable-chips
        clearable
        hide-details
        class="mt-2"
        density="compact"
        @update:modelValue="(v) => emit('update:targets', v as string[])"
      />

      <div class="d-flex align-center justify-space-between mt-3">
        <span class="text-caption">Crosstabs enabled</span>
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
          <span class="text-caption font-weight-medium">Additional crosstab blocks</span>
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
            <v-col cols="12" md="6">
              <v-combobox
                :model-value="block.sources"
                :items="columnHeaders"
                label="sources"
                multiple
                chips
                closable-chips
                clearable
                hide-details
                density="compact"
                @update:modelValue="(v) => updateBlock(block.id, { sources: v as string[] })"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-combobox
                :model-value="block.targets"
                :items="columnHeaders"
                label="targets"
                multiple
                chips
                closable-chips
                clearable
                hide-details
                density="compact"
                @update:modelValue="(v) => updateBlock(block.id, { targets: v as string[] })"
              />
            </v-col>
            <v-col cols="12" class="d-flex align-center justify-space-between mt-2">
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
interface CrosstabBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  enabled: boolean
}

const props = defineProps<{
  columnHeaders: string[]
  sources: string[]
  targets: string[]
  enabled: boolean
  extraBlocks: CrosstabBlockConfig[]
}>()

const emit = defineEmits<{
  (e: 'update:sources', v: string[]): void
  (e: 'update:targets', v: string[]): void
  (e: 'update:enabled', v: boolean): void
  (e: 'update:extraBlocks', v: CrosstabBlockConfig[]): void
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
    { id: makeId(), sources: [], targets: [], enabled: true },
  ])
}

function removeBlock(id: string) {
  emit('update:extraBlocks', props.extraBlocks.filter((b) => b.id !== id))
}

function updateBlock(id: string, patch: Partial<CrosstabBlockConfig>) {
  emit('update:extraBlocks', props.extraBlocks.map((b) => (b.id === id ? { ...b, ...patch } : b)))
}
</script>
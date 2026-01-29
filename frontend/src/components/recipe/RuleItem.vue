

<template>
  <v-card class="mb-2 py-2 px-3" variant="outlined" elevation="0" rounded="lg">
    <v-row dense class="align-center">
      <v-col cols="12" md="8">
        <div class="text-subtitle-1">
          <strong>{{ rule.column }}</strong> — {{ rule.operation }}
        </div>
      </v-col>
      <v-col cols="12" md="4" class="d-flex justify-end">
        <v-btn icon="mdi-delete" variant="text" @click="emitRemove" />
      </v-col>
    </v-row>

    <v-row dense class="align-center mb-1">
      <v-col cols="12" md="6" class="d-flex ga-4 py-0">
        <div class="d-flex flex-column align-center">
          <v-switch
            v-model="rule.options.separateNodes"
            inset
            density="compact"
            class="switch-sm"
            hide-details
            @update:modelValue="emitUpdate"
          />
          <div class="text-caption mt-1 nowrap">separate</div>
        </div>
        <div class="d-flex flex-column align-center">
          <v-switch
            v-model="rule.options.rootOnly"
            inset
            density="compact"
            class="switch-sm"
            hide-details
            @update:modelValue="emitUpdate"
          />
          <div class="text-caption mt-1 nowrap">root only</div>
        </div>
      </v-col>
      <v-col cols="12" md="6" class="d-flex justify-end align-center py-0">
        <v-switch
          v-model="rule.enabled"
          inset
          density="compact"
          class="switch-sm"
          hide-details
          @update:modelValue="emitUpdate"
        />
        <span class="text-caption ml-2">enabled</span>
      </v-col>
    </v-row>

    <v-row dense class="ga-2 mt-1">
      <v-col cols="12" md="3" v-if="rule.operation === 'valueCount'">
        <v-text-field
          v-model="rule.options.value"
          label="value"
          density="compact"
          clearable
          hide-details
          @blur="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field
          v-model="rule.options.delimiter"
          label="delimiter"
          clearable
          density="compact"
          hide-details
          @blur="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-combobox
          v-model="excludeKeysModel"
          label="exclude keys"
          multiple
          chips
          :chip-props="{ size: 'small' }"
          closable-chips
          clearable
          hide-details
          density="compact"
          @update:modelValue="applyExcludeChips"
        />
      </v-col>
    </v-row>

    <v-row dense class="ga-2 mt-1">
      <v-col cols="12" md="4">
        <v-select
          v-model="rule.options.filterColumn"
          :items="columnHeaders"
          label="filter column (optional)"
          clearable
          hide-details
          density="compact"
          @update:modelValue="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-text-field
          v-model="rule.options.filterValue"
          label="filter value"
          density="compact"
          clearable
          hide-details
          @blur="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-select
          v-model="rule.options.filterOperator"
          :items="['eq']"
          label="operator"
          clearable
          hide-details
          density="compact"
          @update:modelValue="emitUpdate"
        />
      </v-col>
    </v-row>

    <v-row dense class="ga-2 mt-1">
      <v-col cols="12">
        <v-combobox
          v-model="groupByModel"
          :items="columnHeaders"
          label="group by (optional)"
          multiple
          chips
          closable-chips
          clearable
          hide-details
          density="compact"
          @update:modelValue="emitUpdate"
        />
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Rule } from '../../types/recipe'

const props = defineProps<{ rule: Rule; columnHeaders: string[] }>()
const emit = defineEmits<{
  (e: 'update', rule: Rule): void
  (e: 'remove', id: string): void
}>()

const excludeKeysLocal = ref<string[]>(Array.isArray(props.rule.options.excludeKeys) ? [...props.rule.options.excludeKeys] : [])

watch(
  () => props.rule.options.excludeKeys,
  (next) => {
    excludeKeysLocal.value = Array.isArray(next) ? [...next] : []
  },
  { deep: true },
)

const excludeKeysModel = computed<string[]>({
  get: () => excludeKeysLocal.value,
  set: (val) => {
    excludeKeysLocal.value = Array.isArray(val) ? val : []
  },
})

const groupByModel = computed<string[]>({
  get: () => (Array.isArray((props.rule as any).group_by) ? (props.rule as any).group_by : []),
  set: (val) => {
    ;(props.rule as any).group_by = Array.isArray(val) ? val : []
  },
})

function applyExcludeChips() {
  const arr = excludeKeysLocal.value || []
  const keys = arr.map((s) => String(s).trim()).filter(Boolean)
  props.rule.options.excludeKeys = keys
  emitUpdate()
}

function emitUpdate() {
  emit('update', props.rule)
}

function emitRemove() {
  emit('remove', props.rule.id)
}
</script>
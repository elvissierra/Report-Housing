<template>
  <v-card class="mb-2 py-2 px-3" variant="outlined" elevation="0" rounded="lg">
    <v-row dense class="align-center">
      <v-col cols="12" md="8">
        <div class="text-subtitle-1">
          <strong>{{ local.column }}</strong> — {{ local.operation }}
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
            v-model="local.options.separateNodes"
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
            v-model="local.options.rootOnly"
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
          v-model="local.enabled"
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
      <v-col cols="12" md="3" v-if="local.operation === 'valueCount'">
        <v-text-field
          v-model="local.options.value"
          label="value"
          density="compact"
          clearable
          hide-details
          @blur="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field
          v-model="local.options.delimiter"
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
          v-model="local.options.filterColumn"
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
          v-model="local.options.filterValue"
          label="filter value"
          density="compact"
          clearable
          hide-details
          @blur="emitUpdate"
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-select
          v-model="local.options.filterOperator"
          :items="['eq', 'neq', 'gt', 'lt', 'in', 'not_in', 'contains']"
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
import { computed, reactive, watch } from 'vue'
import type { Rule } from '../../types/recipe'

const props = defineProps<{ rule: Rule; columnHeaders: string[] }>()
const emit = defineEmits<{
  (e: 'update', rule: Rule): void
  (e: 'remove', id: string): void
}>()

// Local reactive copy — never mutate the prop directly.
const local = reactive<Rule>({
  ...props.rule,
  options: { ...props.rule.options },
  group_by: [...(props.rule.group_by ?? [])],
})

// Keep local in sync if the parent replaces the rule object (e.g. after store reset).
watch(
  () => props.rule,
  (r) => {
    Object.assign(local, { ...r, options: { ...r.options }, group_by: [...(r.group_by ?? [])] })
  },
  { deep: true },
)

const excludeKeysModel = computed<string[]>({
  get: () => (Array.isArray(local.options.excludeKeys) ? [...local.options.excludeKeys] : []),
  set: (val) => {
    local.options.excludeKeys = Array.isArray(val) ? val : []
  },
})

const groupByModel = computed<string[]>({
  get: () => (Array.isArray(local.group_by) ? local.group_by : []),
  set: (val) => {
    local.group_by = Array.isArray(val) ? val : []
  },
})

function applyExcludeChips() {
  const keys = (excludeKeysModel.value ?? []).map((s) => String(s).trim()).filter(Boolean)
  local.options.excludeKeys = keys
  emitUpdate()
}

function emitUpdate() {
  emit('update', { ...local, options: { ...local.options }, group_by: [...(local.group_by ?? [])] })
}

function emitRemove() {
  emit('remove', local.id)
}
</script>

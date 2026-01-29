<template>
  <v-card class="mb-6 card-add-rule" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center">
      <span>Add Rule</span>
    </v-card-title>

    <v-card-text>
      <v-row dense>
        <v-col cols="12" md="6">
          <v-autocomplete
            v-model="draft.column"
            :items="columnHeaders"
            label="Column"
            clearable
            hide-details
            density="compact"
          />
        </v-col>

        <v-col cols="12" md="4">
          <v-select
            v-model="draft.operation"
            :items="operations"
            label="Operation"
            clearable
            hide-details
            density="compact"
          />
        </v-col>

        <v-col cols="12" md="2" class="d-flex align-center">
          <v-btn
            block
            color="primary"
            variant="elevated"
            :disabled="!draft.column || !draft.operation"
            @click="emitAdd"
          >
            Add
          </v-btn>
        </v-col>
      </v-row>

      <div class="text-caption text-medium-emphasis mt-2">
        Tip: start with <code>distribution</code> for categorical columns or <code>average/sum/median</code> for numeric columns.
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { Operation } from '../../types/recipe'

defineProps<{
  columnHeaders: string[]
  operations: Operation[]
}>()

const emit = defineEmits<{
  (e: 'add', payload: { column: string; operation: Operation }): void
}>()

const draft = reactive<{ column: string; operation: Operation | null }>({
  column: '',
  operation: null,
})

function emitAdd() {
  if (!draft.column || !draft.operation) return
  emit('add', { column: draft.column, operation: draft.operation })
  draft.column = ''
  draft.operation = null
}
</script>
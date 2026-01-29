

<template>
  <v-card class="mb-6 card-rules" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center">
      <span>Rules</span>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <template v-if="rules.length">
        <RuleItem
          v-for="r in rules"
          :key="r.id"
          :rule="r"
          :column-headers="columnHeaders"
          @update="onUpdate"
          @remove="onRemove"
        />
      </template>
      <template v-else>
        <div class="text-medium-emphasis">No rules yet — add one above.</div>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import RuleItem from './RuleItem.vue'
import type { Rule } from '../../types/recipe'

defineProps<{ rules: Rule[]; columnHeaders: string[] }>()

const emit = defineEmits<{
  (e: 'updateRule', rule: Rule): void
  (e: 'removeRule', id: string): void
}>()

function onUpdate(rule: Rule) {
  emit('updateRule', rule)
}

function onRemove(id: string) {
  emit('removeRule', id)
}
</script>
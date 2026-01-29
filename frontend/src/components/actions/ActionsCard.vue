

<template>
  <v-card class="mb-6 card-actions" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center justify-space-between">
      <span>Utilities</span>
      <div class="d-flex ga-2">
        <v-btn
          class="text-truncate"
          variant="tonal"
          color="primary"
          :disabled="!inputFile || isRunning"
          prepend-icon="mdi-table-column-plus-after"
          @click="emit('importHeaders')"
        >
          Import headers
        </v-btn>
        <v-btn
          class="text-truncate primary-pill"
          variant="flat"
          color="primary"
          :loading="isRunning"
          :disabled="isRunning || !inputFile"
          prepend-icon="mdi-play-circle"
          @click="emit('runReport')"
        >
          Run report
        </v-btn>
      </div>
    </v-card-title>
    <v-card-text>
      <div class="text-caption font-weight-medium mb-1">Run &amp; output</div>
      <v-row dense>
        <v-col cols="12" md="5">
          <v-text-field
            :model-value="bundleName"
            label="Output Analysis Title"
            placeholder="generated_report"
            density="compact"
            variant="outlined"
            hide-details
            @update:modelValue="(v) => emit('update:bundleName', String(v ?? ''))"
          />
        </v-col>
        <v-col cols="12" md="7">
          <v-file-input
            :model-value="inputFile"
            label="Data file (CSV)"
            accept=".csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
            density="compact"
            variant="outlined"
            hide-details
            @update:modelValue="(v) => emit('update:inputFile', (v as File | null) ?? null)"
          />
        </v-col>
      </v-row>

      <v-divider class="my-3" />

      <div class="text-caption font-weight-medium mb-1">Recipe &amp; reference</div>
      <v-row dense>
        <v-col cols="12" md="4">
          <v-btn
            block
            class="text-truncate"
            variant="tonal"
            color="primary"
            @click="emit('exportRecipe')"
            prepend-icon="mdi-content-save"
          >
            Export recipe
          </v-btn>
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            block
            class="text-truncate"
            variant="tonal"
            @click="emit('openImport')"
            prepend-icon="mdi-file-import"
          >
            Import recipe
          </v-btn>
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            block
            class="text-truncate"
            variant="text"
            color="error"
            prepend-icon="mdi-broom"
            @click="emit('clearRecipe')"
          >
            Clear setup
          </v-btn>
        </v-col>
      </v-row>

      <v-row dense class="mt-2">
        <v-col cols="12" md="6">
          <v-btn
            block
            class="text-truncate"
            variant="outlined"
            prepend-icon="mdi-book-open-page-variant"
            @click="emit('openLogicReference')"
          >
            View logic reference
          </v-btn>
        </v-col>
        <v-col cols="12" md="6">
          <v-btn
            block
            class="text-truncate"
            variant="text"
            prepend-icon="mdi-file-document-outline"
            @click="emit('downloadLogicReference')"
          >
            Download logic reference (.txt)
          </v-btn>
        </v-col>
      </v-row>

      <div v-if="errorMessage" class="mt-2 text-caption text-error">
        {{ errorMessage }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  inputFile: File | null
  bundleName: string
  isRunning: boolean
  errorMessage: string | null
}>()

const emit = defineEmits<{
  (e: 'update:inputFile', v: File | null): void
  (e: 'update:bundleName', v: string): void
  (e: 'importHeaders'): void
  (e: 'runReport'): void
  (e: 'exportRecipe'): void
  (e: 'openImport'): void
  (e: 'clearRecipe'): void
  (e: 'openLogicReference'): void
  (e: 'downloadLogicReference'): void
}>()
</script>




<template>
  <v-app-bar density="comfortable">
    <v-toolbar-title>Reporting Auto</v-toolbar-title>
    <v-toolbar-items class="ml-4">
      <v-btn variant="text" prepend-icon="mdi-content-save" @click="exportRecipe">Export</v-btn>
      <v-btn variant="text" prepend-icon="mdi-file-import" @click="openImport">Import</v-btn>
      <v-menu>
        <template #activator="{ props }">
          <v-btn v-bind="props" variant="text" prepend-icon="mdi-view-grid-plus">Presets</v-btn>
        </template>
        <v-list>
          <v-list-item @click="loadTemplate('minimal')">Minimal</v-list-item>
          <v-list-item @click="loadTemplate('icfi')">ICFI</v-list-item>
          <v-list-item @click="loadTemplate('bmb')">BMB</v-list-item>
        </v-list>
      </v-menu>
    </v-toolbar-items>
    <v-spacer></v-spacer>

    <v-btn
      variant="text"
      prepend-icon="mdi-open-in-new"
      :href="FEEDBACK_LINK"
      target="_blank"
      :disabled="FEEDBACK_LINK === '#'"
    >
      Feedback (TBD)
    </v-btn>

    <input ref="fileInput" type="file" accept="application/json" class="d-none" @change="onImport" />
  </v-app-bar>

  <v-main class="pt-12 app-background">
    <v-container fluid class="py-8">
      <v-row class="mb-4">
        <v-col cols="12">
          <div class="d-flex justify-space-between align-center page-header">
            <div>
              <h1 class="text-h5 mb-1">Analysis recipe</h1>
              <p class="text-body-2 text-medium-emphasis mb-0">
                Configure your columns, rules, and insights on the left. Upload your data and run the report on the right.
              </p>
            </div>
          </div>
        </v-col>
      </v-row>

      <v-row class="mb-6">
        <v-col cols="12">
          <div class="mb-2 section-label">Step 1 · Data &amp; run</div>

          <ActionsCard
            :input-file="inputFile"
            :bundle-name="bundleName"
            :is-running="isRunning"
            :error-message="errorMessage"
            @update:inputFile="(v) => (inputFile = v)"
            @update:bundleName="(v) => (bundleName = v)"
            @importHeaders="importHeadersFromFile"
            @runReport="runReport"
            @exportRecipe="exportRecipe"
            @openImport="openImport"
            @clearRecipe="clearRecipe"
            @openLogicReference="openDefinitionsDialog"
            @downloadLogicReference="downloadDefinitions"
          />
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12" md="8">
          <div class="mb-2 section-label">Step 2 · Columns &amp; rules</div>

          <ColumnHeadersCard :column-headers="store.recipe.columnHeaders" @setHeaders="onSetHeaders" />

          <AddRuleCard
            :column-headers="store.recipe.columnHeaders"
            :operations="operations"
            @add="onAddRule"
          />

          <RulesCard
            :rules="store.rules"
            :column-headers="store.recipe.columnHeaders"
            @updateRule="update"
            @removeRule="remove"
          />

          <UnderstandLogicCard />
        </v-col>

        <v-col cols="12" md="4" class="right-column">
          <div class="mb-2 section-label">Step 3 · Insights &amp; advanced</div>

          <CorrelationsCard
            :column-headers="store.recipe.columnHeaders"
            v-model:sources="correlationSources"
            v-model:targets="correlationTargets"
            v-model:threshold="correlationThreshold"
            v-model:enabled="correlationEnabled"
            v-model:extraBlocks="extraCorrelationBlocks"
          />

          <CrosstabsCard
            :column-headers="store.recipe.columnHeaders"
            v-model:sources="crosstabSources"
            v-model:targets="crosstabTargets"
            v-model:enabled="crosstabEnabled"
            v-model:extraBlocks="extraCrosstabBlocks"
          />

          <AdvancedAnalysesCard
            :column-headers="store.recipe.columnHeaders"
            :frequencies="frequencies"
            :time-series-metrics="timeSeriesMetrics"
            v-model:keyDriver="keyDriver"
            v-model:outlierDetection="outlierDetection"
            v-model:summaryStats="summaryStats"
            v-model:timeSeries="timeSeries"
          />
        </v-col>
      </v-row>
    </v-container>
  </v-main>

  <LogicReference ref="logicReference" :api-base-url="API_BASE_URL" @error="(m) => (errorMessage = m)" />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRecipeStore } from '../stores/recipe'
import type { Operation, Rule, CorrelationBlockConfig, CrosstabBlockConfig } from '../types/recipe'
import { normalizeHeaderName } from '../utils/normalize'
import { useReportSubmission } from '../composables/useReportSubmission'
import ColumnHeadersCard from '../components/recipe/ColumnHeadersCard.vue'
import AddRuleCard from '../components/recipe/AddRuleCard.vue'
import RulesCard from '../components/recipe/RulesCard.vue'
import CorrelationsCard from '../components/insights/CorrelationsCard.vue'
import CrosstabsCard from '../components/insights/CrosstabsCard.vue'
import AdvancedAnalysesCard from '../components/advanced/AdvancedAnalysesCard.vue'
import UnderstandLogicCard from '../components/help/UnderstandLogicCard.vue'
import ActionsCard from '../components/actions/ActionsCard.vue'
import LogicReference from '../components/actions/LogicReference.vue'


const FEEDBACK_LINK: string = import.meta.env.VITE_FEEDBACK_LINK || '#'
const store = useRecipeStore()

const inputFile = ref<File | null>(null)
// Prefer env-driven configuration; fall back to same-origin in production builds.
const API_BASE_URL: string = String(import.meta.env.VITE_API_BASE_URL || `${window.location.origin}/api`)
const isRunning = ref(false)
const errorMessage = ref<string | null>(null)
const bundleName = ref<string>('generated_report')

const logicReference = ref<InstanceType<typeof LogicReference> | null>(null)

const operations: Operation[] = ['distribution', 'valueCount', 'duplicate', 'average', 'sum', 'median', 'clean']
const frequencies = ['D', 'W', 'ME', 'QE', 'YE']
const timeSeriesMetrics: Array<'sum' | 'average' | 'count'> = ['sum', 'average', 'count']

const keyDriver = computed({
  get: () => store.recipe.keyDriver!,
  set: (val) => {
    store.recipe.keyDriver = val
  },
})

const outlierDetection = computed({
  get: () => store.recipe.outlierDetection!,
  set: (val) => {
    store.recipe.outlierDetection = val
  },
})

const summaryStats = computed({
  get: () => store.recipe.summaryStats!,
  set: (val) => {
    store.recipe.summaryStats = val
  },
})

const timeSeries = computed({
  get: () => store.recipe.timeSeries!,
  set: (val) => {
    store.recipe.timeSeries = val
  },
})

function onSetHeaders(headers: string[]) {
  store.setColumnHeaders(headers)
}

function onAddRule(payload: { column: string; operation: Operation }) {
  const normalizedColumn = normalizeHeaderName(payload.column)
  store.addRule(normalizedColumn, payload.operation)
}

function update(r: Rule) {
  store.updateRule(r.id, r)
}
function remove(id: string) {
  store.removeRule(id)
}


// Insights state — all backed by the store so changes are persisted immediately
// and the exported recipe is always in sync without a manual flush step.
const correlationSources = computed({
  get: () => store.recipe.insights.sources,
  set: (v: string[]) => store.patchInsights({ sources: v }),
})
const correlationTargets = computed({
  get: () => store.recipe.insights.targets,
  set: (v: string[]) => store.patchInsights({ targets: v }),
})
const correlationThreshold = computed({
  get: () => store.recipe.insights.threshold,
  set: (v: number) => store.patchInsights({ threshold: v }),
})
const correlationEnabled = computed({
  get: () => store.recipe.insights.enabled,
  set: (v: boolean) => store.patchInsights({ enabled: v }),
})
const crosstabSources = computed({
  get: () => store.recipe.insights.crosstabSources,
  set: (v: string[]) => store.patchInsights({ crosstabSources: v }),
})
const crosstabTargets = computed({
  get: () => store.recipe.insights.crosstabTargets,
  set: (v: string[]) => store.patchInsights({ crosstabTargets: v }),
})
const crosstabEnabled = computed({
  get: () => store.recipe.insights.crosstabEnabled,
  set: (v: boolean) => store.patchInsights({ crosstabEnabled: v }),
})
const extraCorrelationBlocks = computed({
  get: () => store.recipe.insights.extraCorrelationBlocks,
  set: (v: CorrelationBlockConfig[]) => store.patchInsights({ extraCorrelationBlocks: v }),
})
const extraCrosstabBlocks = computed({
  get: () => store.recipe.insights.extraCrosstabBlocks,
  set: (v: CrosstabBlockConfig[]) => store.patchInsights({ extraCrosstabBlocks: v }),
})

const fileInput = ref<HTMLInputElement | null>(null)
function openImport() {
  fileInput.value?.click()
}

function onImport(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || !files[0]) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      store.importRecipe(String(reader.result))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Invalid recipe.json')
    }
  }
  reader.readAsText(files[0])
}

function exportRecipe() {
  store.exportRecipe()
}


function defaultRuleOptions() {
  return {
    delimiter: '',
    separateNodes: false,
    rootOnly: false,
    excludeKeys: [] as string[],
    value: '',
    filterColumn: '',
    filterValue: '',
    filterOperator: 'eq' as const,
  }
}

function loadTemplate(name: string) {
  if (name === 'minimal') {
    store.$patch({ recipe: { ...store.recipe, rules: [] } })
    return
  }

  if (name === 'icfi') {
    store.$patch({
      recipe: {
        ...store.recipe,
        rules: [
          { id: cryptoRandom(), column: 'category', operation: 'distribution', options: defaultRuleOptions(), enabled: true },
          { id: cryptoRandom(), column: 'dup_col', operation: 'duplicate', options: defaultRuleOptions(), enabled: true },
        ],
      },
    })
    return
  }

  if (name === 'bmb') {
    store.$patch({
      recipe: {
        ...store.recipe,
        rules: [{ id: cryptoRandom(), column: 'score', operation: 'average', options: defaultRuleOptions(), enabled: true }],
      },
    })
  }
}

function cryptoRandom() {
  return crypto.randomUUID()
}

const { runReport } = useReportSubmission(store, inputFile, bundleName, isRunning, errorMessage)

function clearRecipe() {
  store.resetRecipe()
  bundleName.value = 'generated_report'
  inputFile.value = null
  errorMessage.value = null
}


function openDefinitionsDialog() {
  logicReference.value?.open()
}

function downloadDefinitions() {
  logicReference.value?.download()
}

async function importHeadersFromFile() {
  if (!inputFile.value) {
    errorMessage.value = 'Please select a data file before importing headers.'
    return
  }

  try {
    errorMessage.value = null
    const formData = new FormData()
    formData.append('file', inputFile.value)

    const resp = await fetch(`${API_BASE_URL}/headers`, { method: 'POST', body: formData })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

    const data = await resp.json()
    const headers = Array.isArray((data as any).headers) ? (data as any).headers.map((h: unknown) => normalizeHeaderName(String(h))) : []

    if (!headers.length) throw new Error('No headers returned from server')

    store.setColumnHeaders(headers)
  } catch (err) {
    console.error('Failed to import headers from file:', err)
    errorMessage.value = 'Failed to import headers from file. Please check the API and try again.'
  }
}
</script>
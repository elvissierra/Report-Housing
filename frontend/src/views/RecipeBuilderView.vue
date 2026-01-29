



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
import type { Operation, Rule } from '../types/recipe'
import { submitReport } from '../services/api'
import type { AnalysisRequest, CustomAnalysis, CrosstabAnalysis, CorrelationAnalysis, Filter, Transformation } from '../services/api'
import axios from 'axios'
import ColumnHeadersCard from '../components/recipe/ColumnHeadersCard.vue'
import AddRuleCard from '../components/recipe/AddRuleCard.vue'
import RulesCard from '../components/recipe/RulesCard.vue'
import CorrelationsCard from '../components/insights/CorrelationsCard.vue'
import CrosstabsCard from '../components/insights/CrosstabsCard.vue'
import AdvancedAnalysesCard from '../components/advanced/AdvancedAnalysesCard.vue'
import UnderstandLogicCard from '../components/help/UnderstandLogicCard.vue'
import ActionsCard from '../components/actions/ActionsCard.vue'
import LogicReference from '../components/actions/LogicReference.vue'

interface CorrelationBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean
}

interface CrosstabBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  enabled: boolean
}

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
const frequencies = ['D', 'W', 'M']
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

function normalizeHeaderName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/[^\w]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
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


// Correlations
const correlationSources = ref<string[]>(store.recipe.insights.sources ?? [])
const correlationTargets = ref<string[]>(store.recipe.insights.targets ?? [])
const correlationThreshold = ref<number>(store.recipe.insights.threshold ?? 0.2)
const correlationEnabled = ref<boolean>(store.recipe.insights.enabled ?? true)

// Crosstabs
const crosstabSources = ref<string[]>(store.recipe.insights.crosstabSources ?? [])
const crosstabTargets = ref<string[]>(store.recipe.insights.crosstabTargets ?? [])
const crosstabEnabled = ref<boolean>(store.recipe.insights.crosstabEnabled ?? true)

const extraCorrelationBlocks = ref<CorrelationBlockConfig[]>([])
const extraCrosstabBlocks = ref<CrosstabBlockConfig[]>([])

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
    } catch {
      alert('Invalid recipe.json')
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
  try {
    return crypto.randomUUID().slice(0, 8)
  } catch {
    return Math.random().toString(36).slice(2, 10)
  }
}

function buildTransformationsForRule(r: Rule): Transformation[] {
  const transformations: Transformation[] = []
  transformations.push({ action: 'strip_whitespace', params: {} })

  if (r.options.delimiter) {
    if (r.options.separateNodes) {
      transformations.push({ action: 'split_and_explode', params: { delimiter: r.options.delimiter } })
    } else if (r.options.rootOnly) {
      transformations.push({ action: 'to_root_node', params: { delimiter: r.options.delimiter } })
    }
  }

  if (r.operation === 'average' || r.operation === 'sum' || r.operation === 'median') {
    transformations.push({ action: 'to_numeric', params: {} })
  }

  return transformations
}

function buildFiltersForRule(r: Rule): Filter[] {
  const filters: Filter[] = []

  const filterColumn = r.options.filterColumn
  const filterValue = r.options.filterValue
  const operator = r.options.filterOperator || 'eq'

  if (filterColumn && filterValue) {
    filters.push({ column: filterColumn, operator, value: filterValue })
  }

  return filters
}

function buildPostFiltersForRule(r: Rule): Filter[] {
  const postFilters: Filter[] = []

  if (r.options.excludeKeys && r.options.excludeKeys.length > 0) {
    postFilters.push({ column: r.column, operator: 'not_in', value: r.options.excludeKeys })
  }

  if (r.operation === 'valueCount' && r.options.value) {
    postFilters.push({ column: r.column, operator: 'eq', value: r.options.value })
  }

  return postFilters
}

function clearRecipe() {
  if (typeof (store as any).resetRecipe === 'function') {
    ;(store as any).resetRecipe()
    correlationSources.value = []
    correlationTargets.value = []
    correlationThreshold.value = store.recipe.insights.threshold ?? 0.2
    correlationEnabled.value = store.recipe.insights.enabled ?? true
    crosstabSources.value = []
    crosstabTargets.value = []
    crosstabEnabled.value = store.recipe.insights.crosstabEnabled ?? true
    extraCorrelationBlocks.value = []
    extraCrosstabBlocks.value = []
    bundleName.value = 'generated_report'
    inputFile.value = null
    errorMessage.value = null
  }
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

async function runReport() {
  if (!inputFile.value) {
    errorMessage.value = 'Please select a data file before running the report.'
    return
  }

  const customSteps: CustomAnalysis[] = store.rules
    .filter((r) => r.enabled)
    .map((r) => {
      let operation: CustomAnalysis['operation']

      switch (r.operation) {
        case 'average':
          operation = 'average'
          break
        case 'sum':
          operation = 'sum'
          break
        case 'median':
          operation = 'median'
          break
        case 'duplicate':
          operation = 'duplicate_count'
          break
        case 'distribution':
        case 'valueCount':
          operation = 'distribution'
          break
        case 'clean':
          operation = 'list_unique_values'
          break
        default:
          operation = 'distribution'
      }

      const transformations = buildTransformationsForRule(r)
      const filters = buildFiltersForRule(r)
      const postFilters = buildPostFiltersForRule(r)

      const step: CustomAnalysis = {
        type: 'custom',
        output_name: `${r.column} — ${r.operation}`,
        filters,
        group_by: Array.isArray((r as any).group_by) ? (r as any).group_by : [],
        target_columns: [r.column],
        transformations,
        operation,
        post_transformation_filters: postFilters,
      }

      return step
    })

  store.setInsights(
    correlationSources.value,
    correlationTargets.value,
    correlationThreshold.value,
    correlationEnabled.value,
    crosstabSources.value,
    crosstabTargets.value,
    crosstabEnabled.value,
  )

  const insight = store.recipe.insights
  const analysisSteps: AnalysisRequest['analysis_steps'] = [...customSteps]

  if (insight.enabled) {
    const srcs = (insight.sources || []).filter(Boolean)
    const tgts = (insight.targets || []).filter(Boolean)

    const correlationSteps: CorrelationAnalysis[] = []

    if (srcs.length && tgts.length) {
      for (const src of srcs) {
        for (const tgt of tgts) {
          if (!src || !tgt || src === tgt) continue
          correlationSteps.push({
            type: 'correlation',
            output_name: `Correlation: ${src} vs ${tgt}`,
            filters: [],
            group_by: [],
            columns: [src, tgt],
            threshold: insight.threshold ?? 0.2,
          })
        }
      }
    }

    analysisSteps.push(...correlationSteps)
  }

  for (const block of extraCorrelationBlocks.value) {
    if (!block.enabled) continue

    const srcs = (block.sources || []).filter(Boolean)
    const tgts = (block.targets || []).filter(Boolean)
    if (!srcs.length || !tgts.length) continue

    for (const src of srcs) {
      for (const tgt of tgts) {
        if (!src || !tgt || src === tgt) continue
        analysisSteps.push({
          type: 'correlation',
          output_name: `Correlation (extra): ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          columns: [src, tgt],
          threshold: block.threshold ?? insight.threshold ?? 0.2,
        })
      }
    }
  }

  if (insight.crosstabEnabled && insight.crosstabSources.length > 0 && insight.crosstabTargets.length > 0) {
    const crosstabSteps: CrosstabAnalysis[] = []

    for (const src of insight.crosstabSources) {
      for (const tgt of insight.crosstabTargets) {
        if (!src || !tgt || src === tgt) continue
        crosstabSteps.push({
          type: 'crosstab',
          output_name: `Crosstab: ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          index_column: src,
          column_to_compare: tgt,
          column_transformations: [],
          show_percentages: 'none',
        })
      }
    }

    analysisSteps.push(...crosstabSteps)
  }

  for (const block of extraCrosstabBlocks.value) {
    if (!insight.crosstabEnabled) continue
    if (!block.enabled || block.sources.length === 0 || block.targets.length === 0) continue

    const srcs = block.sources.filter(Boolean)
    const tgts = block.targets.filter(Boolean)

    const extraCrosstabSteps: CrosstabAnalysis[] = []

    for (const src of srcs) {
      for (const tgt of tgts) {
        if (!src || !tgt || src === tgt) continue
        extraCrosstabSteps.push({
          type: 'crosstab',
          output_name: `Crosstab: ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          index_column: src,
          column_to_compare: tgt,
          column_transformations: [],
          show_percentages: 'none',
        })
      }
    }

    analysisSteps.push(...extraCrosstabSteps)
  }

  const kdConfig = store.recipe.keyDriver
  if (kdConfig && kdConfig.enabled && kdConfig.target_variable && kdConfig.feature_columns.length > 0) {
    analysisSteps.push({
      type: 'key_driver',
      output_name: `Key Drivers — ${kdConfig.target_variable}`,
      filters: [],
      group_by: [],
      target_variable: kdConfig.target_variable,
      feature_columns: kdConfig.feature_columns,
      categorical_features: kdConfig.categorical_features ?? [],
      include_intercept: kdConfig.include_intercept,
      p_value_threshold: kdConfig.p_value_threshold,
    })
  }

  const outlierConfig = store.recipe.outlierDetection
  if (outlierConfig && outlierConfig.enabled && outlierConfig.target_columns.length > 0) {
    analysisSteps.push({
      type: 'outlier_detection',
      output_name: 'Outliers',
      filters: [],
      group_by: [],
      target_columns: outlierConfig.target_columns,
      method: outlierConfig.method,
      threshold: outlierConfig.threshold,
    })
  }

  const statsConfig = store.recipe.summaryStats
  if (statsConfig && statsConfig.enabled && statsConfig.numeric_columns.length > 0) {
    analysisSteps.push({
      type: 'summary_stats',
      output_name: 'Summary Statistics',
      filters: [],
      group_by: [],
      numeric_columns: statsConfig.numeric_columns,
      column_transformations: [],
    })
  }

  const tsConfig = store.recipe.timeSeries
  if (tsConfig && tsConfig.enabled && tsConfig.date_column && tsConfig.metric_column) {
    analysisSteps.push({
      type: 'time_series',
      output_name: 'Time Series',
      filters: [],
      group_by: [],
      date_column: tsConfig.date_column,
      metric_column: tsConfig.metric_column,
      frequency: tsConfig.frequency,
      metric: tsConfig.metric,
    })
  }

  const outputBaseName = bundleName.value?.trim() || 'generated_report'

  const request: AnalysisRequest = {
    output_filename: outputBaseName,
    analysis_steps: analysisSteps,
  }

  isRunning.value = true
  errorMessage.value = null

  try {
    const blob = await submitReport(inputFile.value, request)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${outputBaseName}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error(err)
    if (axios.isAxiosError(err) && err.response?.data instanceof Blob) {
      try {
        const text = await err.response.data.text()
        console.error('Server error body:', text)
      } catch (blobErr) {
        console.error('Failed to read error blob', blobErr)
      }
    }
    errorMessage.value = 'Failed to generate report. Please try again.'
  } finally {
    isRunning.value = false
  }
}
</script>
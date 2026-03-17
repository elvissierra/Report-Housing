import type { Ref } from 'vue'
import axios from 'axios'
import type { useRecipeStore } from '../stores/recipe'
import type { Operation, Rule } from '../types/recipe'
import { submitReport } from '../services/api'
import type {
  AnalysisRequest,
  CustomAnalysis,
  CrosstabAnalysis,
  CorrelationAnalysis,
  KeyDriverAnalysis,
  OutlierDetectionAnalysis,
  SummaryStatsAnalysis,
  TimeSeriesAnalysis,
  Filter,
  Transformation,
} from '../services/api'

// Maps every frontend UI operation label to the corresponding backend wire value.
// Using a typed Record ensures TypeScript will flag any unmapped Operation at compile time.
const OPERATION_MAP: Record<Operation, CustomAnalysis['operation']> = {
  average: 'average',
  sum: 'sum',
  median: 'median',
  duplicate: 'duplicate_count',
  distribution: 'distribution',
  valueCount: 'distribution',
  clean: 'list_unique_values',
}

function buildTransformations(r: Rule): Transformation[] {
  // 1. Always strip whitespace first so subsequent scripts work on clean values.
  const out: Transformation[] = [{ action: 'strip_whitespace', params: {} }]

  // 2. User-selected pre-processing scripts, in selection order.
  //    deduplicate_within_cell uses the rule's delimiter (defaults to '|' on backend).
  for (const script of r.customScripts ?? []) {
    if (script === 'remove_special_chars') {
      out.push({ action: 'remove_special_chars', params: {} })
    } else if (script === 'deduplicate_within_cell') {
      out.push({
        action: 'deduplicate_within_cell',
        params: r.options.delimiter ? { delimiter: r.options.delimiter } : {},
      })
    }
  }

  // 3. Structural transforms (split/root) run after per-cell cleanup.
  if (r.options.delimiter) {
    if (r.options.separateNodes) {
      out.push({ action: 'split_and_explode', params: { delimiter: r.options.delimiter } })
    } else if (r.options.rootOnly) {
      out.push({ action: 'to_root_node', params: { delimiter: r.options.delimiter } })
    }
  }

  // 4. Numeric coercion last, only when the operation needs it.
  if (r.operation === 'average' || r.operation === 'sum' || r.operation === 'median') {
    out.push({ action: 'to_numeric', params: {} })
  }

  return out
}

function buildFilters(r: Rule): Filter[] {
  const { filterColumn, filterValue, filterOperator } = r.options
  if (filterColumn && filterValue) {
    return [{ column: filterColumn, operator: filterOperator ?? 'eq', value: filterValue }]
  }
  return []
}

function buildPostFilters(r: Rule): Filter[] {
  const out: Filter[] = []
  if (r.options.excludeKeys?.length) {
    out.push({ column: r.column, operator: 'not_in', value: r.options.excludeKeys })
  }
  if (r.operation === 'valueCount' && r.options.value) {
    out.push({ column: r.column, operator: 'eq', value: r.options.value })
  }
  return out
}

function buildCustomSteps(rules: Rule[]): CustomAnalysis[] {
  return rules
    .filter((r) => r.enabled)
    .map((r) => ({
      type: 'custom' as const,
      output_name: r.label?.trim() || `${r.column} — ${r.operation}`,
      filters: buildFilters(r),
      group_by: Array.isArray(r.group_by) ? r.group_by : [],
      target_columns: [r.column],
      transformations: buildTransformations(r),
      operation: OPERATION_MAP[r.operation],
      post_transformation_filters: buildPostFilters(r),
    }))
}

type Store = ReturnType<typeof useRecipeStore>

function buildAnalysisRequest(store: Store, outputBaseName: string): AnalysisRequest {
  const insight = store.recipe.insights
  const steps: AnalysisRequest['analysis_steps'] = [...buildCustomSteps(store.rules)]

  // Correlation steps
  if (insight.enabled) {
    const srcs = insight.sources.filter(Boolean)
    const tgts = insight.targets.filter(Boolean)
    for (const src of srcs) {
      for (const tgt of tgts) {
        if (src === tgt) continue
        const step: CorrelationAnalysis = {
          type: 'correlation',
          output_name: `Correlation: ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          columns: [src, tgt],
          threshold: insight.threshold ?? 0.2,
        }
        steps.push(step)
      }
    }
  }

  for (const block of insight.extraCorrelationBlocks ?? []) {
    if (!block.enabled) continue
    const srcs = block.sources.filter(Boolean)
    const tgts = block.targets.filter(Boolean)
    if (!srcs.length || !tgts.length) continue
    for (const src of srcs) {
      for (const tgt of tgts) {
        if (src === tgt) continue
        const step: CorrelationAnalysis = {
          type: 'correlation',
          output_name: `Correlation (extra): ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          columns: [src, tgt],
          threshold: block.threshold ?? insight.threshold ?? 0.2,
        }
        steps.push(step)
      }
    }
  }

  // Crosstab steps
  if (insight.crosstabEnabled) {
    const srcs = insight.crosstabSources.filter(Boolean)
    const tgts = insight.crosstabTargets.filter(Boolean)
    for (const src of srcs) {
      for (const tgt of tgts) {
        if (src === tgt) continue
        const step: CrosstabAnalysis = {
          type: 'crosstab',
          output_name: `Crosstab: ${src} vs ${tgt}`,
          filters: [],
          group_by: [],
          index_column: src,
          column_to_compare: tgt,
          column_transformations: [],
          show_percentages: 'none',
        }
        steps.push(step)
      }
    }

    for (const block of insight.extraCrosstabBlocks ?? []) {
      if (!block.enabled || !block.sources.length || !block.targets.length) continue
      const srcs = block.sources.filter(Boolean)
      const tgts = block.targets.filter(Boolean)
      for (const src of srcs) {
        for (const tgt of tgts) {
          if (src === tgt) continue
          const step: CrosstabAnalysis = {
            type: 'crosstab',
            output_name: `Crosstab: ${src} vs ${tgt}`,
            filters: [],
            group_by: [],
            index_column: src,
            column_to_compare: tgt,
            column_transformations: [],
            show_percentages: 'none',
          }
          steps.push(step)
        }
      }
    }
  }

  // Advanced analysis steps
  const kd = store.recipe.keyDriver
  if (kd?.enabled && kd.target_variable && kd.feature_columns.length > 0) {
    const step: KeyDriverAnalysis = {
      type: 'key_driver',
      output_name: `Key Drivers — ${kd.target_variable}`,
      filters: [],
      group_by: [],
      target_variable: kd.target_variable,
      feature_columns: kd.feature_columns,
      categorical_features: kd.categorical_features ?? [],
      include_intercept: kd.include_intercept,
      p_value_threshold: kd.p_value_threshold,
    }
    steps.push(step)
  }

  const od = store.recipe.outlierDetection
  if (od?.enabled && od.target_columns.length > 0) {
    const step: OutlierDetectionAnalysis = {
      type: 'outlier_detection',
      output_name: 'Outliers',
      filters: [],
      group_by: [],
      target_columns: od.target_columns,
      method: od.method,
      threshold: od.threshold,
    }
    steps.push(step)
  }

  const ss = store.recipe.summaryStats
  if (ss?.enabled && ss.numeric_columns.length > 0) {
    const step: SummaryStatsAnalysis = {
      type: 'summary_stats',
      output_name: 'Summary Statistics',
      filters: [],
      group_by: [],
      numeric_columns: ss.numeric_columns,
      column_transformations: [],
    }
    steps.push(step)
  }

  const ts = store.recipe.timeSeries
  if (ts?.enabled && ts.date_column && ts.metric_column) {
    const step: TimeSeriesAnalysis = {
      type: 'time_series',
      output_name: 'Time Series',
      filters: [],
      group_by: [],
      date_column: ts.date_column,
      metric_column: ts.metric_column,
      frequency: ts.frequency,
      metric: ts.metric,
    }
    steps.push(step)
  }

  return { output_filename: outputBaseName, analysis_steps: steps }
}

export function useReportSubmission(
  store: Store,
  inputFile: Ref<File | null>,
  bundleName: Ref<string>,
  isRunning: Ref<boolean>,
  errorMessage: Ref<string | null>,
) {
  async function runReport() {
    if (!inputFile.value) {
      errorMessage.value = 'Please select a data file before running the report.'
      return
    }

    const outputBaseName = bundleName.value?.trim() || 'generated_report'
    const request = buildAnalysisRequest(store, outputBaseName)

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

  return { runReport }
}

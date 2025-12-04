function normalizeHeaderName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/[^\w]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
}

import { defineStore } from 'pinia'
import type {
  Recipe,
  Rule,
  Operation,
  KeyDriverConfig,
  OutlierDetectionConfig,
  SummaryStatsConfig,
  TimeSeriesConfig,
} from '../types/recipe'

function normalizeRecipe(recipe: Recipe): Recipe {
  const normalizedHeaders = recipe.columnHeaders.map(normalizeHeaderName)

  const normalizedRules = recipe.rules.map((r) => ({
    ...r,
    column: normalizeHeaderName(r.column),
  }))

  const normalizedKeyDriver: KeyDriverConfig = {
    enabled: recipe.keyDriver?.enabled ?? false,
    target_variable: recipe.keyDriver?.target_variable
      ? normalizeHeaderName(recipe.keyDriver.target_variable)
      : null,
    feature_columns: (recipe.keyDriver?.feature_columns ?? []).map(normalizeHeaderName),
    categorical_features: (recipe.keyDriver?.categorical_features ?? []).map(normalizeHeaderName),
    include_intercept: recipe.keyDriver?.include_intercept ?? true,
    p_value_threshold: recipe.keyDriver?.p_value_threshold ?? 0.05,
  }

  const normalizedOutlierDetection: OutlierDetectionConfig = {
    enabled: recipe.outlierDetection?.enabled ?? false,
    target_columns: (recipe.outlierDetection?.target_columns ?? []).map(normalizeHeaderName),
    method: recipe.outlierDetection?.method ?? 'iqr',
    threshold: recipe.outlierDetection?.threshold ?? 1.5,
  }

  const normalizedSummaryStats: SummaryStatsConfig = {
    enabled: recipe.summaryStats?.enabled ?? false,
    numeric_columns: (recipe.summaryStats?.numeric_columns ?? []).map(normalizeHeaderName),
  }

  const normalizedTimeSeries: TimeSeriesConfig = {
    enabled: recipe.timeSeries?.enabled ?? false,
    date_column: recipe.timeSeries?.date_column
      ? normalizeHeaderName(recipe.timeSeries.date_column)
      : null,
    metric_column: recipe.timeSeries?.metric_column
      ? normalizeHeaderName(recipe.timeSeries.metric_column)
      : null,
    frequency: recipe.timeSeries?.frequency ?? 'D',
    metric: recipe.timeSeries?.metric ?? 'sum',
  }

  const normalizedInsights = {
    sources: recipe.insights.sources.map(normalizeHeaderName),
    targets: recipe.insights.targets.map(normalizeHeaderName),
    threshold: recipe.insights.threshold,
    enabled: recipe.insights.enabled ?? true,
    crosstabSources: (recipe.insights as any).crosstabSources
      ? (recipe.insights as any).crosstabSources.map(normalizeHeaderName)
      : [],
    crosstabTargets: (recipe.insights as any).crosstabTargets
      ? (recipe.insights as any).crosstabTargets.map(normalizeHeaderName)
      : [],
    crosstabEnabled: (recipe.insights as any).crosstabEnabled ?? true,
  }

  return {
    ...recipe,
    columnHeaders: normalizedHeaders,
    rules: normalizedRules,
    insights: normalizedInsights,
    keyDriver: normalizedKeyDriver,
    outlierDetection: normalizedOutlierDetection,
    summaryStats: normalizedSummaryStats,
    timeSeries: normalizedTimeSeries,
  }
}

const DEFAULT_RECIPE: Recipe = {
  version: '1',
  columnHeaders: [],
  rules: [],
  insights: {
    sources: [],
    targets: [],
    threshold: 0.2,
    enabled: true,
    crosstabSources: [],
    crosstabTargets: [],
    crosstabEnabled: true,
  },
  keyDriver: {
    enabled: false,
    target_variable: null,
    feature_columns: [],
    categorical_features: [],
    include_intercept: true,
    p_value_threshold: 0.05,
  },
  outlierDetection: {
    enabled: false,
    target_columns: [],
    method: 'iqr',
    threshold: 1.5,
  },
  summaryStats: {
    enabled: false,
    numeric_columns: [],
  },
  timeSeries: {
    enabled: false,
    date_column: null,
    metric_column: null,
    frequency: 'D',
    metric: 'sum',
  },
}

function uid() { return Math.random().toString(36).slice(2, 10) }

export const useRecipeStore = defineStore('recipe', {
  state: () => ({
    recipe: load()
  }),
  getters: {
    rules: (s) => s.recipe.rules,
    insights: (s) => s.recipe.insights,
  },
  actions: {
    setColumnHeaders(headers: string[]) {
      this.recipe.columnHeaders = headers
        .map(normalizeHeaderName)
        .filter(Boolean)
      this.recipe = normalizeRecipe(this.recipe)
      save(this.recipe)
    },
    addRule(column: string, operation: Operation) {
      const r: Rule = {
        id: uid(),
        column,
        operation,
        options: {
          delimiter: '',
          separateNodes: false,
          rootOnly: false,
          excludeKeys: [],
          value: '',
          filterColumn: '',
          filterValue: '',
          filterOperator: 'eq',
        },
        enabled: true,
      }
      this.recipe.rules.push(r)
      save(this.recipe)
    },
    updateRule(id: string, patch: Partial<Omit<Rule, 'id'>>) {
      const i = this.recipe.rules.findIndex(r => r.id === id)
      if (i >= 0) {
        this.recipe.rules[i] = { ...this.recipe.rules[i], ...patch } as Rule
        save(this.recipe)
      }
    },
    removeRule(id: string) {
      this.recipe.rules = this.recipe.rules.filter(r => r.id !== id)
      save(this.recipe)
    },
    reorderRule(id: string, toIndex: number) {
      const i = this.recipe.rules.findIndex(r => r.id === id)
      if (i < 0) return
      const [r] = this.recipe.rules.splice(i, 1)
      if (!r) return
      this.recipe.rules.splice(Math.max(0, Math.min(toIndex, this.recipe.rules.length)), 0, r)
      save(this.recipe)
    },
    setInsights(
      sources: string[],
      targets: string[],
      threshold: number,
      enabled: boolean | undefined,
      crosstabSources: string[],
      crosstabTargets: string[],
      crosstabEnabled: boolean | undefined,
    ) {
      this.recipe.insights = {
        sources,
        targets,
        threshold,
        enabled: enabled ?? this.recipe.insights.enabled ?? true,
        crosstabSources,
        crosstabTargets,
        crosstabEnabled: crosstabEnabled ?? this.recipe.insights.crosstabEnabled ?? true,
      }
      save(this.recipe)
    },
    exportRecipe(): string {
      const json = JSON.stringify(this.recipe, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'recipe.json'
      a.click()
      URL.revokeObjectURL(url)
      return json
    },
    importRecipe(jsonText: string) {
      const obj = JSON.parse(jsonText)
      this.recipe = normalizeRecipe(obj)
      save(this.recipe)
    },
    resetRecipe() {
      const fresh = normalizeRecipe(JSON.parse(JSON.stringify(DEFAULT_RECIPE)))
      this.recipe = fresh
      save(this.recipe)
    },
  }
})

function load(): Recipe {
  const raw = localStorage.getItem('recipe.v1')
  if (!raw) return DEFAULT_RECIPE
  const parsed = JSON.parse(raw) as Recipe
  return normalizeRecipe(parsed)
}
function save(r: Recipe) {
  localStorage.setItem('recipe.v1', JSON.stringify(r))
}

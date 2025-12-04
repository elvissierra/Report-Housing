export type Operation =
  | 'distribution'
  | 'valueCount'
  | 'duplicate'
  | 'average'
  | 'sum'
  | 'median'
  | 'clean'

export interface RuleOptions {
  delimiter?: string
  separateNodes?: boolean
  rootOnly?: boolean
  excludeKeys?: string[]
  value?: string
  filterColumn?: string
  filterValue?: string
  filterOperator?: 'eq'
}

export interface Rule {
  id: string
  column: string
  operation: Operation
  options: RuleOptions
  enabled: boolean
}

export interface Insights {
  // Correlation config
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean

  // Crosstab config
  crosstabSources: string[]
  crosstabTargets: string[]
  crosstabEnabled: boolean
}

export interface KeyDriverConfig {
  enabled: boolean
  target_variable: string | null
  feature_columns: string[]
  categorical_features: string[]
  include_intercept: boolean
  p_value_threshold: number
}

export interface OutlierDetectionConfig {
  enabled: boolean
  target_columns: string[]
  method: 'iqr' | 'z-score'
  threshold: number
}

export interface SummaryStatsConfig {
  enabled: boolean
  numeric_columns: string[]
}

export interface TimeSeriesConfig {
  enabled: boolean
  date_column: string | null
  metric_column: string | null
  frequency: 'D' | 'W' | 'M'
  metric: 'sum' | 'average' | 'count'
}

export interface Recipe {
  version: '1'
  columnHeaders: string[]
  rules: Rule[]
  insights: Insights
  keyDriver?: KeyDriverConfig
  outlierDetection?: OutlierDetectionConfig
  summaryStats?: SummaryStatsConfig
  timeSeries?: TimeSeriesConfig
}
export type Operation =
  | 'distribution'
  | 'valueCount'
  | 'duplicate'
  | 'average'
  | 'sum'
  | 'median'
  | 'clean'

export type FilterOperator = 'eq' | 'neq' | 'gt' | 'lt' | 'in' | 'not_in' | 'contains'

export type CustomScript = 'remove_special_chars' | 'deduplicate_within_cell'

export interface RuleOptions {
  delimiter?: string
  separateNodes?: boolean
  rootOnly?: boolean
  excludeKeys?: string[]
  value?: string
  filterColumn?: string
  filterValue?: string
  filterOperator?: FilterOperator
}

export interface Rule {
  id: string
  label: string
  column: string
  operation: Operation
  options: RuleOptions
  enabled: boolean
  group_by?: string[]
  customScripts: CustomScript[]
}

export interface CorrelationBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean
}

export interface CrosstabBlockConfig {
  id: string
  sources: string[]
  targets: string[]
  enabled: boolean
}

export interface Insights {
  // Correlation config
  sources: string[]
  targets: string[]
  threshold: number
  enabled: boolean
  extraCorrelationBlocks: CorrelationBlockConfig[]

  // Crosstab config
  crosstabSources: string[]
  crosstabTargets: string[]
  crosstabEnabled: boolean
  extraCrosstabBlocks: CrosstabBlockConfig[]
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
  frequency: 'D' | 'W' | 'ME' | 'QE' | 'YE'
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

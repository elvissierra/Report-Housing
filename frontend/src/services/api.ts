import axios from 'axios'

export type FilterOperator =
  | 'eq'
  | 'neq'
  | 'gt'
  | 'lt'
  | 'in'
  | 'not_in'
  | 'contains'

export interface Filter {
  column: string
  operator: FilterOperator
  value: string | number | (string | number)[]
}

export type TransformationAction =
  | 'split_and_explode'
  | 'to_root_node'
  | 'strip_whitespace'
  | 'to_numeric'
  | 'fill_na'

export interface Transformation {
  action: TransformationAction
  params?: Record<string, unknown>
}

export interface ColumnTransformation {
  column_name: string
  transformations: Transformation[]
}

export interface BaseAnalysis {
  output_name: string
  filters: Filter[]
  group_by: string[]
}

export type CustomOperation =
  | 'average'
  | 'sum'
  | 'median'
  | 'duplicate_count'
  | 'distribution'
  | 'list_unique_values'

export interface CustomAnalysis extends BaseAnalysis {
  type: 'custom'
  target_columns: string[]
  transformations: Transformation[]
  operation: CustomOperation
  post_transformation_filters: Filter[]
}

export interface CrosstabAnalysis extends BaseAnalysis {
  type: 'crosstab'
  index_column: string
  column_to_compare: string
  column_transformations: ColumnTransformation[]
  show_percentages: 'none' | 'index' | 'columns' | 'all'
}

export interface CorrelationAnalysis extends BaseAnalysis {
  type: 'correlation'
  columns: string[]
  threshold: number
}

export interface KeyDriverAnalysis extends BaseAnalysis {
  type: 'key_driver'
  target_variable: string
  feature_columns: string[]
  categorical_features: string[]
  include_intercept: boolean
  p_value_threshold: number
}

export interface OutlierDetectionAnalysis extends BaseAnalysis {
  type: 'outlier_detection'
  target_columns: string[]
  method: 'iqr' | 'z-score'
  threshold: number
}

export interface SummaryStatsAnalysis extends BaseAnalysis {
  type: 'summary_stats'
  numeric_columns: string[]
  column_transformations: ColumnTransformation[]
}

export interface TimeSeriesAnalysis extends BaseAnalysis {
  type: 'time_series'
  date_column: string
  metric_column: string
  frequency: string
  metric: 'sum' | 'average' | 'count'
}

export type AnalysisJob =
  | CustomAnalysis
  | CorrelationAnalysis
  | CrosstabAnalysis
  | KeyDriverAnalysis
  | OutlierDetectionAnalysis
  | SummaryStatsAnalysis
  | TimeSeriesAnalysis

export interface AnalysisRequest {
  output_filename: string
  analysis_steps: AnalysisJob[]
}

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || `${window.location.origin}/api`

const api = axios.create({
  baseURL: API_BASE_URL,
})

export async function submitReport(file: File, request: AnalysisRequest): Promise<Blob> {
  const form = new FormData()
  form.append('input_file', file)
  form.append('request_data_str', JSON.stringify(request))

  const res = await api.post('/generate-report/', form, {
    responseType: 'blob',
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return res.data
}
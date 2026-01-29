<template>
  <v-card class="mb-6 card-advanced" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center"><span>Advanced Analyses</span></v-card-title>
    <v-card-text>
      <v-expansion-panels multiple density="compact">
        <!-- Key Drivers -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <div class="d-flex align-center justify-space-between w-100">
              <span class="text-subtitle-2">Key Drivers</span>
              <v-switch
                :model-value="keyDriver.enabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
                @update:modelValue="(v) => updateKeyDriver({ enabled: Boolean(v) })"
              />
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-select
              :model-value="keyDriver.target_variable"
              :items="columnHeaders"
              label="Target variable"
              clearable
              hide-details
              density="compact"
              @update:modelValue="(v) => updateKeyDriver({ target_variable: (v as string) || '' })"
            />

            <v-select
              :model-value="keyDriver.feature_columns"
              :items="columnHeaders"
              label="Feature columns"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              class="mt-2"
              density="compact"
              @update:modelValue="(v) => updateKeyDriver({ feature_columns: (v as string[]) || [] })"
            />

            <v-select
              :model-value="keyDriver.categorical_features"
              :items="keyDriver.feature_columns"
              label="Categorical features"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              class="mt-2"
              density="compact"
              @update:modelValue="(v) => updateKeyDriver({ categorical_features: (v as string[]) || [] })"
            />

            <v-text-field
              :model-value="keyDriver.p_value_threshold"
              type="number"
              label="P-value threshold"
              step="0.01"
              min="0"
              max="1"
              density="compact"
              variant="outlined"
              hide-details
              class="mt-2"
              @update:modelValue="(v) => updateKeyDriver({ p_value_threshold: Number(v) })"
            />

            <div class="d-flex align-center justify-space-between mt-2">
              <span class="text-caption">Include intercept</span>
              <v-switch
                :model-value="keyDriver.include_intercept"
                inset
                density="compact"
                class="switch-sm"
                hide-details
                @update:modelValue="(v) => updateKeyDriver({ include_intercept: Boolean(v) })"
              />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Outliers -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <div class="d-flex align-center justify-space-between w-100">
              <span class="text-subtitle-2">Outliers</span>
              <v-switch
                :model-value="outlierDetection.enabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
                @update:modelValue="(v) => updateOutliers({ enabled: Boolean(v) })"
              />
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-select
              :model-value="outlierDetection.target_columns"
              :items="columnHeaders"
              label="Target columns"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              density="compact"
              @update:modelValue="(v) => updateOutliers({ target_columns: (v as string[]) || [] })"
            />

            <v-select
              :model-value="outlierDetection.method"
              :items="['iqr', 'z-score']"
              label="Method"
              hide-details
              density="compact"
              class="mt-2"
              @update:modelValue="(v) => updateOutliers({ method: (v as 'iqr' | 'z-score') || 'iqr' })"
            />

            <v-text-field
              :model-value="outlierDetection.threshold"
              type="number"
              label="Threshold"
              step="0.1"
              min="0"
              density="compact"
              variant="outlined"
              hide-details
              class="mt-2"
              @update:modelValue="(v) => updateOutliers({ threshold: Number(v) })"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Summary Stats -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <div class="d-flex align-center justify-space-between w-100">
              <span class="text-subtitle-2">Summary Stats</span>
              <v-switch
                :model-value="summaryStats.enabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
                @update:modelValue="(v) => updateSummary({ enabled: Boolean(v) })"
              />
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-select
              :model-value="summaryStats.numeric_columns"
              :items="columnHeaders"
              label="Numeric columns"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              density="compact"
              @update:modelValue="(v) => updateSummary({ numeric_columns: (v as string[]) || [] })"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Time Series -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <div class="d-flex align-center justify-space-between w-100">
              <span class="text-subtitle-2">Time Series</span>
              <v-switch
                :model-value="timeSeries.enabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
                @update:modelValue="(v) => updateTimeSeries({ enabled: Boolean(v) })"
              />
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-select
              :model-value="timeSeries.date_column"
              :items="columnHeaders"
              label="Date column"
              clearable
              hide-details
              density="compact"
              @update:modelValue="(v) => updateTimeSeries({ date_column: (v as string) || '' })"
            />

            <v-select
              :model-value="timeSeries.metric_column"
              :items="columnHeaders"
              label="Metric column"
              clearable
              hide-details
              class="mt-2"
              density="compact"
              @update:modelValue="(v) => updateTimeSeries({ metric_column: (v as string) || '' })"
            />

            <v-select
              :model-value="timeSeries.frequency"
              :items="frequencies"
              label="Frequency"
              hide-details
              class="mt-2"
              density="compact"
              @update:modelValue="(v) => updateTimeSeries({ frequency: (v as string) || frequencies[0] })"
            />

            <v-select
              :model-value="timeSeries.metric"
              :items="timeSeriesMetrics"
              label="Metric"
              hide-details
              class="mt-2"
              density="compact"
              @update:modelValue="(v) => updateTimeSeries({ metric: (v as 'sum' | 'average' | 'count') || 'sum' })"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
type TimeSeriesMetric = 'sum' | 'average' | 'count'

type KeyDriverConfig = {
  enabled: boolean
  target_variable: string | null
  feature_columns: string[]
  categorical_features: string[]
  include_intercept: boolean
  p_value_threshold: number
}

type OutlierConfig = {
  enabled: boolean
  target_columns: string[]
  method: 'iqr' | 'z-score'
  threshold: number
}

type SummaryStatsConfig = {
  enabled: boolean
  numeric_columns: string[]
}

type TimeSeriesConfig = {
  enabled: boolean
  date_column: string | null
  metric_column: string | null
  frequency: string
  metric: TimeSeriesMetric
}

const props = defineProps<{
  columnHeaders: string[]
  frequencies: string[]
  timeSeriesMetrics: TimeSeriesMetric[]
  keyDriver: KeyDriverConfig
  outlierDetection: OutlierConfig
  summaryStats: SummaryStatsConfig
  timeSeries: TimeSeriesConfig
}>()

const emit = defineEmits<{
  (e: 'update:keyDriver', v: KeyDriverConfig): void
  (e: 'update:outlierDetection', v: OutlierConfig): void
  (e: 'update:summaryStats', v: SummaryStatsConfig): void
  (e: 'update:timeSeries', v: TimeSeriesConfig): void
}>()

function updateKeyDriver(patch: Partial<KeyDriverConfig>) {
  emit('update:keyDriver', { ...props.keyDriver, ...patch })
}
function updateOutliers(patch: Partial<OutlierConfig>) {
  emit('update:outlierDetection', { ...props.outlierDetection, ...patch })
}
function updateSummary(patch: Partial<SummaryStatsConfig>) {
  emit('update:summaryStats', { ...props.summaryStats, ...patch })
}
function updateTimeSeries(patch: Partial<TimeSeriesConfig>) {
  emit('update:timeSeries', { ...props.timeSeries, ...patch })
}
</script>
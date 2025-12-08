<template>
  <v-app>
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
        Feedback (Quip)
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
                    @click="importHeadersFromFile"
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
                    @click="runReport"
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
                      v-model="bundleName"
                      label="Output Analysis Title"
                      placeholder="generated_report"
                      density="compact"
                      variant="outlined"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" md="7">
                    <v-file-input
                      v-model="inputFile"
                      label="Data file (CSV)"
                      accept=".csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                      density="compact"
                      variant="outlined"
                      hide-details
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
                      @click="exportRecipe"
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
                      @click="openImport"
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
                      @click="clearRecipe"
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
                      @click="openDefinitionsDialog"
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
                      @click="downloadDefinitions"
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
          </v-col>
        </v-row>
        <v-row>

        <v-col cols="12" md="8">
          <div class="mb-2 section-label">Step 2 · Columns &amp; rules</div>
          <v-card class="mb-6 card-headers" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
              <span>Column Headers (manual)</span>
              <v-tooltip
                text="These are the column names used throughout the analysis. Paste or type them here so rules, insights, and advanced analyses line up with your data file."
              >
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
                </template>
              </v-tooltip>
            </v-card-title>
            <v-card-text class="py-3">
              <v-textarea
                v-model="headersText"
                label="Known headers"
                placeholder="One per line or comma-separated"
                variant="outlined"
                rows="1"
                hide-details
                clearable
                density="compact"
                no-resize
                class="my-0 no-resize-ta"
                style="max-height: 48px;"
              />
              <div class="d-flex align-center mt-1">
                <div class="text-caption">
                  Paste or type your column headers, then click Apply. The active headers will appear below as tags.
                </div>
                <v-spacer />
                <v-btn
                  variant="tonal"
                  color="primary"
                  size="small"
                  @click="applyHeaders"
                >
                  Apply
                </v-btn>
              </div>
              <div
                v-if="store.recipe.columnHeaders.length"
                class="mt-2 d-flex flex-wrap ga-1"
              >
                <v-chip
                  v-for="h in store.recipe.columnHeaders"
                  :key="h"
                  size="small"
                  color="primary"
                  variant="tonal"
                  class="ma-1 text-capitalize"
                >
                  {{ h }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>
          <v-card class="mb-6 card-add-rule" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
              <span>Add Rule</span>
              <v-tooltip
                text="Rules run column-level analyses like distributions, averages, sums, and duplicate checks. Example: 'Category' + 'distribution' shows the share of each category as % and count."
              >
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
                </template>
              </v-tooltip>
            </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="newRule.column"
                  :items="store.recipe.columnHeaders"
                  label="Column"
                  clearable
                  hide-details
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="newRule.operation"
                  :items="operations"
                  label="Operation"
                  clearable
                  hide-details
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="2" class="d-flex align-center">
                <v-btn block color="primary" variant="elevated" :disabled="!newRule.column || !newRule.operation" @click="addRule">
                  Add
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
          </v-card>

          <v-card class="mb-6 card-rules" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
              <span>Rules</span>
              <v-tooltip
                text="Each rule targets a single column with an operation. 'separate' splits values on a delimiter, 'root only' keeps just the first part, and 'exclude keys' filters out specific values from the result."
              >
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
                </template>
              </v-tooltip>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <template v-if="store.rules.length">
                <v-card
                  v-for="r in store.rules"
                  :key="r.id"
                  class="mb-2 py-2 px-3"
                  variant="outlined"
                  elevation="0"
                  rounded="lg"
                >
                  <v-row dense class="align-center">
                    <v-col cols="12" md="8">
                      <div class="text-subtitle-1">
                        <strong>{{ r.column }}</strong> — {{ r.operation }}
                      </div>
                    </v-col>
                    <v-col cols="12" md="4" class="d-flex justify-end">
                      <v-btn icon="mdi-delete" variant="text" @click="remove(r.id)" />
                    </v-col>
                  </v-row>
                  <v-row dense class="align-center mb-1">
                    <v-col cols="12" md="6" class="d-flex ga-4 py-0">
                      <div class="d-flex flex-column align-center">
                        <v-switch
                          v-model="r.options.separateNodes"
                          inset
                          density="compact"
                          class="switch-sm"
                          hide-details
                          @update:modelValue="update(r)"
                        />
                        <div class="text-caption mt-1 nowrap">separate</div>
                      </div>
                      <div class="d-flex flex-column align-center">
                        <v-switch
                          v-model="r.options.rootOnly"
                          inset
                          density="compact"
                          class="switch-sm"
                          hide-details
                          @update:modelValue="update(r)"
                        />
                        <div class="text-caption mt-1 nowrap">root only</div>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6" class="d-flex justify-end align-center py-0">
                      <v-switch v-model="r.enabled" inset density="compact" class="switch-sm" @update:modelValue="update(r)" />
                      <span class="text-caption ml-2">enabled</span>
                    </v-col>
                  </v-row>
                  <v-row dense class="ga-2 mt-1">
                    <v-col cols="12" md="3" v-if="r.operation === 'valueCount'">
                      <v-text-field
                        v-model="r.options.value"
                        label="value"
                        density="compact"
                        clearable
                        @blur="update(r)"
                      />
                    </v-col>
                    <v-col cols="12" md="3">
                      <v-text-field
                        v-model="r.options.delimiter"
                        label="delimiter"
                        clearable
                        density="compact"
                        @blur="update(r)"
                      />
                    </v-col>
                    <v-col cols="12" md="3">
                      <v-combobox
                        v-model="excludeKeysText[r.id]"
                        label="exclude keys"
                        multiple
                        chips
                        :chip-props="{ size: 'small' }"
                        closable-chips
                        clearable
                        hide-details
                        density="compact"
                        @update:modelValue="applyExcludeChips(r)"
                      />
                    </v-col>
                  </v-row>
                                    <v-row dense class="ga-2 mt-1">
                    <v-col cols="12" md="4">
                      <v-select
                        v-model="r.options.filterColumn"
                        :items="store.recipe.columnHeaders"
                        label="filter column (optional)"
                        clearable
                        hide-details
                        density="compact"
                        @update:modelValue="update(r)"
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="r.options.filterValue"
                        label="filter value"
                        density="compact"
                        clearable
                        hide-details
                        @blur="update(r)"
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-select
                        v-model="r.options.filterOperator"
                        :items="['eq']"
                        label="operator"
                        clearable
                        hide-details
                        density="compact"
                        @update:modelValue="update(r)"
                      />
                    </v-col>
                  </v-row>
                  <v-row dense class="ga-2 mt-1">
                    <v-col cols="12">
                      <v-combobox
                        v-model="r.group_by"
                        :items="store.recipe.columnHeaders"
                        label="group by (optional)"
                        multiple
                        chips
                        closable-chips
                        clearable
                        hide-details
                        density="compact"
                        @update:modelValue="update(r)"
                      />
                    </v-col>
                  </v-row>
                </v-card>
              </template>
              <template v-else>
                <div class="text-medium-emphasis">No rules yet — add one above.</div>
              </template>
            </v-card-text>
          </v-card>

          <!-- Understand the Logic (Quick Examples) -->
          <v-card class="mb-6 card-understand" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
              <span>Understand the logic</span>
              <v-tooltip
                text="Quick examples of what each advanced tool does so you can pick the right one for your question."
              >
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
                </template>
              </v-tooltip>
            </v-card-title>
            <v-card-text class="text-caption">
              <div class="mb-2">
                <strong>Correlations</strong> – “How strongly do two columns move together?”
                <br />
                Example: <code>units_sold</code> vs <code>marketing_spend</code> (numeric–numeric, Pearson) or
                <code>units_sold</code> vs <code>product_category</code> (numeric–categorical, correlation ratio η).
              </div>
              <div class="mb-2">
                <strong>Crosstabs</strong> – “How does the mix of categories change across another field?”
                <br />
                Example: sources = <code>product_category</code>, targets = <code>region</code> to see category share by region.
              </div>
              <div class="mb-2">
                <strong>Key Drivers</strong> – “Which columns help explain my main metric?”
                <br />
                Example: Target = <code>sales_amount</code>, Features = <code>discount_rate</code>, <code>quantity</code>, <code>channel</code>.
              </div>
              <div class="mb-2">
                <strong>Outliers</strong> – “What values look unusually high or low?”
                <br />
                Example: Scan <code>sales_amount</code> and <code>discount_rate</code> with IQR = 1.5 to flag extreme rows.
              </div>
              <div class="mb-2">
                <strong>Summary Stats</strong> – “What does the distribution look like?”
                <br />
                Example: Show count, mean, and quartiles for <code>sales_amount</code>, <code>quantity</code>.
              </div>
              <div>
                <strong>Time Series</strong> – “How does this metric move over time?”
                <br />
                Example: Sum <code>sales_amount</code> by week using <code>order_date</code> as the time column.
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Right: Insights & Actions -->
        <v-col cols="12" md="4" class="right-column">
          <div class="mb-2 section-label">Step 3 · Insights &amp; advanced</div>

        <!-- Correlations -->
        <v-card class="mb-6 card-insights" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
            <span>Correlations</span>
            <v-tooltip
              text="Select columns to test for statistical correlation. Numeric pairs use Pearson; categorical pairs use Cramér's V; mixed numeric/categorical pairs use correlation ratio (eta)."
            >
              <template #activator="{ props }">
                <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
              </template>
            </v-tooltip>
          </v-card-title>
          <v-card-text>
            <v-combobox
              v-model="correlationSources"
              :items="store.recipe.columnHeaders"
              label="source columns"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              density="compact"
            />
            <v-combobox
              v-model="correlationTargets"
              :items="store.recipe.columnHeaders"
              label="target columns"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              class="mt-2"
              density="compact"
            />
            <v-slider
              v-model="correlationThreshold"
              :min="0"
              :max="1"
              :step="0.05"
              :show-ticks="true"
              class="mt-6"
            />
            <div class="text-caption">threshold: {{ correlationThreshold.toFixed(2) }}</div>
          
            <div class="d-flex align-center justify-space-between mt-2">
              <span class="text-caption">Correlations enabled</span>
              <v-switch
                v-model="correlationEnabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
              />
            </div>
            <v-divider class="my-3" />

              <div class="mt-1">
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="text-caption font-weight-medium">Additional correlation blocks</span>
                  <v-btn
                    size="x-small"
                    variant="text"
                    prepend-icon="mdi-plus"
                    @click="addCorrelationBlock"
                  >
                    Add
                  </v-btn>
                </div>
              
                <v-card
                  v-for="block in extraCorrelationBlocks"
                  :key="block.id"
                  class="mb-2 pa-2"
                  variant="outlined"
                  rounded="lg"
                >
                  <v-row dense>
                    <v-col cols="12">
                      <v-combobox
                        v-model="block.sources"
                        :items="store.recipe.columnHeaders"
                        label="source columns"
                        multiple
                        chips
                        closable-chips
                        clearable
                        hide-details
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="12">
                      <v-combobox
                        v-model="block.targets"
                        :items="store.recipe.columnHeaders"
                        label="target columns"
                        multiple
                        chips
                        closable-chips
                        clearable
                        hide-details
                        class="mt-2"
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="12">
                      <v-slider
                        v-model="block.threshold"
                        :min="0"
                        :max="1"
                        :step="0.05"
                        class="mt-2"
                      />
                      <div class="text-caption">
                        threshold: {{ block.threshold.toFixed(2) }}
                      </div>
                    </v-col>
                    <v-col cols="12" class="d-flex align-center justify-space-between">
                      <div class="d-flex align-center">
                        <span class="text-caption mr-2">Enabled</span>
                        <v-switch
                          v-model="block.enabled"
                          inset
                          density="compact"
                          class="switch-sm"
                          hide-details
                        />
                      </div>
                      <v-btn
                        icon="mdi-delete"
                        variant="text"
                        size="small"
                        @click="removeCorrelationBlock(block.id)"
                      />
                    </v-col>
                  </v-row>
                </v-card>
              </div>
          </v-card-text>
        </v-card>
        
        <!-- Crosstabs -->
        <v-card class="mb-6 card-crosstabs" variant="outlined" rounded="lg">
          <v-card-title class="d-flex align-center">
            <span>Crosstabs</span>
            <v-tooltip
              text="Crosstabs show how the distribution of one categorical column changes across another. Example: sources = 'category', targets = 'status'."
            >
              <template #activator="{ props }">
                <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
              </template>
            </v-tooltip>
          </v-card-title>
          <v-card-text>
            <v-combobox
              v-model="crosstabSources"
              :items="store.recipe.columnHeaders"
              label="sources"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              density="compact"
            />
            <v-combobox
              v-model="crosstabTargets"
              :items="store.recipe.columnHeaders"
              label="targets"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              class="mt-2"
              density="compact"
            />
            <div class="d-flex align-center justify-space-between mt-3">
              <span class="text-caption">Crosstabs enabled</span>
              <v-switch
                v-model="crosstabEnabled"
                inset
                density="compact"
                class="switch-sm"
                hide-details
              />
            </div>
            <v-divider class="my-3" />

              <div class="mt-1">
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="text-caption font-weight-medium">Additional crosstab blocks</span>
                  <v-btn
                    size="x-small"
                    variant="text"
                    prepend-icon="mdi-plus"
                    @click="addCrosstabBlock"
                  >
                    Add
                  </v-btn>
                </div>
              
                <v-card
                  v-for="block in extraCrosstabBlocks"
                  :key="block.id"
                  class="mb-2 pa-2"
                  variant="outlined"
                  rounded="lg"
                >
                  <v-row dense>
                    <v-col cols="12" md="6">
                      <v-combobox
                        v-model="block.sources"
                        :items="store.recipe.columnHeaders"
                        label="sources"
                        multiple
                        chips
                        closable-chips
                        clearable
                        hide-details
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-combobox
                        v-model="block.targets"
                        :items="store.recipe.columnHeaders"
                        label="targets"
                        multiple
                        chips
                        closable-chips
                        clearable
                        hide-details
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="12" class="d-flex align-center justify-space-between mt-2">
                      <div class="d-flex align-center">
                        <span class="text-caption mr-2">Enabled</span>
                        <v-switch
                          v-model="block.enabled"
                          inset
                          density="compact"
                          class="switch-sm"
                          hide-details
                        />
                      </div>
                      <v-btn
                        icon="mdi-delete"
                        variant="text"
                        size="small"
                        @click="removeCrosstabBlock(block.id)"
                      />
                    </v-col>
                  </v-row>
                </v-card>
              </div>
          </v-card-text>
        </v-card>

          <!-- Advanced Analyses -->
          <v-card class="mb-6 card-advanced" variant="outlined" rounded="lg">
            <v-card-title class="d-flex align-center">
              <span>Advanced Analyses</span>
              <v-tooltip
                text="These analyses look for deeper patterns: key drivers for a target metric, numeric outliers, summary statistics, and time-based trends."
              >
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="18" class="ml-1">mdi-help-circle-outline</v-icon>
                </template>
              </v-tooltip>
            </v-card-title>
            <v-card-text>
              <v-expansion-panels multiple density="compact">
                <!-- Key Drivers -->
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="d-flex align-center justify-space-between w-100">
                      <div class="d-flex align-center">
                        <span class="text-subtitle-2">Key Drivers</span>
                        <v-tooltip
                          text="Estimates which columns best explain a numeric target. Example: target = 'conversion_rate', features = 'channel' + 'region' shows which segments drive conversion up or down."
                        >
                          <template #activator="{ props }">
                            <v-icon v-bind="props" size="16" class="ml-1">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-switch
                        v-model="keyDriver.enabled"
                        inset
                        density="compact"
                        class="switch-sm"
                        hide-details
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select
                      v-model="keyDriver.target_variable"
                      :items="store.recipe.columnHeaders"
                      label="Target variable"
                      clearable
                      hide-details
                      density="compact"
                    />
                    <v-select
                      v-model="keyDriver.feature_columns"
                      :items="store.recipe.columnHeaders"
                      label="Feature columns"
                      multiple
                      chips
                      closable-chips
                      clearable
                      hide-details
                      class="mt-2"
                      density="compact"
                    />
                    <v-select
                      v-model="keyDriver.categorical_features"
                      :items="keyDriver.feature_columns"
                      label="Categorical features"
                      multiple
                      chips
                      closable-chips
                      clearable
                      hide-details
                      class="mt-2"
                      density="compact"
                    />
                    <v-text-field
                      v-model.number="keyDriver.p_value_threshold"
                      type="number"
                      label="P-value threshold"
                      step="0.01"
                      min="0"
                      max="1"
                      density="compact"
                      variant="outlined"
                      hide-details
                      class="mt-2"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Outlier Detection -->
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="d-flex align-center justify-space-between w-100">
                      <div class="d-flex align-center">
                        <span class="text-subtitle-2">Outliers</span>
                        <v-tooltip
                          text="Flags unusually high or low numeric values. Example: on 'daily_visits', this highlights days that sit far outside the usual range."
                        >
                          <template #activator="{ props }">
                            <v-icon v-bind="props" size="16" class="ml-1">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-switch
                        v-model="outlierDetection.enabled"
                        inset
                        density="compact"
                        class="switch-sm"
                        hide-details
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select
                      v-model="outlierDetection.target_columns"
                      :items="store.recipe.columnHeaders"
                      label="Target columns"
                      multiple
                      chips
                      closable-chips
                      clearable
                      hide-details
                      density="compact"
                    />
                    <v-select
                      v-model="outlierDetection.method"
                      :items="['iqr', 'z-score']"
                      label="Method"
                      hide-details
                      density="compact"
                      class="mt-2"
                    />
                    <v-text-field
                      v-model.number="outlierDetection.threshold"
                      type="number"
                      label="Threshold"
                      step="0.1"
                      min="0"
                      density="compact"
                      variant="outlined"
                      hide-details
                      class="mt-2"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Summary Statistics -->
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="d-flex align-center justify-space-between w-100">
                      <div class="d-flex align-center">
                        <span class="text-subtitle-2">Summary Stats</span>
                        <v-tooltip
                          text="Reports count, mean, min, max, and quartiles for numeric columns. Example: 'amount_spent' by group to quickly see distribution and spread."
                        >
                          <template #activator="{ props }">
                            <v-icon v-bind="props" size="16" class="ml-1">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-switch
                        v-model="summaryStats.enabled"
                        inset
                        density="compact"
                        class="switch-sm"
                        hide-details
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select
                      v-model="summaryStats.numeric_columns"
                      :items="store.recipe.columnHeaders"
                      label="Numeric columns"
                      multiple
                      chips
                      closable-chips
                      clearable
                      hide-details
                      density="compact"
                    />
                    <!-- Column-level transforms can be added later -->
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Time Series -->
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <div class="d-flex align-center justify-space-between w-100">
                      <div class="d-flex align-center">
                        <span class="text-subtitle-2">Time Series</span>
                        <v-tooltip
                          text="Rolls up a numeric metric over time at daily, weekly, or monthly frequency. Example: 'revenue' summed by month to see trends."
                        >
                          <template #activator="{ props }">
                            <v-icon v-bind="props" size="16" class="ml-1">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-switch
                        v-model="timeSeries.enabled"
                        inset
                        density="compact"
                        class="switch-sm"
                        hide-details
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select
                      v-model="timeSeries.date_column"
                      :items="store.recipe.columnHeaders"
                      label="Date column"
                      clearable
                      hide-details
                      density="compact"
                    />
                    <v-select
                      v-model="timeSeries.metric_column"
                      :items="store.recipe.columnHeaders"
                      label="Metric column"
                      clearable
                      hide-details
                      class="mt-2"
                      density="compact"
                    />
                    <v-select
                      v-model="timeSeries.frequency"
                      :items="frequencies"
                      label="Frequency"
                      hide-details
                      class="mt-2"
                      density="compact"
                    />
                    <v-select
                      v-model="timeSeries.metric"
                      :items="timeSeriesMetrics"
                      label="Metric"
                      hide-details
                      class="mt-2"
                      density="compact"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </v-card>


        </v-col>
      </v-row>
      </v-container>
    </v-main>
        <v-dialog v-model="definitionsDialog" max-width="900">
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <span>Logic reference</span>
          <v-btn icon="mdi-close" variant="text" @click="definitionsDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 70vh; overflow-y: auto;">
          <pre class="text-caption" style="white-space: pre-wrap;">{{ definitionsText }}</pre>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="definitionsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRecipeStore } from './stores/recipe'
import type { Operation, Rule } from './types/recipe'
import {
  submitReport,
  type AnalysisRequest,
  type CustomAnalysis,
  type CrosstabAnalysis,
  type CorrelationAnalysis,
  type Filter,
  type Transformation,
} from './services/api'
import axios from 'axios'

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

const FEEDBACK_LINK: string =
  import.meta.env.VITE_FEEDBACK_LINK ||
  '#'

const store = useRecipeStore()
const inputFile = ref<File | null>(null)

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.origin}/api`
const isRunning = ref(false)
const errorMessage = ref<string | null>(null)
const bundleName = ref<string>('generated_report')
const definitionsDialog = ref(false)
const definitionsText = ref<string>('')
const operations: Operation[] = [
  'distribution',
  'valueCount',
  'duplicate',
  'average',
  'sum',
  'median',
  'clean',
]

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

function normalizeHeaderName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/[^\w]+/g, '_')
    .replace(/_+/g, '_')    
    .replace(/^_+|_+$/g, '')
}

const headersText = ref(store.recipe.columnHeaders.join('\n'))
function applyHeaders() {
  const parts = headersText.value
    .split(/[\n,]+/)
    .map(s => s.trim())
    .filter(Boolean)
    .map(normalizeHeaderName)
  store.setColumnHeaders(parts)
}

const newRule = ref<{column:string, operation:Operation|null}>({ column: '', operation: null })
function addRule() {
  if (!newRule.value.column || !newRule.value.operation) return
  const normalizedColumn = normalizeHeaderName(newRule.value.column)
  store.addRule(normalizedColumn, newRule.value.operation)
  newRule.value = { column:'', operation: null }
}

function update(r: Rule) { store.updateRule(r.id, r) }
function remove(id: string) { store.removeRule(id) }

const excludeKeysText = ref<Record<string, string[]>>({})
function syncExcludeFromStore() {
  const map: Record<string, string[]> = {}
  for (const r of store.rules) {
    map[r.id] = Array.isArray(r.options.excludeKeys) ? [...r.options.excludeKeys] : []
  }
  excludeKeysText.value = map
}
onMounted(syncExcludeFromStore)
watch(
  () => store.rules.map(r => ({ id: r.id, keys: r.options.excludeKeys })),
  () => syncExcludeFromStore(),
  { deep: true }
)
function applyExcludeChips(r: Rule) {
  const arr = excludeKeysText.value[r.id] || []
  const keys = arr.map((s: string) => String(s).trim()).filter(Boolean)
  store.updateRule(r.id, { options: { ...r.options, excludeKeys: keys } })
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

function openImport() {
  (fileInput.value as HTMLInputElement).click()
}
const fileInput = ref<HTMLInputElement|null>(null)
function onImport(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || !files[0]) return
  const reader = new FileReader()
  reader.onload = () => {
    try { store.importRecipe(String(reader.result)) }
    catch (e) { alert('Invalid recipe.json') }
  }
  reader.readAsText(files[0])
}
function exportRecipe() { store.exportRecipe() }

function addCorrelationBlock() {
  extraCorrelationBlocks.value.push({
    id: cryptoRandom(),
    sources: [],
    targets: [],
    threshold: correlationThreshold.value,
    enabled: true,
  })
}

function removeCorrelationBlock(id: string) {
  extraCorrelationBlocks.value = extraCorrelationBlocks.value.filter((b) => b.id !== id)
}

function addCrosstabBlock() {
  extraCrosstabBlocks.value.push({
    id: cryptoRandom(),
    sources: [],
    targets: [],
    enabled: true,
  })
}

function removeCrosstabBlock(id: string) {
  extraCrosstabBlocks.value = extraCrosstabBlocks.value.filter((b) => b.id !== id)
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
          {
            id: cryptoRandom(),
            column: 'category',
            operation: 'distribution',
            options: defaultRuleOptions(),
            enabled: true,
          },
          {
            id: cryptoRandom(),
            column: 'dup_col',
            operation: 'duplicate',
            options: defaultRuleOptions(),
            enabled: true,
          },
        ],
      },
    })
    return
  }
  if (name === 'bmb') {
    store.$patch({
      recipe: {
        ...store.recipe,
        rules: [
          {
            id: cryptoRandom(),
            column: 'score',
            operation: 'average',
            options: defaultRuleOptions(),
            enabled: true,
          },
        ],
      },
    })
  }
}
function cryptoRandom() {
  try { return crypto.randomUUID().slice(0, 8) } catch { return Math.random().toString(36).slice(2,10) }
}

function buildTransformationsForRule(r: Rule): Transformation[] {
  const transformations: Transformation[] = []

  transformations.push({ action: 'strip_whitespace', params: {} })

  if (r.options.delimiter) {
    if (r.options.separateNodes) {
      transformations.push({
        action: 'split_and_explode',
        params: { delimiter: r.options.delimiter },
      })
    } else if (r.options.rootOnly) {
      transformations.push({
        action: 'to_root_node',
        params: { delimiter: r.options.delimiter },
      })
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
    filters.push({
      column: filterColumn,
      operator,
      value: filterValue,
    })
  }

  return filters
}

function buildPostFiltersForRule(r: Rule): Filter[] {
  const postFilters: Filter[] = []

  if (r.options.excludeKeys && r.options.excludeKeys.length > 0) {
    postFilters.push({
      column: r.column,
      operator: 'not_in',
      value: r.options.excludeKeys,
    })
  }

  if (r.operation === 'valueCount' && r.options.value) {
    postFilters.push({
      column: r.column,
      operator: 'eq',
      value: r.options.value,
    })
  }

  return postFilters
}

function clearRecipe() {
  
  if (typeof (store as any).resetRecipe === 'function') {
    (store as any).resetRecipe()
    headersText.value = ''
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
    return
  }
}

async function openDefinitionsDialog() {
  try {
    if (!definitionsText.value) {
      const resp = await fetch(`${API_BASE_URL}/definitions.txt`)
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      definitionsText.value = await resp.text()
    }
    definitionsDialog.value = true
  } catch (err) {
    console.error('Failed to load logic reference:', err)
    errorMessage.value = 'Failed to load logic reference. Please try again.'
  }
}

async function downloadDefinitions() {
  try {
    const resp = await fetch(`${API_BASE_URL}/definitions.txt`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const text = await resp.text()
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'report_auto_definitions.txt'
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Failed to download definitions:', err)
    errorMessage.value = 'Failed to download definitions. Please try again.'
  }
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

    const resp = await fetch(`${API_BASE_URL}/headers`, {
      method: 'POST',
      body: formData,
    })

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    const data = await resp.json()
    const headers = Array.isArray((data as any).headers)
      ? (data as any).headers.map((h: unknown) => normalizeHeaderName(String(h)))
      : []

    if (!headers.length) {
      throw new Error('No headers returned from server')
    }

    store.setColumnHeaders(headers)
    headersText.value = headers.join('\n')
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

// Build correlation steps per (source, target) pair so each requested
// relationship is explicitly returned.
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

  if (
    insight.crosstabEnabled &&
    insight.crosstabSources.length > 0 &&
    insight.crosstabTargets.length > 0
  ) {
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
    // Respect global switch but do not depend on main sources/targets.
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

  // --- Advanced Analyses: Key Drivers, Outliers, Summary Stats, Time Series ---
  const kdConfig = store.recipe.keyDriver
  if (
    kdConfig &&
    kdConfig.enabled &&
    kdConfig.target_variable &&
    kdConfig.feature_columns.length > 0
  ) {
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
  if (
    outlierConfig &&
    outlierConfig.enabled &&
    outlierConfig.target_columns.length > 0
  ) {
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
  if (
    statsConfig &&
    statsConfig.enabled &&
    statsConfig.numeric_columns.length > 0
  ) {
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
  if (
    tsConfig &&
    tsConfig.enabled &&
    tsConfig.date_column &&
    tsConfig.metric_column
  ) {
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

<style>
.app-background {
  /* Soft neutral background in the spirit of macOS/iOS surfaces */
  background: linear-gradient(180deg, #f5f5f7 0%, #f5f5f7 40%, #ffffff 100%);
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* Treat the main container as the "app surface" */
.app-background > .v-container {
  max-width: 1040px;
  width: 100%;
  margin: 24px auto 32px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  padding-inline: 24px;
}

@media (max-width: 959px) {
  .app-background > .v-container {
    margin: 12px 8px 24px;
    border-radius: 18px;
    padding-inline: 16px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  }
}

.v-application {
  --v-theme-primary: #facc15;          
  --v-theme-primary-darken-1: #eab308; 
  --v-theme-on-primary: #1f2937;       
}

/* Top app bar – light, minimal, with subtle divider like macOS toolbars */
.v-app-bar {
  background-color: #f9fafb !important;
  color: #111827 !important;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.08);
}

.v-toolbar-title {
  font-weight: 600;
  letter-spacing: -0.01em;
}

.v-card {
  background-color: #ffffff;
  border-radius: 14px;
  border-color: rgba(15, 23, 42, 0.06);
  box-shadow:
    0 4px 12px rgba(15, 23, 42, 0.04),
    0 1px 1px rgba(15, 23, 42, 0.04);
}

/* Compact card layout – tighter padding, more "app-like" density */
.card-headers .v-card-title,
.card-add-rule .v-card-title,
.card-rules .v-card-title,
.card-insights .v-card-title,
.card-crosstabs .v-card-title,
.card-advanced .v-card-title,
.card-understand .v-card-title,
.card-actions .v-card-title {
  padding-top: 8px !important;
  padding-bottom: 4px !important;
}

.card-headers .v-card-text,
.card-add-rule .v-card-text,
.card-rules .v-card-text,
.card-insights .v-card-text,
.card-crosstabs .v-card-text,
.card-advanced .v-card-text,
.card-understand .v-card-text,
.card-actions .v-card-text {
  padding-top: 8px !important;
  padding-bottom: 10px !important;
}

.card-rules .v-card.mb-2 {
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}

/* Right column layout: tidy vertical stack with compact spacing */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Improve contrast on tonal buttons and chips when using mustard primary */
.v-btn--variant-tonal {
  color: #1f2937; /* dark slate text for legibility */
  font-weight: 500;
}

.v-chip--variant-tonal {
  color: #1f2937;
  font-weight: 500;
}

.d-none { display: none; }
.ml-2 { margin-left: 8px; }
.nowrap { white-space: nowrap; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.switch-sm { transform: scale(0.85); transform-origin: center left; }
.no-resize-ta textarea { resize: none !important; }

/* Page header */
.page-header h1 {
  font-weight: 600;
}

.page-header p {
  max-width: 640px;
}

.section-label {
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(17, 24, 39, 0.45);
  font-weight: 500;
  margin-bottom: 4px;
}

/* Card polish – unify look across the main sections */
.card-headers,
.card-add-rule,
.card-rules,
.card-insights,
.card-crosstabs,
.card-advanced,
.card-understand,
.card-actions {
  background-color: #ffffff;
  border-radius: 14px;
}

/* Stronger section titles */
.card-headers .v-card-title,
.card-add-rule .v-card-title,
.card-rules .v-card-title,
.card-insights .v-card-title,
.card-crosstabs .v-card-title,
.card-advanced .v-card-title,
.card-understand .v-card-title,
.card-actions .v-card-title {
  font-weight: 500;
}



/* Mobile tweaks – disable sticky so it doesn’t feel broken on small screens */
@media (max-width: 959px) {
  .right-column {
    position: static;
  }

  .sticky-card {
    position: static;
  }
}

.primary-pill {
  border-radius: 999px !important;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 600;
  padding-inline: 20px;
}
</style>
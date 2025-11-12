<template>
  <v-app>
    <v-app-bar density="comfortable">
      <v-toolbar-title>Report Configure</v-toolbar-title>
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
      <input ref="fileInput" type="file" accept="application/json" class="d-none" @change="onImport"/>
    </v-app-bar>

    <v-main class="pt-12">
      <v-container fluid class="py-8">
      <v-row>

        <v-col cols="12" md="9">
          <v-card class="mb-6" variant="outlined" rounded="lg">
            <v-card-title>Column Headers (manual)</v-card-title>
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
                <div class="text-caption">Currently not set to identify column headers, manual intervention needed.</div>
                <v-spacer />
                <v-btn variant="tonal" color="primary" size="small" @click="applyHeaders">Apply</v-btn>
              </div>
            </v-card-text>
          </v-card>
          <v-card class="mb-6" variant="outlined" rounded="lg">
            <v-card-title>Add Rule</v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="newRule.column"
                  :items="store.recipe.columnHeaders"
                  label="Column"
                  clearable
                  hide-details
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="newRule.operation"
                  :items="operations"
                  label="Operation"
                  clearable
                  hide-details
                  density="comfortable"
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

          <v-card class="mb-6" variant="outlined" rounded="lg">
            <v-card-title>Rules</v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <template v-if="store.rules.length">
                <v-card
                  v-for="r in store.rules"
                  :key="r.id"
                  class="mb-3 pa-3"
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
                </v-card>
              </template>
              <template v-else>
                <div class="text-medium-emphasis">No rules yet — add one above.</div>
              </template>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Right: Insights & Actions -->
        <v-col cols="12" md="3">
          <v-card class="mb-6" variant="outlined" rounded="lg">
            <v-card-title>Insights</v-card-title>
          <v-card-text>
            <v-combobox
              v-model="sources"
              :items="store.recipe.columnHeaders"
              label="sources"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              density="comfortable"
            />
            <v-combobox
              v-model="targets"
              :items="store.recipe.columnHeaders"
              label="targets"
              multiple
              chips
              closable-chips
              clearable
              hide-details
              class="mt-2"
              density="comfortable"
            />
            <v-slider
              v-model="threshold"
              :min="0"
              :max="1"
              :step="0.05"
              :show-ticks="true"
              class="mt-6"
            />
            <div class="text-caption">threshold: {{ threshold.toFixed(2) }}</div>
            <v-btn class="mt-3" block @click="applyInsights">Apply</v-btn>
          </v-card-text>
          </v-card>

          <v-card class="mb-6" variant="outlined" rounded="lg">
            <v-card-title>Actions</v-card-title>
          <v-card-text>
            <v-btn block class="text-truncate" variant="tonal" color="primary" @click="exportRecipe" prepend-icon="mdi-content-save">Export recipe.json</v-btn>
            <v-btn block class="mt-2 text-truncate" variant="tonal" @click="openImport" prepend-icon="mdi-file-import">Import recipe.json</v-btn>
          </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRecipeStore } from './stores/recipe'
import type { Operation, Rule } from './types/recipe'

const store = useRecipeStore()
const operations: Operation[] = ['distribution','valueCount','duplicate','average','clean']

const headersText = ref(store.recipe.columnHeaders.join('\n'))
function applyHeaders() {
  const parts = headersText.value
    .split(/[\n,]+/)
    .map(s => s.trim())
    .filter(Boolean)
  store.setcolumnHeaders(parts)
}

const newRule = ref<{column:string, operation:Operation|null}>({ column: '', operation: null })
function addRule() {
  if (!newRule.value.column || !newRule.value.operation) return
  store.addRule(newRule.value.column, newRule.value.operation)
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

const sources = ref<string[]>(store.recipe.insights.sources)
const targets = ref<string[]>(store.recipe.insights.targets)
const threshold = ref<number>(store.recipe.insights.threshold ?? 0.2)
function applyInsights() { store.setInsights(sources.value, targets.value, threshold.value) }

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


function loadTemplate(name: string) {
  if (name === 'minimal') {
    // keep headers, clear rules
    store.$patch({ recipe: { ...store.recipe, rules: [] } })
    return
  }
  if (name === 'icfi') {
    store.$patch({
      recipe: {
        ...store.recipe,
        rules: [
          { id: cryptoRandom(), column: 'category', operation: 'distribution', options: {}, enabled: true },
          { id: cryptoRandom(), column: 'dup_col', operation: 'duplicate', options: {}, enabled: true },
        ]
      }
    })
    return
  }
  if (name === 'bmb') {
    store.$patch({
      recipe: {
        ...store.recipe,
        rules: [
          { id: cryptoRandom(), column: 'score', operation: 'average', options: {}, enabled: true },
        ]
      }
    })
  }
}
function cryptoRandom() {
  try { return crypto.randomUUID().slice(0, 8) } catch { return Math.random().toString(36).slice(2,10) }
}
</script>

<style>
.d-none { display: none; }
.ml-2 { margin-left: 8px; }
.nowrap { white-space: nowrap; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.switch-sm { transform: scale(0.85); transform-origin: center left; }
.no-resize-ta textarea { resize: none !important; }
</style>
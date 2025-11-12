import { defineStore } from 'pinia'
import type { Recipe, Rule, Operation } from '../types/recipe'

const DEFAULT_RECIPE: Recipe = {
  version: '1',
  headersPalette: [],
  rules: [],
  insights: { sources: [], targets: [], threshold: 0.2 },
}

function uid() { return Math.random().toString(36).slice(2, 10) }

export const useRecipeStore = defineStore('recipe', {
  state: () => ({
    recipe: load() as Recipe
  }),
  getters: {
    rules: (s) => s.recipe.rules,
    insights: (s) => s.recipe.insights,
  },
  actions: {
    setHeadersPalette(headers: string[]) {
      this.recipe.headersPalette = headers.map(h => h.trim()).filter(Boolean)
      save(this.recipe)
    },
    addRule(column: string, operation: Operation) {
      const r: Rule = {
        id: uid(),
        column, operation,
        options: {},
        enabled: true,
      }
      this.recipe.rules.push(r)
      save(this.recipe)
    },
    updateRule(id: string, patch: Partial<Rule>) {
      const i = this.recipe.rules.findIndex(r => r.id === id)
      if (i >= 0) {
        this.recipe.rules[i] = { ...this.recipe.rules[i], ...patch }
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
      this.recipe.rules.splice(Math.max(0, Math.min(toIndex, this.recipe.rules.length)), 0, r)
      save(this.recipe)
    },
    setInsights(sources: string[], targets: string[], threshold: number) {
      this.recipe.insights = { sources, targets, threshold }
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
      this.recipe = obj
      save(this.recipe)
    },
  }
})

function load(): Recipe {
  const raw = localStorage.getItem('recipe.v1')
  return raw ? JSON.parse(raw) : DEFAULT_RECIPE
}
function save(r: Recipe) {
  localStorage.setItem('recipe.v1', JSON.stringify(r))
}
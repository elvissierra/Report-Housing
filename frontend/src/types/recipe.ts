export type Operation = 'distribution' | 'valueCount' | 'duplicate' | 'average' | 'clean'

export interface RuleOptions {
  delimiter?: string | null
  separateNodes?: boolean
  rootOnly?: boolean
  value?: string | null
  excludeKeys?: string[]
}

export interface Rule {
  id: string
  column: string
  operation: Operation
  options: RuleOptions
  enabled: boolean
}

export interface Insights {
  sources: string[]
  targets: string[]
  threshold: number
}

export interface Recipe {
  version: '1'
  columnHeaders: string[]
  rules: Rule[]
  insights: Insights
}
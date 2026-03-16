/**
 * Canonical column-name normalizer — identical logic runs on the backend (extract.py).
 * Any change here must be mirrored there and in the Pinia store.
 */
export function normalizeHeaderName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .replace(/[^\w]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
}

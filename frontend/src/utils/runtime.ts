export function isMockApiEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK !== 'false'
}

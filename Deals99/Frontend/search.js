// Lightweight search module using Fuse.js (loaded from CDN)
// Exposes `buildIndex(products)` and `search(q, opts)`.
let FuseModule = null;
let fuseInstance = null;

export async function ensureFuse() {
  if (!FuseModule) {
    FuseModule = (await import('https://cdn.jsdelivr.net/npm/fuse.js@6.6.2/dist/fuse.esm.js'))?.default || (await import('https://cdn.jsdelivr.net/npm/fuse.js@6.6.2/dist/fuse.esm.js'));
  }
  return FuseModule;
}

export async function buildIndex(products = []) {
  const Fuse = await ensureFuse();
  const options = {
    keys: [
      { name: 'name', weight: 0.8 },
      { name: 'category', weight: 0.4 },
      { name: 'desc', weight: 0.2 }
    ],
    threshold: 0.35,
    includeScore: true,
    useExtendedSearch: true,
  };
  fuseInstance = new Fuse(products, options);
  try { localStorage.setItem('deals99_search_index_ts', String(Date.now())); } catch(e){}
  return fuseInstance;
}

export function search(query, limit = 20) {
  if (!fuseInstance || !query) return [];
  const results = fuseInstance.search(query, { limit }).map(r => r.item);
  return results;
}

export function hasIndex() {
  return !!fuseInstance;
}
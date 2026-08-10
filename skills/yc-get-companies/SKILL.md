---
name: yc-get-companies
description: >-
  Fetches Y Combinator companies from the Startup Directory via agent-browser,
  applying batch and other filters, then prints a table of name, batch, website,
  industries, location, and short description. Use when the user invokes
  /yc-get-companies, or asks for YC companies by batch (e.g. S26) or directory
  filters.
---

# YC Get Companies

Invocation: `/yc-get-companies <filters>` — e.g. `S26`, `Summer 2026 fintech`, `W25 hiring`.

Uses `agent-browser` against https://www.ycombinator.com/companies.

## 1. Parse filters

Map batch shorthand to directory labels:

| Input | Batch |
|-------|-------|
| `S26` / `Summer 26` | `Summer 2026` |
| `W25` / `Winter 25` | `Winter 2025` |
| `F24` / `Fall 24` | `Fall 2024` |
| `Sp26` / `Spring 26` | `Spring 2026` |

Two-digit years → `20xx`. Also accept full labels (`Summer 2026`).

Other filters → URL params:

| Filter | Param |
|--------|-------|
| Batch | `batch` |
| Industry | `industry` |
| HQ region | `regions` |
| Search text | `query` |
| Is hiring | `isHiring=true` |
| Top companies | `top_company=true` |
| Nonprofit | `nonprofit=true` |

Examples: `?batch=Summer%202026`, `?industry=Fintech&regions=Europe`.

## 2. Open filtered directory

```bash
agent-browser open "https://www.ycombinator.com/companies?<params>"
agent-browser wait --load networkidle
```

If a batch checkbox isn't visible, click Batch **See all options**, re-snapshot, then check it. Prefer URL params when possible — they drive the same controls.

## 3. Extract rows

List cards omit website URLs. After the filtered page loads, pull complete rows from the directory's Algolia index using the public search key already on the page:

```bash
agent-browser eval --stdin <<'EVALEOF'
(async () => {
  const entry = performance.getEntriesByType('resource').find(e => e.name.includes('algolia.net'));
  if (!entry) throw new Error('No Algolia request found — wait for page load');
  const u = new URL(entry.name);
  const appId = u.searchParams.get('x-algolia-application-id');
  const apiKey = u.searchParams.get('x-algolia-api-key');

  // Mirror active URL filters as facetFilters (AND of OR-groups).
  const sp = new URLSearchParams(location.search);
  const facets = [];
  for (const [param, facet] of [['batch','batch'],['industry','industry'],['regions','regions']]) {
    const v = sp.get(param);
    if (v) facets.push([`${facet}:${v}`]);
  }
  for (const [param, facet] of [['isHiring','isHiring'],['top_company','top_company'],['nonprofit','nonprofit']]) {
    if (sp.get(param) === 'true') facets.push([`${facet}:true`]);
  }

  const params = new URLSearchParams({ query: sp.get('query') || '', hitsPerPage: '1000' });
  if (facets.length) params.set('facetFilters', JSON.stringify(facets));

  const res = await fetch(`https://${appId}-dsn.algolia.net/1/indexes/*/queries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Algolia-Application-Id': appId,
      'X-Algolia-API-Key': apiKey,
    },
    body: JSON.stringify({ requests: [{ indexName: 'YCCompany_production', params: params.toString() }] }),
  });
  const hits = (await res.json()).results[0].hits;
  return JSON.stringify(hits.map(h => ({
    name: h.name,
    batch: h.batch,
    website: h.website || '',
    industries: (h.industries || []).join(', '),
    location: h.all_locations || '',
    description: h.one_liner || '',
  })));
})()
EVALEOF
```

If Algolia is unavailable: scroll until company count stabilizes, scrape cards (`[class*="_coName_"]`, `[class*="_coLocation_"]`, `.pill`, description span), then same-origin `fetch(/companies/<slug>)` and parse `data-tooltip-content` next to `aria-label="Company website"`.

## 4. Print table

Markdown table columns (exact order):

`company name | batch number | website URL | industries | location | company short description`

Then `agent-browser close`.

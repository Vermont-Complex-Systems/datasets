import datasetsData from "$data/datasets.ts";

export async function load() {
  const datasets = datasetsData.map(d => ({
    id: d.id,
    url: d.url,
    display: d.display,
    description: d.description,
    format: d.format,
    name: d.name,
    month: d.month,
    keywords: d.keywords,
    filters: Array.isArray(d.filters) ? d.filters : [d.filters].filter(Boolean)
  }));

  return {
    datasets
  };
}
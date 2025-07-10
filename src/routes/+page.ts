// src/routes/+page.ts
import { datasets } from '$lib/data/datasets.js';
import type { PageLoad } from './$types.js';

export const load: PageLoad = async () => {
  return {
    datasets
  };
};
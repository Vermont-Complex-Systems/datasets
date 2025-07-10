// src/routes/+page.ts
import { datasets } from '$lib/data/datasets.js';

export function load() {
  return {
    datasets
  };
}
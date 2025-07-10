// src/lib/data/datasets.ts
import type { Dataset } from '$lib/types/dataset.js';

export const datasets: Dataset[] = [
  {
    id: 'uvm-professors-2023',
    name: 'UVM Professors 2023',
    description: 'University of Vermont professors data including research groups, publications, and departmental information',
    url: '/data/uvm_profs_2023.csv',
    source: 'Vermont Complex Systems',
    tags: ['csv', 'university', 'professors', 'research', 'uvm'],
    contentType: 'text/csv',
    format: 'CSV',
    size: '47KB',
    lastUpdated: '2024-07-10'
  },
  {
    id: 'uvm-departments-colleges',
    name: 'UVM Departments to Colleges',
    description: 'Mapping of University of Vermont departments to their parent colleges',
    url: '/data/uvm_depts_to_colleges.csv',
    source: 'Vermont Complex Systems',
    tags: ['csv', 'university', 'departments', 'colleges', 'uvm', 'mapping'],
    contentType: 'text/csv',
    format: 'CSV',
    size: '2KB',
    lastUpdated: '2024-07-10'
  }
];
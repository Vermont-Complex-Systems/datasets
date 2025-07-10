// src/lib/data/datasets.ts
import type { Dataset } from '$lib/types/dataset.js';

export const datasets: Dataset[] = [
  {
    id: 'uvm-professors-2023',
    name: 'UVM Professors 2023',
    description: 'University of Vermont professors data including research groups, publications, and departmental information',
    url: 'https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/uvm_profs_2023.csv',
    source: 'GitHub',
    tags: ['csv', 'university', 'professors', 'research', 'uvm'],
    status: 'unknown'
  },
  {
    id: 'jsonplaceholder-posts',
    name: 'JSONPlaceholder Posts',
    description: 'Fake REST API for testing and prototyping',
    url: 'https://jsonplaceholder.typicode.com/posts',
    source: 'JSONPlaceholder',
    tags: ['api', 'json', 'testing'],
    status: 'unknown'
  },
  {
    id: 'github-api',
    name: 'GitHub API',
    description: 'GitHub REST API v3',
    url: 'https://api.github.com',
    source: 'GitHub',
    tags: ['api', 'github', 'development'],
    status: 'unknown'
  },
  {
    id: 'httpbin',
    name: 'HTTPBin',
    description: 'HTTP request and response service',
    url: 'https://httpbin.org/status/200',
    source: 'HTTPBin',
    tags: ['api', 'testing', 'http'],
    status: 'unknown'
  }
];
<!-- src/lib/components/DatasetCard.svelte -->
<script lang="ts">
  import type { Dataset } from '$lib/types/dataset.js';
  
  let { dataset }: { dataset: Dataset } = $props();
</script>

<div class="border rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
  <!-- Header -->
  <div class="flex items-start justify-between mb-4">
    <div class="flex-1">
      <h3 class="text-lg font-semibold mb-1">{dataset.name}</h3>
      <p class="text-sm text-gray-600">{dataset.description}</p>
    </div>
    
    <div class="ml-4">
      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
        {dataset.format}
      </span>
    </div>
  </div>

  <!-- Tags -->
  <div class="flex flex-wrap gap-1 mb-4">
    {#each dataset.tags as tag}
      <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
        {tag}
      </span>
    {/each}
  </div>

  <!-- Metadata -->
  <div class="space-y-2 text-sm text-gray-600">
    <div class="flex justify-between">
      <span>Source:</span>
      <span>{dataset.source}</span>
    </div>
    
    {#if dataset.size}
      <div class="flex justify-between">
        <span>Size:</span>
        <span>{dataset.size}</span>
      </div>
    {/if}
    
    {#if dataset.lastUpdated}
      <div class="flex justify-between">
        <span>Last updated:</span>
        <span>{dataset.lastUpdated}</span>
      </div>
    {/if}
  </div>

  <!-- Download Button -->
  <div class="mt-4 pt-4 border-t">
    <a 
      href={dataset.url}
      class="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      target="_blank"
      rel="noopener noreferrer"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Download {dataset.format}
    </a>
  </div>
</div>
<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { datasets } from '$lib/data/datasets.js';
</script>

<svelte:head>
  <title>Vermont Complex Systems Datasets</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b">
    <div class="max-w-4xl mx-auto px-4 py-12">
      <h1 class="text-3xl font-bold text-gray-900 mb-4">
        Vermont Complex Systems Datasets
      </h1>
      <p class="text-lg text-gray-600">
        Research datasets from the Vermont Complex Systems research group
      </p>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-4 py-8">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">Available Datasets</h2>
    
    <div class="space-y-4">
      {#each datasets as dataset}
        <div class="bg-white border rounded-lg p-6">
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-lg font-medium text-gray-900">{dataset.name}</h3>
            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">{dataset.format}</span>
          </div>
          
          <p class="text-gray-600 mb-4">{dataset.description}</p>
          
          <div class="flex flex-wrap gap-2 mb-4">
            {#each dataset.tags as tag}
              <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">{tag}</span>
            {/each}
          </div>
          
          <a 
            href={dataset.url}
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download CSV
          </a>
        </div>
      {/each}
    </div>

    <div class="mt-12 bg-white border rounded-lg p-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Usage</h3>
      <div class="bg-gray-100 p-4 rounded">
        <code class="text-sm">
          import pandas as pd<br>
          df = pd.read_csv('https://vermont-complex-systems.github.io/datasets/data/uvm_profs_2023.csv')
        </code>
      </div>
    </div>
  </main>
</div>
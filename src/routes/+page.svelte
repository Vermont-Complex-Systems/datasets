<!-- src/routes/+page.svelte -->
<script lang="ts">
  import type { PageProps } from './$types.js';
  import DatasetCard from '$lib/components/DatasetCard.svelte';
  
  let { data }: PageProps = $props();
</script>

<svelte:head>
  <title>Vermont Complex Systems Datasets</title>
  <meta name="description" content="Collection of datasets from Vermont Complex Systems research group" />
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <!-- Hero Section -->
  <header class="bg-white border-b">
    <div class="max-w-7xl mx-auto px-4 py-16">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        Vermont Complex Systems Datasets
      </h1>
      <p class="text-xl text-gray-600 max-w-3xl">
        A collection of research datasets from the Vermont Complex Systems research group. 
        All datasets are freely available for research and educational purposes.
      </p>
      
      <div class="flex gap-4 mt-8">
        <a 
          href="https://github.com/Vermont-Complex-Systems/datasets" 
          class="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          View on GitHub
        </a>
        
        <a 
          href="https://github.com/Vermont-Complex-Systems" 
          class="inline-flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Research Group
        </a>
      </div>
    </div>
  </header>

  <!-- Datasets Section -->
  <main class="max-w-7xl mx-auto px-4 py-12">
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Available Datasets</h2>
      <p class="text-gray-600">
        {data.datasets.length} dataset{data.datasets.length === 1 ? '' : 's'} available for download
      </p>
    </div>

    {#if data.datasets.length === 0}
      <div class="text-center py-12">
        <p class="text-gray-500">No datasets available.</p>
      </div>
    {:else}
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {#each data.datasets as dataset}
          <DatasetCard {dataset} />
        {/each}
      </div>
    {/if}

    <!-- Usage Examples -->
    <div class="mt-16 bg-white rounded-lg border p-8">
      <h3 class="text-xl font-bold text-gray-900 mb-4">Usage Examples</h3>
      
      <div class="space-y-6">
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Python/Pandas</h4>
          <pre class="bg-gray-100 p-4 rounded text-sm overflow-x-auto"><code>import pandas as pd

# Load UVM professors dataset
df = pd.read_csv('https://vermont-complex-systems.github.io/datasets/data/uvm_profs_2023.csv')
print(f"Loaded {len(df)} professors")</code></pre>
        </div>
        
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Dagster Asset</h4>
          <pre class="bg-gray-100 p-4 rounded text-sm overflow-x-auto"><code>from dagster import asset
import pandas as pd
import requests

@asset
def uvm_professors_2023() -> pd.DataFrame:
    url = "https://vermont-complex-systems.github.io/datasets/data/uvm_profs_2023.csv"
    
    # Check availability
    response = requests.head(url)
    if response.status_code != 200:
        raise Exception(f"Dataset not available: {response.status_code}")
    
    return pd.read_csv(url)</code></pre>
        </div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="bg-white border-t mt-20">
    <div class="max-w-7xl mx-auto px-4 py-8 text-center text-sm text-gray-600">
      <p>
        Built with SvelteKit • 
        <a href="https://github.com/Vermont-Complex-Systems" class="hover:text-gray-900 transition-colors">
          Vermont Complex Systems Research Group
        </a>
      </p>
    </div>
  </footer>
</div>
<script lang="ts">
  import { getContext } from "svelte";
  import FilterBar from "$lib/components/FilterBar.svelte";
	import { base } from "$app/paths";
  
  const { datasets } = getContext("Home");

  let activeFilter = $state(undefined);

  // Extract unique filters from all stories
  let allFilters = $derived.by(() => {
    const filterSet = new Set();
    datasets.forEach(d => {
      if (d.filters && Array.isArray(d.filters)) {
        d.filters.forEach(filter => filterSet.add(filter));
      }
    });
    return Array.from(filterSet).sort();
  });

  let filtered = $derived.by(() => {
    const f = datasets.filter((d) => {
      return !activeFilter || d.filters.includes(activeFilter);
    });
    return f;
  });

  // Reset pagination when filter changes
  $effect(() => {
    activeFilter; // Track the dependency
  });

  console.log(datasets.map(d=>d.keywords))
</script>

<div class="content">
  <FilterBar bind:activeFilter filters={allFilters} />
  
  <div class="min-h-screen">
    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-4 py-12">
      <!-- Dataset Cards -->
      <div class="grid gap-6 md:grid-cols-3">
        {#each filtered as dataset}
          <div class="card">
            <!-- Card Header -->
            <div class="card-content">
              <div class="card-header">
                <h4 class="card-title">{dataset.name}</h4>
                <span class="format-badge">
                  {dataset.format}
                </span>
              </div>
              
              <p class="card-description">{dataset.description}</p>
            </div>
            
            <!-- Tags -->
            <div class="tags-section">
              <div class="tags-container">
                {#each dataset.keywords as tag}
                  <span class="tag">
                    {tag}
                  </span>
                {/each}
              </div>
            </div>
            
            <!-- Card Footer - Always at bottom -->
            <div class="card-footer">
              <div class="button-group">
                <a 
                  href={dataset.url}
                  class="download-button"
                  target="_blank"
                >
                  <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download {dataset.format}
                </a>
                
                <a 
                  href={dataset.display} 
                  class="preview-button"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <svg class="button-icon" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  Preview
                </a>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </main>  
  </div>
</div>

<style>
  /* Card layout */
  .card {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
    overflow: hidden;
    transition: box-shadow 0.2s;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  /* Card content */
  .card-content {
    padding: 1.5rem;
    padding-bottom: 1rem;
    flex: 1;
  }

  /* Header with proper alignment */
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start; /* This is key - aligns items to the top */
    margin-bottom: 0.75rem;
    gap: 1rem; /* Adds space between title and badge */
  }

  .card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
    line-height: 1.4; /* Ensures consistent line height */
    flex: 1; /* Takes available space */
  }

  .format-badge {
    background: #dbeafe;
    color: #1e40af;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap; /* Prevents wrapping */
    flex-shrink: 0; /* Prevents shrinking */
  }

  .card-description {
    color: #6b7280;
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
  }

  /* Tags section */
  .tags-section {
    padding: 0 1.5rem 1rem 1.5rem;
  }

  .tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    background: #f3f4f6;
    color: #374151;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  /* Card footer */
  .card-footer {
    padding: 1.5rem;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
    margin-top: auto;
  }

  .button-group {
    display: flex;
    gap: 0.75rem;
  }

  .download-button,
  .preview-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .download-button {
    background: #3b82f6;
    color: white;
  }

  .download-button:hover {
    background: #2563eb;
  }

  .preview-button {
    background: #6b7280;
    color: white;
  }

  .preview-button:hover {
    background: #4b5563;
  }

  .button-icon {
    width: 1rem;
    height: 1rem;
  }
</style>
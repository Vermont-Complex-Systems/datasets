<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import Footer from '$lib/components/Footer.svelte';
  
  let { children } = $props();
</script>

<Header />

<main id="content">
	{@render children?.()}
</main>

<Footer />

<style>
	#content {
		flex: 1;
		padding: 1rem 2rem 2rem;
	}
	
	@media (max-width: 768px) {
		#content {
			padding: 0 1rem 1rem; /* Reduced top padding from 0.5rem to 0.25rem */
			margin-top: -0.5rem; /* Pull content up slightly */
		}
	}
</style>

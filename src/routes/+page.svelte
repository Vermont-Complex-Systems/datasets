<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { setContext } from "svelte";
  import Meta from "$lib/components/Meta.svelte";
  import Home from "$lib/components/Home.svelte";

  let { data } = $props();
  const { datasets } = data;

  // To change when we can, it is pudding property
  const preloadFont = [
    "https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Regular.woff2",
    "https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Bold.woff2",
    "https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Regular-Web.woff2",
    "https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Bold-Web.woff2",
    "https://pudding.cool/assets/fonts/atlas/AtlasTypewriter-Medium-Web.woff2"
  ];
  
  // Make stories available to Home component via context
  setContext("Home", { datasets });

</script>

<svelte:head>
  <title>Vermont Complex Systems Institute</title>
  <meta name="description" content="Research datasets from the Vermont Complex Systems Institute.">
</svelte:head>

<Meta 
  title="Datasets"
  description="Scientific data essays that uncover the challenges of computational science."
  {preloadFont}
/>

<Home />


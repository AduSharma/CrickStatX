<script>
  // Load global CSS
  import '../app.css';
  
  // Navbar
  import Navbar from '$lib/components/Navbar.svelte';
</script>

<Navbar />

<!-- Page content -->
<div class="container" style="padding-block: 20px;">
  <slot />
</div>
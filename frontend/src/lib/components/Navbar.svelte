<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

  let current = '/';
  $: {
    const unsubscribe = page.subscribe(($p) => {
      current = $p.url.pathname ?? '/';
    });
  }

  let activePath: string = current;
  $: if (current !== activePath) activePath = current;

  const links = [
    { href: '/', label: 'Home' },
    { href: '/player-profile', label: 'Player Profile' },
    { href: '/compare', label: 'Compare' },
    { href: '/top-performers', label: 'Top Performers' },
    { href: '/player-filter', label: 'Explore Players' }
  ];

  const normalize = (p: string) => {
    if (!p) return '/';
    if (p !== '/' && p.endsWith('/')) return p.slice(0, -1);
    return p;
  };

  const isActive = (href: string) => {
    const c = normalize(current);
    const h = normalize(href);
    if (h === '/') return c === '/';
    return c === h || c.startsWith(h + '/');
  };

  function onClick(e: MouseEvent, href: string) {
    e.preventDefault();
    activePath = href;
    goto(href, { invalidateAll: true });
  }
</script>

<nav class="nav-bar">
  <div class="nav-container">
    <a href="/" class="logo-link">
      <img src="/Logo.png" alt="CrickStatX" class="logo" />
    </a>

    <div class="nav-links">
      {#each links as l}
        <a
          href={l.href}
          class="btn"
          on:click={(e) => onClick(e, l.href)}
          class:active-tab={ activePath === l.href || isActive(l.href) }
          aria-current={isActive(l.href) ? 'page' : undefined}
        >
          {l.label}
        </a>
      {/each}
    </div>
  </div>
</nav>

<style>
  .nav-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    border-bottom: 1px solid var(--border);
    width: 100%;
    background: linear-gradient(90deg, var(--brand-red), var(--brand-blue));
  }
  .nav-container {
    margin: 0 auto;
    display:flex;
    align-items:center;
    gap:14px;
    padding:10px 20px;
    color:white;
    flex-wrap: wrap;
  }
  .logo-link { display:flex; align-items:center; gap:10px; font-weight:700; font-size:22px; color:white; text-decoration:none; }
  .logo { width:115px; height:48px; border-radius:10px; border:2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }

  .nav-links {
    display:flex;
    gap:12px;
    margin-left:auto;
    flex-wrap: wrap;
  }

  .btn {
    color: black;
    background: white;
    border: none;
    padding: 9px 16px;
    border-radius: 8px;
    text-decoration: none;
    transition: transform 0.15s ease, background 0.15s ease;
    display: inline-block;
    font-weight: 600;
  }
  .btn:hover {
    transform: translateY(-2.5px);
    color: white;
    background: rgba(255,255,255,0.18);
  }
  .active-tab {
    color: white !important;
    background: rgba(255, 255, 255, 0.18);
    border-radius: 8px;
  }

  @media (max-width: 700px) {
    .nav-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }
    .nav-links {
      width: 100%;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .btn {
      flex: 1;
      text-align: center;
    }
  }
</style>

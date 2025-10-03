<script lang="ts">
  import { onMount } from 'svelte';

  let personalizedPlayers: string[] = [];
  let current = 0;
  let intervalId: number | null = null;
  const rotateInterval = 3000; // 3 seconds

  type Slide = {
    id: string;
    title: string;
    detail: string;
    href: string;
    emoji?: string;
    cta: string;
  };

  const slides: Slide[] = [
    {
      id: 'compare',
      title: 'Compare Players',
      detail: 'Quickly compare stats of two or more players across formats. Use it to find matchups, strengths and weaknesses.',
      cta: 'Compare Now',
      href: '/compare',
      emoji: '⚖️'
    },
    {
      id: 'top-performers',
      title: 'Top Performers',
      detail: 'Discover the best batsmen, bowlers and all-rounders across Test, ODI and T20 formats.',
      cta: 'View Top Performers',
      href: '/top-performers',
      emoji: '🏆'
    },
    {
      id: 'explore',
      title: 'Explore Players',
      detail: 'Filter and explore players by team, era and top stats. Great for research and deep-dives.',
      cta: 'Explore Players',
      href: '/explore',
      emoji: '🔎'
    }
  ];

  function startRotation() {
    stopRotation();
    intervalId = window.setInterval(() => {
      next();
    }, rotateInterval);
  }

  function stopRotation() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  function goTo(href: string) {
    window.location.href = href;
  }

  function prev() {
    current = (current - 1 + slides.length) % slides.length;
  }

  function next() {
    current++;
    if (current >= slides.length) {
      current = 0;
    }
  }

  function goToPlayerProfile(player: string) {
    window.location.href = `/player-profile?name=${encodeURIComponent(player)}`;
  }

  onMount(() => {
    const stored = localStorage.getItem("personalizedPlayers");
    if (stored) personalizedPlayers = JSON.parse(stored);

    startRotation();
    return () => stopRotation();
  });
</script>

<!-- Banner Header -->
<div class="banner">
  <h1>Welcome to <span>CrickStatX</span></h1>
  <p class="fade-in">Your cricket insights, stats & personalized players in one place.</p>
</div>

<!-- Two-column layout -->
<main class="home-grid">
  <!-- Carousel Section -->
  <section
    class="card hero-carousel curtain"
    on:mouseenter={stopRotation}
    on:mouseleave={startRotation}
    aria-roledescription="carousel"
  >
    <div class="carousel-inner" style="transform: translateX(-{current * 100}%);">
      {#each slides as s, i}
        <article class="slide">
          <div class="slide-left">
            <div class="slide-header">
              <div class="slide-emoji">{s.emoji}</div>
              <h3 class="slide-title">
                <a href={s.href} class="title-link">{s.title}</a>
              </h3>
            </div>
            <p class="slide-detail">{s.detail}</p>
            <button class="cta-btn" on:click={() => goTo(s.href)}>{s.cta}</button>
          </div>
        </article>
      {/each}
    </div>

    <!-- controls -->
    <div class="carousel-controls">
      <button class="nav prev" aria-label="Previous slide" on:click={prev}>◀</button>
      <div class="dots">
        {#each slides as _, idx}
          <button
            class:active={idx === current}
            on:click={() => (current = idx)}
            aria-label={`Go to slide ${idx + 1}`}
          />
        {/each}
      </div>
      <button class="nav next" aria-label="Next slide" on:click={next}>▶</button>
    </div>
  </section>

  <!-- Personalized Players Section -->
  <section class="card your-players curtain delay">
    <h2>⭐ Your Players</h2>
    {#if personalizedPlayers.length > 0}
      <div class="player-grid">
        {#each personalizedPlayers as p}
          <div class="player-card" on:click={() => goToPlayerProfile(p)}>{p}</div>
        {/each}
      </div>
    {:else}
      <p class="no-players">
        You haven't added any players yet. Go to
        <a href="/player-profile"><strong>Player Profile</strong></a> to personalize.
      </p>
    {/if}
  </section>
</main>

<style>
  :global(body) {
    background: #f3f4f6;
  }

  /* Banner */
  .banner {
    text-align: center;
    padding: 16px 12px;
    background: linear-gradient(90deg, var(--brand-red), var(--brand-blue));
    color: white;
    border-bottom: 1px solid var(--border);
    margin-bottom: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  }
  .banner h1 { margin: 0; font-size: 1.7rem; font-weight: 800; }
  .banner h1 span { color: #ffd54f; text-shadow: 0 1px 3px rgba(0,0,0,0.35); }
  .banner p { margin: 6px 0 0; font-size: 1rem; font-weight: 500; background: linear-gradient(90deg, #fff, #dbeafe, #fff); -webkit-background-clip: text; color: transparent; }

  .fade-in { opacity: 0; animation: fadeInText 1.2s ease-in forwards; }
  @keyframes fadeInText { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0);} }

  /* Curtain animation */
  .curtain { position: relative; overflow: hidden; }
  .curtain::before {
    content: "";
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%;
    background: #f3f4f6;
    transform: translateX(0);
    animation: curtainReveal 1s ease forwards;
  }
  .curtain.delay::before { animation-delay: 0.4s; }
  @keyframes curtainReveal { to { transform: translateX(100%); } }

  .home-grid {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px 32px;
  }

  .card {
    background: var(--card);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }

  /* Carousel */
  .hero-carousel { 
    position: relative; 
    overflow: hidden; 
    min-height: 300px;   /* fixed consistent height */
    display:flex; 
    flex-direction:column; 
  }
  .carousel-inner {
    display: flex;
    transition: transform 0.6s ease-in-out;
    width: 100%;
  }
  .slide { 
    flex: 0 0 100%; 
    display:flex; 
    flex-direction: column; 
    justify-content: space-between; /* push button down */
    padding: 10px; 
  }
  .slide-left { 
    display: flex; 
    flex-direction: column; 
    height: 100%; 
    padding: 8px; 
  }
  .slide-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
  .slide-emoji { font-size: 28px; }
  .slide-title { font-size: 1.2rem; font-weight: 700; color: var(--brand-blue); margin: 0; }
  .slide-title .title-link { text-decoration: none; color: inherit; }
  .slide-title .title-link:hover { text-decoration: none; }
  .slide-detail { margin: 10px 0; color: #4b5563; line-height: 1.35; }

  .cta-btn {
    background: var(--brand-blue);
    color: white;
    border: none;
    padding: 7px 14px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 700;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    margin-top: auto;   /* stays at bottom */
  }
  .cta-btn:hover { transform: translateY(-2px); box-shadow: 0 3px 6px rgba(0,0,0,0.12); }

  .carousel-controls {
    display:flex; align-items:center; justify-content:space-between;
    margin-top: 10px;
  }
  .nav { background: white; border-radius: 8px; border:1px solid var(--border); padding: 6px 8px; cursor:pointer; }
  .dots { display:flex; gap:8px; }
  .dots button { width:10px; height:10px; border-radius:50%; border:none; background:#e5e7eb; cursor:pointer; }
  .dots button.active { background: var(--brand-blue); }

  /* Players */
  .your-players { 
    height: 300px;        /* same fixed height as carousel */
    overflow-y: auto; 
    padding-top: 20px; 
  }
  .your-players h2 { margin-bottom: 14px; font-size: 1.2rem; font-weight: 700; color: var(--brand-red); }
  .player-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap:12px; }
  .player-card {
    background:white;
    padding: 14px 18px;
    border-radius: 12px;
    border: 1px solid var(--border);
    font-weight: 600;
    text-align:center;
    cursor:pointer;
  }
  .player-card:hover { transform: translateY(-2px); box-shadow:0 2px 8px rgba(0,0,0,0.1); }
  .no-players { margin-top: 10px; }

  @media (max-width: 900px) {
    .slide { flex-direction:column; text-align:center; align-items:center; }
    .carousel-controls { gap:8px; }
    .slide-header { justify-content:center; }
  }
  @media (max-width: 768px) {
    .home-grid { grid-template-columns: 1fr; }
  }
</style>

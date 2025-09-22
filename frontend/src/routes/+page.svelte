<script lang="ts">
  import { onMount } from 'svelte';

  let personalizedPlayers: string[] = [];
  let liveScores: { match: string; score: string }[] = [];

  onMount(() => {
    const stored = localStorage.getItem("personalizedPlayers");
    if (stored) personalizedPlayers = JSON.parse(stored);

    liveScores = [
      { match: "IND vs AUS", score: "IND 245/6 (45.3)" },
      { match: "ENG vs PAK", score: "ENG 310/7 (50)" }
    ];
  });

  function goToPlayerProfile(player: string) {
    // Navigate with query parameter ?name=<player>
    window.location.href = `/player-profile?name=${encodeURIComponent(player)}`;
  }
</script>

<!-- Banner Header -->
<div class="banner">
  <h1>Welcome to <span>CrickStatX</span></h1>
  <p class="fade-in">Your cricket insights, stats & personalized players in one place.</p>
</div>

<!-- Two-column layout -->
<main class="home-grid">
  <!-- Live Scores Section -->
  <section class="card live-scores curtain">
    <h2>📡 Live Scores</h2>
    {#if liveScores.length > 0}
      <div class="score-list">
        {#each liveScores as s}
          <div class="score-card">
            <strong>{s.match}</strong> — {s.score}
          </div>
        {/each}
      </div>
    {:else}
      <p>No live matches right now.</p>
    {/if}
  </section>

  <!-- Personalized Players Section -->
  <section class="card your-players curtain delay">
    <h2>⭐ Your Players</h2>
    {#if personalizedPlayers.length > 0}
      <div class="player-carousel-wrapper">
        <div class="player-carousel">
          {#each personalizedPlayers as p}
            <div class="player-card" on:click={() => goToPlayerProfile(p)}>
              {p}
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <p>
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

  /* Banner styling */
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
  
  .banner h1 {
    margin: 0;
    font-size: 1.7rem;
    font-weight: 800;
  }
  
  .banner h1 span {
    color: #ffd54f; /* golden */
    text-shadow: 0 1px 3px rgba(0,0,0,0.35);
  }
  
  .banner p {
    margin: 6px 0 0;
    font-size: 1rem;
    font-weight: 500;
    background: linear-gradient(90deg, #fff, #dbeafe, #fff);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent; /* fallback */
    letter-spacing: 0.4px;
  }

  /* Fade-in animation */
  .fade-in {
    opacity: 0;
    animation: fadeInText 1.2s ease-in forwards;
  }
  
  @keyframes fadeInText {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Curtain animation */
  .curtain {
    position: relative;
    overflow: hidden;
  }
  
  .curtain::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #f3f4f6;
    transform: translateX(0);
    animation: curtainReveal 1s ease forwards;
  }
  
  .curtain.delay::before {
    animation-delay: 0.4s;
  }
  
  @keyframes curtainReveal {
    to {
      transform: translateX(100%);
    }
  }

  /* Grid layout */
  .home-grid {
    display: grid;
    grid-template-columns: 1fr 2fr; /* Live = 30%, Players = 70% */
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px 40px;
  }

  /* Card sections */
  .card {
    background: var(--card);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  
  .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  }

  /* Live scores */
  .live-scores h2 {
    margin-bottom: 14px;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--brand-blue);
  }
  
  .score-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .score-card {
    background: white;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  
  .score-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  /* Personalized players */
  .your-players {
    min-height: 220px; 
  }
  
  .your-players h2 {
    margin-bottom: 14px;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--brand-red);
  }

  .player-carousel-wrapper {
    overflow-x: auto;
    padding-bottom: 10px; /* space for scrollbar */
  }
  
  .player-carousel {
    display: flex;
    gap: 12px;
    scroll-snap-type: x mandatory;
  }
  
  .player-card {
    flex: 0 0 auto;
    scroll-snap-align: start;
    background: white;
    padding: 14px 18px;
    border-radius: 12px;
    border: 1px solid var(--border);
    font-weight: 600;
    min-width: 140px;
    text-align: center;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
  }
  
  .player-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  /* Mobile first adjustments */
  @media (max-width: 768px) {
    .home-grid {
      grid-template-columns: 1fr; 
    }
    
    .your-players {
      min-height: 180px;
    }
  }
</style>

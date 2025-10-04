<script lang="ts">
  import { onMount } from 'svelte';
  import jsPDF from 'jspdf';
  import html2canvas from 'html2canvas';

  const API = 'http://127.0.0.1:8000';

  let query: string = '';
  let allPlayers: string[] = [];
  let suggestions: string[] = [];
  let selectedPlayer: string | null = null;
  let activeTab: 'profile' | 'analyze' | 'tags' = 'profile';

  let loading = false;
  let message: string = '';

  let profileData: any = null;
  let analyzeData: any = null;
  let tagsData: any = null;

  // track instantly if player is added
  let playerAdded = false;

  onMount(async () => {
    try {
      const res = await fetch(`${API}/players`);
      if (res.ok) {
        allPlayers = await res.json();
      }
    } catch (err) {
      console.error('Error loading players:', err);
    }

    // 1. Check URL query param
    const params = new URLSearchParams(window.location.search);
    const paramPlayer = params.get('name');
    if (paramPlayer) {
      query = paramPlayer;
      fetchPlayer(paramPlayer);
      return;
    }

    // 2. Otherwise fallback to last session
    const last = sessionStorage.getItem('lastPlayer');
    if (last) {
      query = last;
      fetchPlayer(last);
    }
  });

  $: if (!query.trim()) {
    suggestions = [];
  } else {
    const q = query.toLowerCase();
    suggestions = allPlayers
      .filter((p) => p && (p.toLowerCase().startsWith(q) || p.toLowerCase().includes(q)))
      .slice(0, 12);
  }

  async function fetchPlayer(player: string) {
    if (!player) return;
    loading = true;
    message = '';
    selectedPlayer = player;
    sessionStorage.setItem('lastPlayer', player);

    try {
      const pRes = await fetch(`${API}/player-profile?player_name=${encodeURIComponent(player)}`);
      profileData = pRes.ok ? await pRes.json() : { message: 'No profile' };

      const aRes = await fetch(`${API}/analyze?player_name=${encodeURIComponent(player)}`);
      analyzeData = aRes.ok ? await aRes.json() : { message: 'No analysis' };

      const tRes = await fetch(`${API}/tags?player_name=${encodeURIComponent(player)}`);
      tagsData = tRes.ok ? await tRes.json() : { message: 'No tags' };

      suggestions = [];
      query = player;
      activeTab = 'profile';

      // update instant toggle state
      playerAdded = isPlayerAdded();
    } catch (err) {
      console.error('Fetch error:', err);
      message = 'Error fetching data from backend.';
    } finally {
      loading = false;
    }
  }

  function selectSuggestion(s: string) {
    fetchPlayer(s);
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (query.trim()) fetchPlayer(query.trim());
    }
  }

  // Add / Remove Player
  function togglePlayer() {
    if (!selectedPlayer) return;
    try {
      const stored = localStorage.getItem('personalizedPlayers');
      let arr: string[] = stored ? JSON.parse(stored) : [];

      if (!arr.includes(selectedPlayer)) {
        arr.unshift(selectedPlayer);
        arr = arr.slice(0, 20);
        localStorage.setItem('personalizedPlayers', JSON.stringify(arr));
        message = `${selectedPlayer} added to your players.`;
      } else {
        arr = arr.filter((p) => p !== selectedPlayer);
        localStorage.setItem('personalizedPlayers', JSON.stringify(arr));
        message = `${selectedPlayer} removed from your players.`;
      }
      // update instant toggle
      playerAdded = isPlayerAdded();
    } catch (err) {
      console.error('localStorage error', err);
      message = 'Could not update player locally.';
    }
    setTimeout(() => (message = ''), 2000);
  }

  // ✅ Fixed exportPDF with multi-page support
  async function exportPDF() {
    const element = document.getElementById('export-section');
    if (!element) return;
    try {
      const canvas = await html2canvas(element, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');

      // Colored Title
      pdf.setFontSize(18);
      pdf.setTextColor(37, 99, 235); // brand blue
      pdf.text('CrickStatX', 10, 15);
      pdf.setTextColor(220, 38, 38); // red
      pdf.text(`- ${selectedPlayer || 'Player'} (${activeTab})`, 45, 15);

      const pdfWidth = pdf.internal.pageSize.getWidth() - 20;
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      let heightLeft = pdfHeight;
      let position = 25;

      // First page
      pdf.addImage(imgData, 'PNG', 10, position, pdfWidth, pdfHeight);
      heightLeft -= pdf.internal.pageSize.getHeight() - 30;

      // Extra pages if content overflows
      while (heightLeft > 0) {
        position = heightLeft - pdfHeight + 25;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 10, position, pdfWidth, pdfHeight);
        heightLeft -= pdf.internal.pageSize.getHeight() - 30;
      }

      pdf.save(`${selectedPlayer || 'player'}_${activeTab || 'profile'}.pdf`);
    } catch (err) {
      console.error('PDF export error', err);
      message = 'Export failed.';
      setTimeout(() => (message = ''), 2500);
    }
  }

  function getAnalyzeSummaries() {
    if (!analyzeData) return [];
    if (Array.isArray(analyzeData)) {
      return analyzeData.map((it: any) => it.summary || JSON.stringify(it));
    }
    if (analyzeData.message) return [analyzeData.message];
    return [JSON.stringify(analyzeData)];
  }

  function getTagsForSelected() {
    if (!tagsData) return [];
    if (Array.isArray(tagsData) && tagsData.length > 0) {
      const found = tagsData.find(
        (t: any) => t.player && selectedPlayer && t.player.toLowerCase() === selectedPlayer.toLowerCase()
      );
      const source = found || tagsData[0];
      return source.tags || [];
    }
    if (tagsData.message) return [tagsData.message];
    return [];
  }

  function orderedProfile(profile: any) {
    if (!profile) return {};
    let entries = Object.entries(profile);
    const tags = getTagsForSelected();
    if (tags.includes('Bowler')) {
      entries = entries.sort(([a]) => (a.toLowerCase().includes('bowling') ? -1 : 1));
    }
    return Object.fromEntries(entries);
  }

  function isPlayerAdded() {
    const stored = localStorage.getItem('personalizedPlayers');
    const arr: string[] = stored ? JSON.parse(stored) : [];
    return selectedPlayer ? arr.includes(selectedPlayer) : false;
  }
</script>

<div style="max-width:900px; margin:0 auto; padding-top:8px;">
  <!-- Banner -->
  <div
    style="background:linear-gradient(90deg,#1e3a8a,#2563eb,#1e40af); color:white; padding:14px; border-radius:10px; text-align:center; margin-bottom:20px;"
  >
    <h2 style="margin:0; font-size:1.2rem; font-weight:700; color:white;">
      Player Profile Explorer
    </h2>
    <p style="margin:4px 0 0; font-size:0.9rem; color:white;">Search any international cricketer to view their stats, analysis & tags.</p>
  </div>

  <div style="max-width:600px; margin:0 auto;">
    <div style="display:flex; gap:8px;">
      <input type="text" bind:value={query} on:keydown={onKeydown} placeholder="Search player..."
        style="flex:1; padding:10px; border:1px solid var(--border); border-radius:8px;" />
      <button class="search-btn" on:click={() => query && fetchPlayer(query.trim())}>Search</button>
      <button class="toggle-btn"
        on:click={() => { query=''; suggestions=[]; selectedPlayer=null; profileData=analyzeData=tagsData=null; sessionStorage.removeItem('lastPlayer'); }}>
        Clear
      </button>
    </div>

    {#if suggestions.length > 0}
      <ul style="border:1px solid var(--border); border-radius:8px; background:white; margin-top:6px; max-height:260px; overflow:auto;">
        {#each suggestions as s}
          <li on:click={() => selectSuggestion(s)} style="padding:8px; cursor:pointer; transition:background 0.2s;"
            on:mouseover={(e) => (e.currentTarget.style.background = '#f3f4f6')}
            on:mouseout={(e) => (e.currentTarget.style.background = 'white')}>
            {s}
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  {#if loading}
    <p style="text-align:center; margin-top:14px; color:var(--muted)">Loading player data...</p>
  {/if}

  {#if message}
    <p style="text-align:center; margin-top:8px; color:var(--brand-red); font-weight:600;">{message}</p>
  {/if}

  {#if selectedPlayer}
    <div style="display:flex; gap:12px; margin-top:20px; border-bottom:1px solid var(--border); padding-bottom:10px;">
      <button class:active-tab={activeTab === 'profile'} on:click={() => (activeTab = 'profile')}>Profile</button>
      <button class:active-tab={activeTab === 'analyze'} on:click={() => (activeTab = 'analyze')}>Analyze</button>
      <button class:active-tab={activeTab === 'tags'} on:click={() => (activeTab = 'tags')}>Tags</button>

      <div style="margin-left:auto; display:flex; gap:8px;">
        <button on:click={togglePlayer} class="toggle-btn">{playerAdded ? 'Remove Player' : 'Add Player'}</button>
        <button on:click={exportPDF} class="pdf-btn">Export PDF</button>
      </div>
    </div>

    <div id="export-section" style="margin-top:18px;">
      {#if activeTab === 'profile'}
        {#if profileData && profileData.profile}
          <h2 style="font-size:1.1rem; font-weight:700; margin-bottom:8px; color:var(--brand-blue);">{profileData.player}</h2>

          {#each Object.entries(orderedProfile(profileData.profile)) as [category, files]}
            <div style="margin-top:12px;">
              <h3 style="font-weight:700; margin-bottom:6px; color:var(--brand-blue);">{category}</h3>

              {#each Object.entries(files as Record<string, any[]>) as [filename, rows]}
                <div style="margin-bottom:12px;">
                  <div style="font-weight:600; margin-bottom:6px;">
                    {filename
                      .replace('Batting/ODI data','ODI')
                      .replace('ODI data','ODI')
                      .replace('Batting_','')
                      .replace('Bowling_','')
                      .replace('Fielding_','')
                      .replace('.csv','')}
                  </div>

                  {#if rows && rows.length > 0}
                    <table class="data-table">
                      <thead>
                        <tr>{#each Object.keys(rows[0]) as col}<th>{col}</th>{/each}</tr>
                      </thead>
                      <tbody>
                        {#each rows as r}
                          <tr>{#each Object.values(r) as val}<td>{val}</td>{/each}</tr>
                        {/each}
                      </tbody>
                    </table>
                  {:else}
                    <div style="padding:8px; color:var(--muted); background:#fff; border:1px solid var(--border); border-radius:8px;">No rows</div>
                  {/if}
                </div>
              {/each}
            </div>
          {/each}
        {:else}
          <p style="color:var(--muted)">No profile data available.</p>
        {/if}
      {/if}

      {#if activeTab === 'analyze'}
        <h3 style="font-weight:700; margin-bottom:8px; color:var(--brand-red);">Analysis</h3>
        {#if analyzeData}
          {#each getAnalyzeSummaries() as s}
            <div class="analyze-box">{s}</div>
          {/each}
        {:else}
          <p style="color:var(--muted)">No analysis available.</p>
        {/if}
      {/if}

      {#if activeTab === 'tags'}
        <h3 style="font-weight:700; margin-bottom:8px; color:var(--brand-red);">Tags</h3>
        {#if tagsData}
          {#each getTagsForSelected() as t}<span class="badge">{t}</span>{/each}
        {:else}
          <p style="color:var(--muted)">No tags available.</p>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .data-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
  }
  .data-table th, .data-table td {
    border: 1px solid var(--border);
    padding: 6px 8px;
    text-align: center;
    font-size: 0.9rem;
  }
  .data-table th {
    background: #f3f4f6;
    font-weight: 700;
  }

  button {
    border: none;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
  }
  button:hover {
    transform: translateY(-1px);
    opacity: 0.9;
  }

  .active-tab {
    color: var(--brand-blue);
    border-bottom: 2px solid var(--brand-blue);
  }
  .badge {
    display: inline-block;
    padding: 6px 10px;
    margin-right: 8px;
    margin-bottom: 8px;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 12px;
    font-weight: 600;
  }
  .pdf-btn {
    background: var(--brand-blue);
    color: white;
  }
  .pdf-btn:hover {
    background: #1e40af;
  }
  .toggle-btn {
    background: white;
    border: 1px solid var(--border);
  }
  .toggle-btn:hover {
    background: #f3f4f6;
  }
  .search-btn {
    background: var(--brand-blue);
    color: white;
  }
  .search-btn:hover {
    background: #1e40af;
  }
  .analyze-box {
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: white;
    font-size: 0.9rem;
    line-height: 1.4;
  }
  
@media (max-width: 768px) {
  div[style*="display:flex; gap:8px;"] {
    flex-direction: column !important;
  }
  .search-btn,
  .toggle-btn {
    width: 100% !important;
  }

  /* Tabs and action buttons stack */
  div[style*="display:flex; gap:12px;"] {
    flex-direction: column !important;
    align-items: flex-start !important;
  }
  div[style*="margin-left:auto; display:flex; gap:8px;"] {
    margin-left: 0 !important;
    flex-wrap: wrap !important;
    width: 100% !important;
    justify-content: space-between !important;
  }
  .pdf-btn {
    flex: 1;
  }
  .data-table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>

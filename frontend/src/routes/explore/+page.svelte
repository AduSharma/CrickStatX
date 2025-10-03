<script lang="ts">
  import { onMount } from 'svelte';
  import jsPDF from 'jspdf';
  import html2canvas from 'html2canvas';

  const API = 'http://127.0.0.1:8000';

  const TEAM_MAP: Record<string, string> = {
    "IND": "India", "AUS": "Australia", "PAK": "Pakistan",
    "ENG": "England", "SA": "South Africa",
    "NZ": "New Zealand", "SL": "Sri Lanka", "BAN": "Bangladesh",
    "WI": "West Indies", "AFG": "Afghanistan",
    "IRE": "Ireland", "NL": "Netherlands", "SCOT": "Scotland", "KENYA": "Kenya",
    "CAN": "Canada", "NAM": "Namibia", "UAE": "United Arab Emirates",
    "HKG": "Hong Kong", "NEPAL": "Nepal",
    "ASIA": "Asia XI", "ICC": "ICC World XI"
  };

  let team: string = '';
  let sort_by: string = '';
  let era: string = '';
  let format: string = '';

  let players: any[] = [];
  let loading = false;
  let message = '';
  let suggestions: string[] = [];

  onMount(() => {
    const sTeam = sessionStorage.getItem('ep_team');
    const sSort = sessionStorage.getItem('ep_sort_by');
    const sEra = sessionStorage.getItem('ep_era');
    const sFormat = sessionStorage.getItem('ep_format');

    if (sTeam) team = sTeam;
    if (sSort) sort_by = sSort;
    if (sEra) era = sEra;
    if (sFormat) format = sFormat;

    if (team) loadPlayers();
  });

  function handleTeamInput(val: string) {
    team = val;
    if (!val) {
      suggestions = [];
      return;
    }
    const upper = val.toUpperCase();
    suggestions = Object.values(TEAM_MAP).filter((t) =>
      t.toUpperCase().startsWith(upper)
    );
  }

  function selectSuggestion(s: string) {
    team = s;
    suggestions = [];
  }

  function formatEra(val: string) {
    if (val && !val.endsWith("s")) era = val + "s";
  }

  async function loadPlayers() {
    if (!team || team.trim() === '') {
      message = 'Please enter a team name (e.g., India, Australia).';
      players = [];
      return;
    }

    const upper = team.toUpperCase();
    if (TEAM_MAP[upper]) team = TEAM_MAP[upper];
    if (era && !era.endsWith("s")) era = era + "s";

    loading = true;
    message = '';
    players = [];

    sessionStorage.setItem('ep_team', team);
    sessionStorage.setItem('ep_sort_by', sort_by);
    sessionStorage.setItem('ep_era', era);
    sessionStorage.setItem('ep_format', format);

    try {
      const params = new URLSearchParams();
      params.set('team', team.trim());
      if (sort_by) params.set('sort_by', sort_by);
      if (era) params.set('era', era);
      if (format) params.set('format', format);

      const res = await fetch(`${API}/player-filter?${params.toString()}`);
      const data = await res.json();

      if (data.players && Array.isArray(data.players) && data.players.length > 0) {
        players = data.players;
        message = '';
      } else {
        players = [];
        message = 'No players found for given filters.';
      }
    } catch (err) {
      console.error(err);
      message = 'Failed to fetch players.';
      players = [];
    } finally {
      loading = false;
    }
  }

  async function exportPDF() {
    const element = document.getElementById('export-section');
    if (!element) return;
    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      let title = format ? `${format.toUpperCase()} players` : "Players";
      title += ` of ${team}`;
      if (era) title += ` in ${era}`;
      if (sort_by) {
        title += ` sorted by ${
          sort_by === 'wkts' ? 'Wickets' : sort_by === 'st' ? 'Stumpings' : 'Runs'
        }`;
      }

      pdf.setFontSize(16);
      pdf.setTextColor(37, 99, 235);
      pdf.text('CrickStatX', 10, 15);
      pdf.setTextColor(220, 38, 38);
      pdf.text(`- ${title}`, 45, 15);

      const canvas = await html2canvas(element, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const imgProps = pdf.getImageProperties(imgData);

      const contentWidth = pdfWidth - 20;
      const contentHeight = (imgProps.height * contentWidth) / imgProps.width;

      let y = 25;
      let heightLeft = contentHeight;

      pdf.addImage(imgData, 'PNG', 10, y, contentWidth, contentHeight);
      heightLeft -= pdfHeight - 30;

      let position = -(pdfHeight - 30);
      while (heightLeft > 0) {
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 10, position + y, contentWidth, contentHeight);
        heightLeft -= pdfHeight - 30;
        position -= pdfHeight - 30;
      }

      pdf.save(`Players_${team}_${format || 'all'}_${era || 'all'}.pdf`);
    } catch (err) {
      console.error('PDF export error', err);
      message = 'Export failed.';
    }
  }

  function goToProfile(name: string) {
    window.location.href = `/player-profile?name=${encodeURIComponent(name)}`;
  }

  function clearFilters() {
    team = '';
    sort_by = '';
    era = '';
    format = '';
    players = [];
    message = '';
    suggestions = [];
    sessionStorage.clear();
  }

  function headingText() {
    let text = `Players for ${team}`;
    if (era) text += ` in ${era}`;
    if (format) text += ` in ${format.toUpperCase()}`;
    if (sort_by) {
      text += ` sorted by ${
        sort_by === 'wkts' ? 'Wickets' : sort_by === 'st' ? 'Stumpings' : 'Runs'
      }`;
    }
    return text;
  }
</script>

<div class="container">
  <div class="banner">
    <h2>Explore Players</h2>
    <p>Filter players by country, era, format or stat.</p>
  </div>

  <div class="filters">
    <div class="filter-controls">
      <div style="position:relative;">
        <input
          type="text"
          placeholder="Enter Team"
          bind:value={team}
          on:input={(e) => handleTeamInput((e.target as HTMLInputElement).value)}
          on:keydown={(e) => e.key === 'Enter' && loadPlayers()}
        />
        {#if suggestions.length > 0}
          <ul class="suggestions">
            {#each suggestions as s}
              <li on:click={() => selectSuggestion(s)}>{s}</li>
            {/each}
          </ul>
        {/if}
      </div>

      <select bind:value={sort_by} on:change={loadPlayers}>
        <option value="" selected> Sort By </option>
        <option value="runs">Runs</option>
        <option value="wkts">Wickets</option>
        <option value="st">Stumpings</option>
      </select>

      <input
        type="text"
        placeholder="Era (e.g., 1990s)"
        bind:value={era}
        on:blur={(e) => formatEra((e.target as HTMLInputElement).value)}
        on:keydown={(e) => e.key === 'Enter' && loadPlayers()}
      />

      <select bind:value={format} on:change={loadPlayers}>
        <option value="" selected> Format</option>
        <option value="test">Test</option>
        <option value="odi">ODI</option>
        <option value="t20">T20</option>
      </select>
    </div>

    <div class="filter-actions">
      <button class="search-btn" on:click={loadPlayers}>Load</button>
      <button class="toggle-btn" on:click={clearFilters}>Clear</button>
      {#if players.length > 0}
        <button class="pdf-btn" on:click={exportPDF}>Export PDF</button>
      {/if}
    </div>
  </div>

  {#if loading}
    <p style="text-align:center; margin-top:14px; color:var(--muted)">Loading players...</p>
  {:else if message}
    <p style="text-align:center; margin-top:8px; color:var(--brand-red); font-weight:600;">{message}</p>
  {:else if players.length > 0}
    <p class="heading">{headingText()}</p>

    <div id="export-section" class="card-grid">
      {#each players as p, i}
        <div class="card">
          <h3 class="player-name" title="View Profile" on:click={() => goToProfile(p.Player)}>
            #{i + 1} {p.Player}
          </h3>
          <div class="stats">
            {#each Object.entries(p) as [key, val]}
              {#if key !== 'Player'}
                <div class="stat-row">
                  <span class="label">{key}</span>
                  <span class="value">{val}</span>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .banner {
    background: linear-gradient(90deg,#1e3a8a,#2563eb,#1e40af);
    color: white;
    padding: 14px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    transition: transform 0.3s ease;
  }

  .banner h2 { margin: 0; font-size: 1.2rem; font-weight: 700; }
  .banner p { margin: 4px 0 0; font-size: 0.9rem; }

  .filters { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  .filter-controls { display: flex; gap: 10px; flex-wrap: wrap; }

  .filter-controls input,
  .filter-controls select {
    padding: 6px 8px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    width: auto;
    min-width: 80px;
    max-width: 125px;
  }
  .filter-controls input:hover,
  .filter-controls select:hover {
    border-color: var(--brand-blue);
    box-shadow: 0 0 5px rgba(37,99,235,0.4);
  }
  .filter-controls input:focus,
  .filter-controls select:focus {
    outline: none;
    border-color: var(--brand-blue);
    box-shadow: 0 0 8px rgba(37,99,235,0.5);
  }

  .filter-actions { display:flex; gap:10px; }

  .search-btn, .pdf-btn, .toggle-btn {
    border: none;
    padding: 8px 14px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }
  .search-btn, .pdf-btn {
    background: var(--brand-blue);
    color: white;
  }
  .search-btn:hover, .pdf-btn:hover {
    background: #1e40af;
    transform: translateY(-2px);
    box-shadow: 0 3px 6px rgba(0,0,0,0.2);
  }
  .toggle-btn {
    background: white;
    border: 1px solid var(--border);
  }
  .toggle-btn:hover {
    background: #f9fafb;
    transform: translateY(-2px);
  }

  .suggestions {
    position: absolute; background: #fff; border: 1px solid #ddd;
    border-radius: 6px; list-style: none; margin: 2px 0 0; padding: 0;
    max-height: 160px; overflow-y: auto; width: 100%; z-index: 10;
  }
  .suggestions li { padding: 6px 10px; cursor: pointer; font-size: 0.9rem; }
  .suggestions li:hover { background: #f3f4f6; }

  .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
  .card {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    background: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

  .player-name {
    margin: 0 0 8px;
    color: var(--brand-blue);
    font-weight: 700;
    cursor: pointer;
    transition: color 0.2s ease;
  }
  .player-name:hover {
    color: #1e40af;
    text-decoration: none;
  }

  .stat-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9rem; border-bottom: 1px dashed #e5e7eb; }
  .stat-row:last-child { border-bottom: none; }
  .label { font-weight: 600; color: #374151; }
  .value { color: #111827; }

  .heading {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--brand-blue);
  }

  @media (max-width: 768px) {
    .filters { flex-direction: column; align-items: flex-start; }
    .filter-actions { width: 100%; justify-content: flex-end; }
    .search-btn, .pdf-btn, .toggle-btn { width: auto; }
  }
</style>
<script lang="ts">
  import { onMount } from 'svelte';
  import jsPDF from 'jspdf';
  import html2canvas from 'html2canvas';

  const API = 'http://127.0.0.1:8000';

  let role: string = '';
  let format: string = '';
  let limit: number | null = null;

  let performers: any[] = [];
  let loading = false;
  let message = '';

  // Restore session storage
  onMount(() => {
    const savedRole = sessionStorage.getItem('tp_role');
    const savedFormat = sessionStorage.getItem('tp_format');
    const savedLimit = sessionStorage.getItem('tp_limit');

    if (savedRole) role = savedRole;
    if (savedFormat) format = savedFormat;
    if (savedLimit) limit = parseInt(savedLimit);

    if (role && format && limit) {
      loadPerformers();
    }
  });

  async function loadPerformers() {
    if (!role || !format || !limit) {
      message = 'Please select role, format and limit.';
      performers = [];
      return;
    }

    loading = true;
    message = '';
    performers = [];

    // Save to session storage
    sessionStorage.setItem('tp_role', role);
    sessionStorage.setItem('tp_format', format);
    sessionStorage.setItem('tp_limit', String(limit));

    try {
      const res = await fetch(`${API}/top-performers?format=${format}&role=${role}&limit=${limit}`);
      const data = await res.json();
      if (data.top_performers) {
        performers = data.top_performers;
      } else {
        message = 'No data available.';
      }
    } catch (err) {
      console.error(err);
      message = 'Failed to fetch performers.';
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

      pdf.setFontSize(18);
      pdf.setTextColor(37, 99, 235);
      pdf.text('CrickStatX', 10, 15);
      pdf.setTextColor(220, 38, 38);
      pdf.text(`- Top ${limit} ${format.toUpperCase()} ${role}`, 45, 15);

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

      pdf.save(`Top_${limit}_${format}_${role}.pdf`);
    } catch (err) {
      console.error('PDF export error', err);
      message = 'Export failed.';
    }
  }

  function goToProfile(name: string) {
    window.location.href = `/player-profile?name=${encodeURIComponent(name)}`;
  }

  // NEW: Clear button logic
  function clearFilters() {
    role = '';
    format = '';
    limit = null;
    performers = [];
    message = '';
    sessionStorage.removeItem('tp_role');
    sessionStorage.removeItem('tp_format');
    sessionStorage.removeItem('tp_limit');
  }
</script>

<div class="container">
  <!-- Banner -->
  <div class="banner">
    <h2>Top Performers Explorer</h2>
    <p>Select role, format & limit to view best performers.</p>
  </div>

  <!-- Filters -->
  <div class="filters">
    <div class="filter-controls">
      <select bind:value={role} on:change={loadPerformers}>
        <option value="" disabled selected>Select Role</option>
        <option value="batsman">Batsman</option>
        <option value="bowler">Bowler</option>
        <option value="allrounder">All-Rounder</option>
        <option value="wk">Wicketkeeper</option>
      </select>

      <select bind:value={format} on:change={loadPerformers}>
        <option value="" disabled selected>Select Format</option>
        <option value="test">Test</option>
        <option value="odi">ODI</option>
        <option value="t20">T20</option>
      </select>

      <input type="number" min="1" max="20" placeholder="Limit" bind:value={limit} on:change={loadPerformers} />
    </div>

    <div class="filter-actions">
      <button class="search-btn" on:click={loadPerformers}>Load</button>
      <button class="toggle-btn" on:click={clearFilters}>Clear</button>
      {#if performers.length > 0}
        <button class="pdf-btn" on:click={exportPDF}>Export PDF</button>
      {/if}
    </div>

  </div>

  {#if loading}
    <p style="text-align:center; margin-top:14px; color:var(--muted)">Loading performers...</p>
  {:else if message}
    <p style="text-align:center; margin-top:8px; color:var(--brand-red); font-weight:600;">{message}</p>
  {:else if performers.length > 0}
    <p style="font-weight:bold; margin:12px 0; color:var(--brand-blue);">
      Top {limit} {format.toUpperCase()} {role.charAt(0).toUpperCase() + role.slice(1)}s
    </p>

    <div id="export-section" class="card-grid">
      {#each performers as p, i}
        <div class="card">
          <h3 
            class="player-name" 
            on:click={() => goToProfile(p.Player || p.player)} 
            title={`Click to view profile of ${p.Player || p.player}`}
          >
            #{i + 1} {p.Player || p.player}
          </h3>
          <div class="stats">
            {#each Object.entries(p) as [key, val]}
              {#if key !== 'Player' && key !== 'player'}
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
  .banner h2 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 700;
  }
  .banner p {
    margin: 4px 0 0;
    font-size: 0.9rem;
  }

  .filters {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .filter-controls {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  select, input[type="number"] {
    padding: 8px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }
  select:hover, input[type="number"]:hover {
    border-color: var(--brand-blue);
    box-shadow: 0 0 5px rgba(37,99,235,0.4);
  }
  select:focus, input[type="number"]:focus {
    outline: none;
    border-color: var(--brand-blue);
    box-shadow: 0 0 8px rgba(37,99,235,0.5);
  }
  input[type="number"] {
    width: 80px;
    text-align: center;
  }
  .filter-actions {
    display: flex;
    gap: 10px;
  }

  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
  .card {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    background: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  .player-name {
    margin: 0 0 8px;
    color: var(--brand-blue);
    font-size: 1.05rem;
    font-weight: 700;
    cursor: pointer;
    transition: color 0.2s ease;
    position: relative;
  }
  .player-name:hover {
    color: #1e40af;
  }
  .player-name[title]:hover::after {
    content: attr(title);
    position: absolute;
    left: 0;
    bottom: -24px;
    background: #111827;
    color: #fff;
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 6px;
    white-space: nowrap;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    z-index: 10;
  }
  .stat-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.9rem;
    border-bottom: 1px dashed #e5e7eb;
  }
  .stat-row:last-child {
    border-bottom: none;
  }
  .label {
    font-weight: 600;
    color: #374151;
  }
  .value {
    color: #111827;
  }

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

  @media (max-width: 768px) {
    .filters {
      flex-direction: column;
      align-items: flex-start;
    }
    .filter-actions {
      width: 100%;
      justify-content: flex-end;
    }
    .search-btn,
    .pdf-btn,
    .toggle-btn {
      width: auto;
    }
  }
</style>

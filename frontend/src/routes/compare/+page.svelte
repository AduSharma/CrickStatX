<script lang="ts">
  import { onMount } from 'svelte';
  import jsPDF from 'jspdf';
  import html2canvas from 'html2canvas';

  const API = 'http://127.0.0.1:8000';

  let player1: string = '';
  let player2: string = '';

  let allPlayers: string[] = [];
  let suggestions1: string[] = [];
  let suggestions2: string[] = [];

  let comparisonData: any = null;
  let loading = false;
  let message: string = '';
  let activeTab: 'compare' | 'winner' = 'compare';

  onMount(async () => {
    try {
      const res = await fetch(`${API}/players`);
      if (res.ok) {
        allPlayers = await res.json();
      }
    } catch (err) {
      console.error('Error loading players:', err);
    }

    const last = sessionStorage.getItem('lastCompare');
    if (last) {
      const parsed = JSON.parse(last);
      player1 = parsed.player1;
      player2 = parsed.player2;
      comparisonData = parsed.data;
    }
  });

  $: suggestions1 =
    player1 && !allPlayers.includes(player1)
      ? allPlayers.filter((p) =>
          p.toLowerCase().includes(player1.toLowerCase())
        ).slice(0, 10)
      : [];

  $: suggestions2 =
    player2 && !allPlayers.includes(player2)
      ? allPlayers.filter((p) =>
          p.toLowerCase().includes(player2.toLowerCase())
        ).slice(0, 10)
      : [];

  async function comparePlayers() {
    if (!player1 || !player2) {
      message = 'Please select two players.';
      return;
    }
    loading = true;
    message = '';
    comparisonData = null;

    try {
      const res = await fetch(
        `${API}/compare?players=${encodeURIComponent(player1)},${encodeURIComponent(player2)}`
      );
      comparisonData = res.ok ? await res.json() : { message: 'No data' };

      sessionStorage.setItem(
        'lastCompare',
        JSON.stringify({ player1, player2, data: comparisonData })
      );
      activeTab = 'compare';
    } catch (err) {
      console.error('Compare error:', err);
      message = 'Error fetching comparison data.';
    } finally {
      loading = false;
    }
  }

  function selectSuggestion1(s: string) {
    player1 = s;
    suggestions1 = [];
  }
  function selectSuggestion2(s: string) {
    player2 = s;
    suggestions2 = [];
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
      pdf.text(`- ${player1} vs ${player2} (${activeTab})`, 45, 15);

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

      pdf.save(`${player1}_vs_${player2}_${activeTab}.pdf`);
    } catch (err) {
      console.error('PDF export error', err);
      message = 'Export failed.';
    }
  }
</script>

<div class="container">
  <div class="banner">
    <h2>Player Comparison</h2>
    <p>Select two players to compare stats & view winner summary.</p>
  </div>

  <div class="inputs">
    <div class="input-box">
      <input type="text" bind:value={player1} placeholder="First player..." />
      {#if suggestions1.length > 0}
        <ul>
          {#each suggestions1 as s (s)}
            <li on:click={() => selectSuggestion1(s)}>{s}</li>
          {/each}
        </ul>
      {/if}
    </div>

    <div class="input-box">
      <input type="text" bind:value={player2} placeholder="Second player..." />
      {#if suggestions2.length > 0}
        <ul>
          {#each suggestions2 as s (s)}
            <li on:click={() => selectSuggestion2(s)}>{s}</li>
          {/each}
        </ul>
      {/if}
    </div>

    <button class="search-btn" on:click={comparePlayers}>Compare</button>
    <button
      class="toggle-btn"
      on:click={() => {
        player1 = '';
        player2 = '';
        comparisonData = null;
        sessionStorage.removeItem('lastCompare');
      }}
    >
      Clear
    </button>
    {#if comparisonData}
      <button on:click={exportPDF} class="pdf-btn">Export PDF</button>
    {/if}
  </div>

  {#if loading}
    <p class="loading">Comparing players...</p>
  {/if}

  {#if message}
    <p class="error">{message}</p>
  {/if}

  {#if comparisonData}
    <div class="tabs">
      <button
        class:active-tab={activeTab === 'compare'}
        on:click={() => (activeTab = 'compare')}
      >
        Compare
      </button>
      <button
        class:active-tab={activeTab === 'winner'}
        on:click={() => (activeTab = 'winner')}
      >
        Winner
      </button>
    </div>

    <div id="export-section" class="export-section">
      {#if activeTab === 'compare'}
        {#each Object.entries(comparisonData.comparison) as [role, roleData] (role)}
          {#if Object.keys(roleData as any).length > 0}
            <div class="section">
              <h3 class="role-heading">{role}</h3>
              {#each Object.entries(roleData as Record<string, any>) as [fmt, stats] (fmt)}
                {#if Object.keys(stats as any).length > 0}
                  <div class="format">
                    <h4>{fmt}</h4>
                    <div class="table-wrapper">
                      <table class="data-table">
                        <thead>
                          <tr>
                            <th>Stat</th>
                            {#each comparisonData.players as p (p)}<th>{p}</th>{/each}
                          </tr>
                        </thead>
                        <tbody>
                          {#each Object.entries(stats as Record<string, any>) as [stat, values] (stat)}
                            <tr>
                              <td>{stat}</td>
                              {#each comparisonData.players as p (p)}
                                <td>{(values as Record<string, any>)[p]}</td>
                              {/each}
                            </tr>
                          {/each}
                        </tbody>
                      </table>
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}
        {/each}
      {/if}

      {#if activeTab === 'winner'}
        <h3 class="winner">Winner: {comparisonData.winner_summary.winner}</h3>
        <div class="analyze-box">{comparisonData.winner_summary.summary}</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 8px;
  }

  .banner {
    background: linear-gradient(90deg, #1e3a8a, #2563eb, #1e40af);
    color: white;
    padding: 14px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
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

  .inputs {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    max-width: 600px;
    margin: 0 auto;
  }
  .input-box {
    flex: 1;
    position: relative;
    min-width: 150px;
  }
  .input-box input {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .input-box ul {
    position: absolute;
    width: 100%;
    z-index: 10;
    border: 1px solid var(--border);
    background: white;
    border-radius: 8px;
    margin-top: 4px;
    max-height: 150px;
    overflow: auto;
  }
  .input-box li {
    padding: 6px;
    cursor: pointer;
  }

  .loading {
    text-align: center;
    margin-top: 14px;
    color: var(--muted);
  }
  .error {
    text-align: center;
    margin-top: 8px;
    color: var(--brand-red);
    font-weight: 600;
  }

  .tabs {
    display: flex;
    gap: 12px;
    margin-top: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
  }
  .data-table th,
  .data-table td {
    border: 1px solid var(--border);
    padding: 6px 8px;
    text-align: center;
    font-size: 0.9rem;
  }
  .data-table th {
    background: #f3f4f6;
    font-weight: 700;
  }
  .data-table tr:hover {
    background: #f9fafb;
  }

  .role-heading {
    color: var(--brand-blue);
    font-weight: 700;
    margin-bottom: 8px;
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
  .pdf-btn {
    background: var(--brand-blue);
    color: white;
  }
  .toggle-btn {
    background: white;
    border: 1px solid var(--border);
  }
  .search-btn {
    background: var(--brand-blue);
    color: white;
  }

  .winner {
    color: green;
    margin-bottom: 10px;
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

  @media (max-width: 600px) {
    .inputs {
      flex-direction: column;
    }
    .search-btn,
    .toggle-btn,
    .pdf-btn {
      width: 100%;
    }
    .tabs { flex-wrap: wrap; }
  }
</style>

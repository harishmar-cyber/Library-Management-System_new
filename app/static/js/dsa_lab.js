/**
 * DSA Interactive Demonstration Lab JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  initLabTabs();
  initSearchLab();
  initSortLab();
});

function initLabTabs() {
  document.querySelectorAll('.lab-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lab-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.lab-panel').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const panelId = btn.getAttribute('data-tab');
      const panel = document.getElementById(panelId);
      if (panel) panel.classList.add('active');
    });
  });
}

function initSearchLab() {
  const btnRun = document.getElementById('btnExecuteSearch');
  if (!btnRun) return;

  btnRun.addEventListener('click', async () => {
    const target = document.getElementById('searchTargetInput').value.trim();
    const algorithm = document.getElementById('searchAlgoSelect').value;
    const keyField = document.getElementById('searchKeyField').value;
    const terminal = document.getElementById('searchTraceTerminal');

    if (!target) {
      showToast('Please type a search query.', 'warning');
      return;
    }

    terminal.innerHTML = `<div class="trace-line">Executing ${algorithm.toUpperCase()} Search on field '${keyField}' for target "${target}"...</div>`;

    try {
      const res = await apiRequest('/api/dsa-lab/search/run', 'POST', {
        algorithm,
        key_field: keyField,
        target
      });

      document.getElementById('searchMetricComplexity').innerText = res.time_complexity;
      document.getElementById('searchMetricComparisons').innerText = res.comparisons;
      document.getElementById('searchMetricTime').innerText = res.elapsed_ms + ' ms';
      document.getElementById('searchMetricMatches').innerText = res.match_count;

      terminal.innerHTML = '';
      terminal.innerHTML += `<div class="trace-line" style="color:#a78bfa;">Algorithm: ${res.algorithm} | Complexity: ${res.time_complexity}</div>`;
      terminal.innerHTML += `<div class="trace-line">Total Comparisons: ${res.comparisons} | Elapsed: ${res.elapsed_ms} ms</div>`;
      terminal.innerHTML += `<div class="trace-line">----------------------------------------------------</div>`;

      res.steps.forEach(s => {
        const isMatch = s.action.includes('MATCH');
        const color = isMatch ? '#10b981' : '#e5e0f5';
        terminal.innerHTML += `<div class="trace-line ${isMatch ? 'highlight' : ''}" style="color:${color}">[Step ${s.step}] ${s.action}</div>`;
      });

      if (res.found) {
        terminal.innerHTML += `<div class="trace-line highlight" style="margin-top:8px;">✓ Search finished. Found ${res.match_count} matching records!</div>`;
      } else {
        terminal.innerHTML += `<div class="trace-line" style="color:#ef4444; margin-top:8px;">✗ Search completed. Target not found.</div>`;
      }
    } catch (err) {
      terminal.innerHTML = `<div class="trace-line" style="color:#ef4444;">Error executing search test: ${err}</div>`;
    }
  });
}

function initSortLab() {
  const btnRun = document.getElementById('btnExecuteSort');
  if (!btnRun) return;

  btnRun.addEventListener('click', async () => {
    const algorithm = document.getElementById('sortAlgoSelect').value;
    const keyField = document.getElementById('sortKeyField').value;
    const reverse = document.getElementById('sortOrderSelect').value === 'desc';
    const terminal = document.getElementById('sortTraceTerminal');

    terminal.innerHTML = `<div class="trace-line">Executing ${algorithm.toUpperCase()} SORT on catalog...</div>`;

    try {
      const res = await apiRequest('/api/dsa-lab/sort/run', 'POST', {
        algorithm,
        key_field: keyField,
        reverse
      });

      document.getElementById('sortMetricComplexity').innerText = res.time_complexity;
      document.getElementById('sortMetricComparisons').innerText = res.comparisons;
      document.getElementById('sortMetricMoves').innerText = res.moves_or_swaps;
      document.getElementById('sortMetricTime').innerText = res.elapsed_ms + ' ms';

      terminal.innerHTML = '';
      terminal.innerHTML += `<div class="trace-line" style="color:#a78bfa;">Method: ${res.algorithm} | Order: ${res.order} | Key: ${res.key_field}</div>`;
      terminal.innerHTML += `<div class="trace-line">Comparisons: ${res.comparisons} | Swaps/Moves: ${res.moves_or_swaps} | Time: ${res.elapsed_ms} ms</div>`;
      terminal.innerHTML += `<div class="trace-line">----------------------------------------------------</div>`;

      res.steps.forEach((s, idx) => {
        terminal.innerHTML += `<div class="trace-line">[Pass/Depth ${s.depth}] ${s.action}</div>`;
      });

      terminal.innerHTML += `<div class="trace-line highlight" style="margin-top:8px;">✓ Array successfully sorted! (${res.total_items} books rearranged)</div>`;

      // Update sample preview
      const preview = document.getElementById('sortedPreviewList');
      if (preview && res.sorted_items) {
        preview.innerHTML = '';
        res.sorted_items.forEach((item, i) => {
          const pill = document.createElement('div');
          pill.className = 'card';
          pill.style.padding = '8px 12px';
          pill.style.border = '1px solid var(--border-color)';
          pill.innerHTML = `<span style="font-weight:700; color:var(--color-primary);">#${i+1}</span> ${item.title} <span style="font-size:11px; color:var(--text-muted);">(${item[keyField]})</span>`;
          preview.appendChild(pill);
        });
      }
    } catch (err) {
      terminal.innerHTML = `<div class="trace-line" style="color:#ef4444;">Error executing sort test: ${err}</div>`;
    }
  });
}

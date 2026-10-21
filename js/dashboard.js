
    // Client-side filtering & modal handler
    document.addEventListener('DOMContentLoaded', () => {
      const searchInput = document.getElementById('searchFilter');
      const sportSelect = document.getElementById('sportFilter');
      const confSelect = document.getElementById('confidenceFilter');
      const verifSelect = document.getElementById('verificationFilter');
      const table = document.getElementById('matchesTable');
      const counter = document.getElementById('matchCounter');

      function filterTable() {
        if (!table) return;
        const rows = table.querySelectorAll('tbody tr');
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const sportVal = sportSelect ? sportSelect.value : 'ALL';
        const confVal = confSelect ? confSelect.value : 'ALL';
        const verifVal = verifSelect ? verifSelect.value : 'ALL';

        let visibleCount = 0;

        rows.forEach(row => {
          const sport = row.getAttribute('data-sport') || '';
          const conf = row.getAttribute('data-confidence') || '';
          const verif = row.getAttribute('data-verified') || '';
          const text = row.innerText.toLowerCase();

          const matchesQuery = !query || text.includes(query);
          const matchesSport = sportVal === 'ALL' || sport === sportVal;
          const matchesConf = confVal === 'ALL' || conf === confVal;
          const matchesVerif = verifVal === 'ALL' || (verifVal === 'Verified' && verif === 'Verified') || (verifVal === 'Flagged' && verif === 'Flagged');

          if (matchesQuery && matchesSport && matchesConf && matchesVerif) {
            row.style.display = '';
            visibleCount++;
          } else {
            row.style.display = 'none';
          }
        });

        if (counter) {
          counter.innerText = `Showing ${visibleCount} matches`;
        }
      }

      if (searchInput) searchInput.addEventListener('input', filterTable);
      if (sportSelect) sportSelect.addEventListener('change', filterTable);
      if (confSelect) confSelect.addEventListener('change', filterTable);
      if (verifSelect) verifSelect.addEventListener('change', filterTable);
    });

    // Modal display
    function openAnalysisModal(id) {
      const dataEl = document.getElementById('data-' + id);
      if (!dataEl) return;
      const m = JSON.parse(dataEl.innerText);

      const modal = document.getElementById('analysisModal');
      const title = document.getElementById('modalTitle');
      const body = document.getElementById('modalBody');

      title.innerHTML = `<span>${m.sport}: ${m.event_name}</span>`;

      const ml = m.originated_markets.moneyline || {};
      const hcap = m.originated_markets.handicap || {};
      const tot = m.originated_markets.totals || {};

      const flagHtml = m.flagged ? `
        <div class="callout callout-warning" style="margin-top:1rem;">
          <h4>⚠️ Flagged for Manual Review</h4>
          <p>${m.flag_reason}</p>
          <p style="font-size:0.8rem; margin-top:0.3rem;"><em>${m.verification_notes}</em></p>
        </div>
      ` : '';

      body.innerHTML = `
        <div style="margin-bottom:1rem;">
          <div style="font-size:0.85rem; color:#94a3b8;">${m.competition} &bull; ${m.event_date}</div>
        </div>

        <div style="background:#0f172a; padding:1rem; border-radius:8px; border:1px solid #334155; margin-bottom:1.25rem;">
          <h4 style="color:#38bdf8; margin-bottom:0.5rem; font-size:0.95rem;">Proprietary Originated Betting Lines</h4>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.85rem; margin-bottom:0.5rem;">
            <div><strong>Moneyline Home:</strong> ${ml.comp1 || '-'}</div>
            <div><strong>Moneyline Away:</strong> ${ml.comp2 || '-'}</div>
          </div>
          <div style="font-size:0.85rem; margin-bottom:0.5rem;">
            <strong>Originated Spread / Handicap:</strong> ${hcap.line || '-'}
          </div>
          <div style="font-size:0.85rem;">
            <strong>Originated Totals:</strong> ${tot.line || '-'} (${tot.over || ''} / ${tot.under || ''})
          </div>
        </div>

        <div style="margin-bottom:1.25rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <h4 style="color:#fff;">Selection & Confidence</h4>
            <span class="badge badge-conf-${m.confidence_level.toLowerCase()}">${m.confidence_level} Confidence</span>
          </div>
          <div style="font-size:1.05rem; font-weight:700; color:#38bdf8; margin-bottom:0.5rem;">
            ${m.recommended_selection}
          </div>
          <p style="line-height:1.6; color:#cbd5e1; font-size:0.9rem; background:#1e293b; padding:0.85rem; border-radius:6px; border-left:3px solid #38bdf8;">
            "${m.prediction_text}"
          </p>
        </div>

        ${flagHtml}

        <div style="border-top:1px solid #334155; padding-top:1rem; display:flex; justify-content:space-between; align-items:center; font-size:0.85rem;">
          <div>
            <strong>Source Status:</strong> <span class="badge ${m.flagged ? 'badge-verif-flagged' : 'badge-verif-ok'}">${m.flagged ? 'Flagged' : 'Verified'}</span>
          </div>
          <div style="display:flex; gap:0.75rem;">
            <a href="${m.official_source_url}" target="_blank" class="src-link official-link">Official Site ↗</a>
            <a href="${m.olbg_url}" target="_blank" class="src-link olbg-link">OLBG Tips ↗</a>
          </div>
        </div>
      `;

      modal.style.display = 'flex';
    }

    function closeAnalysisModal(e) {
      const modal = document.getElementById('analysisModal');
      if (modal) modal.style.display = 'none';
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeAnalysisModal();
    });
    
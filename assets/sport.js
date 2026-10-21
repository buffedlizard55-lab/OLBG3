const escapeText = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function renderSport() {
  const id = new URLSearchParams(location.search).get('category');
  const [sportsResponse, matchesResponse] = await Promise.all([fetch('data/sports.json'), fetch('data/matches.json')]);
  if (!sportsResponse.ok || !matchesResponse.ok) throw new Error('Category data could not be loaded.');
  const [sports, matchData] = await Promise.all([sportsResponse.json(), matchesResponse.json()]);
  const category = (sports.categories || []).find((item) => item.id === id);
  if (!category) {
    document.getElementById('sport-title').textContent = 'Category not found';
    document.getElementById('sport-description').textContent = 'This category identifier is not present in the provisional scope list.';
    document.getElementById('sport-rows').innerHTML = '<tr><td colspan="6" class="empty-cell"><strong>No category found</strong><span><a href="./">Return to the dashboard</a></span></td></tr>';
    return;
  }
  document.title = `${category.name} · OLBG Research Desk`;
  document.getElementById('sport-title').textContent = category.name;
  document.getElementById('sport-description').textContent = `Provisional category page for ${category.name}. Match records appear only after match-level official verification.`;
  document.getElementById('source-description').textContent = `${category.organization} — discovery link only; current content and event schedules were not accessed or verified.`;
  const source = document.getElementById('official-source');
  source.href = category.url;
  source.textContent = `${category.organization} website ↗`;
  const matches = (matchData.matches || []).filter((match) => match.sportId === category.id);
  document.getElementById('record-count').textContent = `${matches.length} records`;
  const tbody = document.getElementById('sport-rows');
  if (!matches.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-cell"><span class="empty-icon">⌕</span><strong>No verified matches to display</strong><span>Nothing is filled by inference; add only records with direct official match sources.</span></td></tr>';
    return;
  }
  tbody.innerHTML = matches.map((match) => {
    const marketText = Array.isArray(match.markets) ? match.markets.map((market) => `${market.marketName || ''}: ${market.ourLineOrPrice || ''}`).join('; ') : '';
    const sourceCell = match.matchSourceUrl ? `<a href="${escapeText(match.matchSourceUrl)}" target="_blank" rel="noopener noreferrer">Official source ↗</a>` : 'Unverified';
    return `<tr><td>${escapeText(match.event || '')}</td><td>${escapeText(match.participants || '')}</td><td>${escapeText(match.startTimeUtc || '')}</td><td>${escapeText(marketText)}</td><td>${escapeText(match.selection || '')}${match.confidence ? ` · ${escapeText(match.confidence)}` : ''}</td><td>${sourceCell}</td></tr>`;
  }).join('');
}
renderSport().catch((error) => {
  document.getElementById('sport-rows').innerHTML = `<tr><td colspan="6" class="empty-cell"><strong>Category data failed to load</strong><span>${escapeText(error.message)}</span></td></tr>`;
});

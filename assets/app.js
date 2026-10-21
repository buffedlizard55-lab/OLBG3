const htmlEscape = (value) => String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const flags = [
  { title: 'No match-level data', detail: 'No fixtures, schedules, results, lines, form, match histories or picks were present in the starter repository. None have been added without direct evidence.', link: null },
  { title: 'Official sources were not accessible for verification', detail: 'The build environment allowed access only to GitHub and package-host domains. The organizations below are discovery links only; their current pages and any specific event facts were not checked.', link: null },
  { title: 'Coverage taxonomy is provisional', detail: 'These categories are a practical starting set, not a comprehensive inventory of every sport OLBG covers. Match-level coverage must be established from official schedules.', link: 'https://www.olbg.com/' },
  { title: 'OLBG reverse engineering remains incomplete', detail: 'The live OLBG site could not be inspected here. Market names, site structure, collection behavior and any site-specific rules remain unverified.', link: 'https://www.olbg.com/' },
  { title: 'Independent lines and confidence picks not yet produced', detail: 'No projections or confidence labels are published until underlying evidence, model assumptions and a timestamp can be reviewed. High-confidence prose must cite its match-specific supporting sources.', link: null }
];

async function initialize() {
  const [sportsResponse, matchesResponse] = await Promise.all([
    fetch('data/sports.json'), fetch('data/matches.json')
  ]);
  if (!sportsResponse.ok || !matchesResponse.ok) throw new Error('Dashboard data could not be loaded.');
  const sportsData = await sportsResponse.json();
  const matchesData = await matchesResponse.json();
  const categories = sportsData.categories || [];
  const matches = matchesData.matches || [];
  const filter = document.getElementById('category-filter');
  const list = document.getElementById('category-list');
  const rows = document.getElementById('match-rows');

  categories.forEach((category) => {
    const option = document.createElement('option');
    option.value = category.id;
    option.textContent = category.name;
    filter.append(option);
    const item = document.createElement('div');
    item.className = 'category-chip';
    item.innerHTML = `<a class="cat-name" href="sports.html?category=${encodeURIComponent(category.id)}">${htmlEscape(category.name)} <span aria-hidden="true">↗</span></a><span class="cat-state">0 verified</span>`;
    list.append(item);
  });

  const renderMatches = () => {
    const shown = filter.value === 'all' ? matches : matches.filter((match) => match.sportId === filter.value);
    document.getElementById('nav-match-count').textContent = String(shown.length);
    if (!shown.length) {
      rows.innerHTML = '<tr><td colspan="6" class="empty-cell"><span class="empty-icon">⌕</span><strong>No verified matches to display</strong><span>Fixtures remain blank until a direct official schedule is checked and linked.</span></td></tr>';
      return;
    }
    rows.innerHTML = shown.map((match) => {
      const confidence = ['low','medium','high'].includes(match.confidence) ? match.confidence : 'unverified';
      return `<tr><td>${htmlEscape(match.sport || '')}</td><td>${htmlEscape(match.event || '')}</td><td>${htmlEscape(match.startTimeUtc || '')}</td><td>${htmlEscape(match.originatedLine || '')}</td><td>${htmlEscape(match.selection || '')} <span class="cat-state">${htmlEscape(confidence)}</span></td><td><a href="${htmlEscape(match.matchSourceUrl || '#')}" target="_blank" rel="noopener noreferrer">Official source ↗</a></td></tr>`;
    }).join('');
  };
  filter.addEventListener('change', renderMatches);
  renderMatches();
  document.getElementById('stat-matches').textContent = String(matches.length);
  document.getElementById('stat-markets').textContent = String(matches.reduce((n, match) => n + (Array.isArray(match.markets) ? match.markets.length : 0), 0));
  document.getElementById('stat-picks').textContent = String(matches.filter((match) => match.confidence === 'high' && match.selection).length);
  document.getElementById('stat-flags').textContent = String(flags.length);
  document.getElementById('nav-flag-count').textContent = String(flags.length);
  const flagList = document.getElementById('flag-list');
  flagList.innerHTML = flags.map((flag) => `<article class="flag-item"><span class="flag-mark" aria-hidden="true">⚑</span><div><strong>${htmlEscape(flag.title)}</strong><p>${htmlEscape(flag.detail)}${flag.link ? ` <a href="${htmlEscape(flag.link)}" target="_blank" rel="noopener noreferrer">Open reference link ↗</a>` : ''}</p></div></article>`).join('');
}

initialize().catch((error) => {
  document.getElementById('match-rows').innerHTML = `<tr><td colspan="6" class="empty-cell"><strong>Dashboard data failed to load</strong><span>${htmlEscape(error.message)}</span></td></tr>`;
});

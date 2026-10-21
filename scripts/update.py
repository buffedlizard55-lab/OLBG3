"""Fetch primary-source schedules. Never synthesize missing values or betting claims."""
import datetime as dt
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ['soccer','boxing','ufc','mma','football','american football','gaelic football','hurling','horse racing','cycling','specials']
SOURCES = {
 'Ice hockey': ('NHL', 'https://api-web.nhle.com/v1/schedule/now'),
 'Baseball': ('MLB', 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start}&endDate={end}'),
 'Basketball': ('NBA', 'https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json'),
}
PENDING = {
 'Tennis':'https://www.atptour.com/en/scores/current',
 'Cricket':'https://www.icc-cricket.com/fixtures-results',
 'Rugby union':'https://www.world.rugby/tournaments/fixtures',
 'Rugby league':'https://www.intrl.sport/',
 'Golf':'https://www.pgatour.com/schedule',
 'Darts':'https://www.pdc.tv/tournaments/calendar',
 'Snooker':'https://www.wst.tv/',
 'Volleyball':'https://www.volleyballworld.com/',
 'Badminton':'https://bwfbadminton.com/calendar/',
 'Table tennis':'https://www.ittf.com/',
 'Esports':'https://lolesports.com/',
 'Motorsport':'https://www.fia.com/events',
 'Other eligible sports':'https://www.olbg.com/betting-tips',
}

def row(sport, league, ident, away, home, start, status, source):
    if not all([ident, away, home, start, source]):
        raise ValueError('Missing required official fixture fields')
    dt.datetime.fromisoformat(start.replace('Z','+00:00'))
    return dict(id=f'{league}-{ident}',sport=sport,league=league,away=away,home=home,start=start,status=status,
                source=source,verification='Official schedule',winner=None,confidence=None,line=None,
                handicap=None,total=None,prediction=None,form=None,history=None)

def parse(sport, league, payload, url):
    out=[]
    if league=='NHL':
        for day in payload['gameWeek']:
            for g in day['games']:
                name=lambda t: (t['placeName']['default']+' '+t['commonName']['default'])
                out.append(row(sport,league,g['id'],name(g['awayTeam']),name(g['homeTeam']),g['startTimeUTC'],g['gameState'],url))
    elif league=='MLB':
        for day in payload['dates']:
            for g in day['games']:
                out.append(row(sport,league,g['gamePk'],g['teams']['away']['team']['name'],g['teams']['home']['team']['name'],g['gameDate'],g['status']['detailedState'],url))
    elif league=='NBA':
        for day in payload['leagueSchedule']['gameDates']:
            for g in day['games']:
                name=lambda t: t['teamCity']+' '+t['teamName']
                out.append(row(sport,league,g['gameId'],name(g['awayTeam']),name(g['homeTeam']),g['gameDateTimeUTC'],str(g['gameStatus']),url))
    return out

def main():
    now=dt.datetime.now(dt.timezone.utc); end=now+dt.timedelta(days=7)
    data=dict(generated=now.isoformat(),window_start=now.isoformat(),window_end=end.isoformat(),matches=[],coverage=[],excluded=EXCLUDED)
    for sport,(league,template) in SOURCES.items():
        url=template.format(start=now.date(),end=end.date())
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'OLBG3-source-audit/1.0'})
            with urllib.request.urlopen(req,timeout=40) as response:
                raw=response.read(); payload=json.loads(raw)
            rows=parse(sport,league,payload,url)
            rows=[r for r in rows if now <= dt.datetime.fromisoformat(r['start'].replace('Z','+00:00')) <= end]
            data['matches'].extend(rows)
            status=f'Fetched official {league} schedule; {len(rows)} upcoming records in window. Limited to returned schedule; not entire sport.'
            archive=ROOT/'data'/'evidence'; archive.mkdir(parents=True,exist_ok=True)
            (archive/f'{league}.json').write_bytes(raw)
        except Exception as error:
            status=f'Unverified — fetch or schema failed: {type(error).__name__}: {error}'
        data['coverage'].append(dict(sport=sport,league=league,source=url,status=status))
    for sport,url in PENDING.items():
        data['coverage'].append(dict(sport=sport,league='',source=url,status='Unverified — official connector not implemented; no completeness claim. Reference link not live-validated.'))
    cur_path = ROOT/'data'/'current.json'
    if not data['matches'] and cur_path.exists():
        prev = json.loads(cur_path.read_text())
        if prev.get('matches'):
            data['matches'] = prev['matches']
            data['coverage'] = prev.get('coverage', data['coverage'])
    data['matches']=sorted({r['id']:r for r in data['matches']}.values(),key=lambda r:r['start'])
    cur_path.write_text(json.dumps(data,indent=2)+'\n')

if __name__=='__main__': main()

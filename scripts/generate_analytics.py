#!/usr/bin/env python3
"""Generate GitHub profile analytics as self-hosted SVGs.

Uses GitHub's GraphQL API, GITHUB_TOKEN and only the Python standard library.
Public data only. No fabricated counts. Existing SVGs remain when API calls fail.
"""
import json
import os
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USERNAME = os.environ.get('GH_USERNAME', 'SantoshThkr')
TOKEN = os.environ.get('GH_TOKEN', '')
ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'analytics'
ASSETS.mkdir(parents=True, exist_ok=True)

BG = '#0B1020'
PANEL = '#17263B'
STROKE = '#2C425C'
TEXT = '#F2F6FF'
MUTED = '#A3B3C9'
TEAL = '#2DD4BF'
BLUE = '#55BFF7'
VIOLET = '#A78BFA'
HEAT = ['#17263B','#164D55','#1D7477','#29A6A3','#38DFC3']
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif'


def graphql(query, variables):
    if not TOKEN:
        raise RuntimeError('GH_TOKEN is missing. Use the automatic GitHub Actions GITHUB_TOKEN.')
    body = json.dumps({'query':query,'variables':variables}).encode('utf-8')
    req = Request('https://api.github.com/graphql', data=body, headers={
        'Authorization':f'Bearer {TOKEN}',
        'Content-Type':'application/json',
        'Accept':'application/vnd.github+json',
        'User-Agent':'SantoshThkr-profile-analytics'
    })
    try:
        with urlopen(req, timeout=30) as response:
            data=json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f'GitHub API returned HTTP {exc.code}') from exc
    except URLError as exc:
        raise RuntimeError(f'Could not reach GitHub API: {exc.reason}') from exc
    if data.get('errors'):
        raise RuntimeError('GitHub GraphQL error: ' + json.dumps(data['errors'])[:1000])
    return data['data']


def t(x,y,label,size=20,color=TEXT,weight=400,anchor=None,spacing=None):
    extras = ''
    if anchor: extras += f' text-anchor="{anchor}"'
    if spacing is not None: extras += f' letter-spacing="{spacing}"'
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}"{extras}>{escape(str(label))}</text>')


def svg(width,height,body,title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title,quote=True)}">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            '<stop stop-color="#0B1020"/><stop offset="0.65" stop-color="#132238"/>'
            '<stop offset="1" stop-color="#18162F"/></linearGradient></defs>'
            f'<rect width="{width}" height="{height}" rx="20" fill="url(#g)"/>'
            f'{body}<rect x="1" y="1" width="{width-2}" height="{height-2}" '
            f'rx="19" fill="none" stroke="{STROKE}" stroke-width="1.5"/></svg>\n')


def save(name,content):
    temp=ASSETS/(name+'.tmp')
    temp.write_text(content,encoding='utf8')
    temp.replace(ASSETS/name)


def stats_query(cursor=None):
    query='''query($login: String!, $cursor: String) {
      user(login:$login) {
        repositories(first:100,after:$cursor,ownerAffiliations:OWNER,privacy:PUBLIC) {
          totalCount pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
        contributionsCollection {
          contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
          totalCommitContributions
        }
      }
    }'''
    data=graphql(query,{'login':USERNAME,'cursor':cursor})
    user=data.get('user')
    if not user: raise RuntimeError(f'GitHub user {USERNAME} not found')
    return user


def load_stats():
    user=stats_query()
    repos=user['repositories']
    count=repos['totalCount']
    stars=sum(r['stargazerCount'] for r in repos['nodes'])
    while repos['pageInfo']['hasNextPage']:
        repos=stats_query(repos['pageInfo']['endCursor'])['repositories']
        stars+=sum(r['stargazerCount'] for r in repos['nodes'])
    collection=user['contributionsCollection']
    calendar=collection['contributionCalendar']
    weeks=calendar['weeks']
    days=sorted((d for w in weeks for d in w['contributionDays']),key=lambda d:d['date'])
    return {
        'repos':count,'stars':stars,
        'contributions':calendar['totalContributions'],
        'commits':collection['totalCommitContributions'],
        'weeks':weeks,'days':days,
    }


def streak_counts(days):
    values={date.fromisoformat(d['date']):d['contributionCount'] for d in days}
    today=datetime.now(timezone.utc).date()
    point=today if values.get(today,0)>0 else today-timedelta(days=1)
    current=0
    while point in values and values[point]>0:
        current+=1
        point-=timedelta(days=1)
    best=run=0
    for day in days:
        if day['contributionCount']>0:
            run+=1
            best=max(best,run)
        else: run=0
    return current,best


def generate_overview(metrics):
    current,best=streak_counts(metrics['days'])
    data=[
        ('PUBLIC REPOS',metrics['repos'],TEAL),
        ('REPO STARS',metrics['stars'],BLUE),
        ('CONTRIBUTIONS / YEAR',metrics['contributions'],VIOLET),
        ('COMMITS / YEAR',metrics['commits'],BLUE),
        ('CURRENT STREAK',f'{current} days',TEAL),
        ('BEST STREAK / YEAR',f'{best} days',VIOLET),
    ]
    body=t(37,53,'GitHub overview',28,TEXT,750)
    body+=t(1162,53,'PUBLIC ACTIVITY · LAST 12 MONTHS',13,MUTED,650,'end',1)
    for i,(label,value,color) in enumerate(data):
        col,row=i%3,i//3
        x=36+col*387;y=83+row*89
        body+=f'<rect x="{x}" y="{y}" width="365" height="76" rx="14" fill="{PANEL}" stroke="{STROKE}"/>'
        body+=f'<rect x="{x}" y="{y+9}" width="4" height="57" rx="2" fill="{color}"/>'
        body+=t(x+22,y+25,label,12,MUTED,700,spacing=.9)
        body+=t(x+22,y+61,f'{value:,}' if isinstance(value,int) else value,29,color,750)
    save('overview.svg',svg(1200,276,body,'GitHub overview'))


def generate_heatmap(metrics):
    weeks=metrics['weeks']; total=metrics['contributions']
    width=1200; startx=73; top=91; cell=12; gap=4; step=cell+gap
    body=t(37,47,'Contribution calendar',28,TEXT,750)
    body+=t(1163,47,f'{total:,} contributions · past year',14,MUTED,500,'end')
    for dow,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]:
        body+=t(35,top+dow*step+10,label,12,MUTED)
    previous_month=None
    for ix,w in enumerate(weeks):
        if w['contributionDays']:
            dt=date.fromisoformat(w['contributionDays'][0]['date'])
            if dt.month!=previous_month and ix%3<3:
                body+=t(startx+ix*step,75,dt.strftime('%b'),12,MUTED,550)
                previous_month=dt.month
        for day in w['contributionDays']:
            d=date.fromisoformat(day['date'])
            dow=(d.weekday()+1)%7
            n=day['contributionCount']
            level=0 if n==0 else 1 if n==1 else 2 if n<=3 else 3 if n<=7 else 4
            x=startx+ix*step;y=top+dow*step
            body+=f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{HEAT[level]}"><title>{d.isoformat()}: {n} contributions</title></rect>'
    body+=t(971,231,'Less',12,MUTED)
    for i,c in enumerate(HEAT):
        body+=f'<rect x="{1009+18*i}" y="219" width="13" height="13" rx="3" fill="{c}"/>'
    body+=t(1112,231,'More',12,MUTED)
    save('contributions.svg',svg(1200,250,body,'Daily GitHub contribution calendar'))


def draw_bars(values,labels,title,subtitle,name,color,unit):
    w,h=1200,272
    body=t(37,48,title,28,TEXT,750)
    body+=t(1163,48,subtitle,14,MUTED,500,'end')
    maxval=max(max(values,default=0),1)
    left=60;right=1149;top=87;bottom=219
    body+=f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{STROKE}"/>'
    for p in (0.25,0.5,0.75,1):
        y=bottom-(bottom-top)*p
        body+=f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" stroke="#294057" opacity=".5" stroke-dasharray="3 7"/>'
    step=(right-left)/max(len(values),1)
    bw=min(23 if len(values)<20 else 12,step*.72)
    for i,val in enumerate(values):
        x=left+i*step+(step-bw)/2
        height=(bottom-top)*(val/maxval) if val else 2.0
        y=bottom-height
        opacity='1' if val else '.44'
        body+=f'<rect x="{x:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{height:.2f}" rx="3" fill="{color}" opacity="{opacity}"><title>{escape(str(labels[i]))}: {val} {unit}</title></rect>'
    if len(values)<20:
        for i,label in enumerate(labels):
            body+=t(round(left+(i+.5)*step,1),243,label,12,MUTED,500,'middle')
    else:
        body+=t(left,243,labels[0],13,MUTED)
        body+=t(right,243,labels[-1],13,MUTED,anchor='end')
    save(name,svg(w,h,body,title))


def generate_weekly(metrics):
    weeks=metrics['weeks']
    values=[sum(d['contributionCount'] for d in week['contributionDays']) for week in weeks]
    labels=[f'Week {i+1}' for i in range(len(values))]
    labels[0]='Oldest';labels[-1]='Most recent'
    draw_bars(values,labels,'Weekly activity','CONTRIBUTIONS PER WEEK · LAST 12 MONTHS',
              'weekly-activity.svg',TEAL,'contributions')


def past_months(n=12):
    now=datetime.now(timezone.utc)
    current=date(now.year,now.month,1)
    months=[]
    for backwards in range(n-1,-1,-1):
        y=current.year; m=current.month-backwards
        while m<1: y-=1;m+=12
        first=date(y,m,1)
        end_exclusive=date(y+1,1,1) if m==12 else date(y,m+1,1)
        last=end_exclusive-timedelta(days=1)
        months.append((first,last))
    return months


def load_monthly_commits():
    months=past_months()
    aliases=[]
    for i,(first,last) in enumerate(months):
        start=first.isoformat()+'T00:00:00Z'
        finish=last.isoformat()+'T23:59:59Z'
        aliases.append(f'm{i}: contributionsCollection(from:"{start}", to:"{finish}") '
                       '{ totalCommitContributions }')
    query='query($login:String!) { user(login:$login) { '+ ' '.join(aliases) +' } }'
    data=graphql(query,{'login':USERNAME})
    user=data.get('user')
    if not user: raise RuntimeError('GitHub user not found in monthly commit query')
    return [user[f'm{i}']['totalCommitContributions'] for i in range(len(months))], [first.strftime('%b %y') for first,_ in months]


def generate_monthly_commits():
    values,labels=load_monthly_commits()
    draw_bars(values,labels,'Commit activity','GITHUB COMMIT CONTRIBUTIONS · LAST 12 CALENDAR MONTHS',
              'monthly-commits.svg',BLUE,'commit contributions')


def main():
    metrics=load_stats()  # Make no changes if the core API query fails.
    generate_overview(metrics)
    generate_heatmap(metrics)
    generate_weekly(metrics)
    # Monthly commit query is separate. A temporary issue won't break the other charts.
    try:
        generate_monthly_commits()
    except (RuntimeError,ValueError,KeyError) as exc:
        print('Monthly commit chart could not be refreshed; previous SVG retained:',exc)
    print(f'Updated {USERNAME} analytics. Public repos={metrics["repos"]}; stars={metrics["stars"]}; '
          f'year contributions={metrics["contributions"]}; year commits={metrics["commits"]}')


if __name__ == '__main__':
    main()

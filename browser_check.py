"""Playwright checks of actual Vue UI with MOCKED HTTP (navigation blocked in sandbox).
Run: python evidence/browser_check.py. The API persistence is tested separately by pytest.
All test messages are fictional and the browser has no internet/localhost access.
"""
from pathlib import Path
import json
import re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
FRONTEND=ROOT.parent/'frontend'
results=[]
def record(name, expected, observed, passed):
    results.append({'check':name,'expected':expected,'observed':observed,'passed':bool(passed)})

# This mocked transport imitates server endpoints; it is deliberately NOT presented as proof of the live API/UI integration.
mock_transport=r'''
const storage={};
Object.defineProperty(window,'localStorage',{configurable:true,value:{
  getItem:(k)=>Object.prototype.hasOwnProperty.call(storage,k)?storage[k]:null,
  setItem:(k,v)=>{storage[k]=String(v)},removeItem:(k)=>{delete storage[k]}
}});
let seq=0;const sessions=[],messages=[];
window.fetch=async(url,opts={})=>{
 const method=opts.method||'GET',body=opts.body?JSON.parse(opts.body):null;
 let status=200,data=null;
 if(url==='/api/sessions'&&method==='POST') {
  data={id:++seq,skill_type:'breathing',status:'in_progress',started_at:'2026-10-26T15:20:00Z',actual_exercise_seconds:null,planned_seconds:70}; sessions.unshift(data);
 } else if(url==='/api/sessions'&&method==='GET') data=sessions;
 else if(url.startsWith('/api/sessions/')&&method==='PATCH') {
  const row=sessions.find(x=>x.id===Number(url.split('/').pop())); Object.assign(row,body);data=row;
 } else if(url==='/api/chat'&&method==='POST') {
  messages.push({id:messages.length+1,session_id:body.session_id,role:'user',content:body.text,response_mode:'user'});
  data={reply:'The chat is unavailable right now. You can return home, review your activity, or open Crisis support at any time.',response_mode:'fallback'};
  messages.push({id:messages.length+1,session_id:body.session_id,role:'assistant',content:data.reply,response_mode:'fallback'});
 } else if(url.startsWith('/api/messages?'))data=messages.filter(x=>x.session_id===Number(url.split('=')[1]));
 else {status=404;data={error:'Not found'}};
 return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}})
}
'''

def inject(page):
    html=(FRONTEND/'index.html').read_text()
    html=re.sub(r'<script src="[^"]+"></script>','',html)
    html=re.sub(r'<link rel="stylesheet"[^>]+>','',html)
    page.set_content(html)
    page.add_style_tag(content=(FRONTEND/'style.css').read_text())
    page.add_script_tag(content=mock_transport)
    page.add_script_tag(content=(FRONTEND/'vue.global.js').read_text())
    page.add_script_tag(content=(FRONTEND/'app.js').read_text())
    page.get_by_role('heading',name='One small step').wait_for()

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1050,'height':800},reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    inject(page)
    page.screenshot(path=str(ROOT/'01-home-mocked.png'),full_page=True)
    record('Vue screen loads with mocked API','Home and crisis link visible',
           'Home heading and crisis link visible',page.get_by_role('link',name='Crisis support').is_visible())
    page.get_by_role('button',name='Start 4–6 breathing').click()
    page.get_by_role('button',name='Pause').wait_for()
    page.screenshot(path=str(ROOT/'02-exercise-mocked.png'),full_page=True)
    page.get_by_role('button',name='Pause').click()
    page.get_by_role('heading',name='Paused').wait_for()
    page.get_by_role('button',name='Resume').click()
    page.get_by_role('button',name='Leave exercise').click()
    page.get_by_role('heading',name='You chose to stop.').wait_for()
    page.screenshot(path=str(ROOT/'03-left-early-mocked.png'),full_page=True)
    record('Leave early screen','No penalty or completion force','You chose to stop.',True)
    page.get_by_label('Fictional message (optional)').fill('Fictional test: the pace felt fast.')
    page.get_by_role('button',name='Send fictional message').click()
    page.get_by_text('Response mode: fallback').wait_for()
    page.screenshot(path=str(ROOT/'04-model-failure-mocked.png'),full_page=True)
    record('Mocked model failure UI','Fallback label and persistent crisis link displayed',
           'fallback and Crisis support visible',page.get_by_role('link',name='Crisis support').is_visible())
    page.get_by_role('button',name='History').click()
    page.get_by_text('left early',exact=False).wait_for()
    page.screenshot(path=str(ROOT/'05-history-mocked.png'),full_page=True)
    page.get_by_role('button',name='View chat').first.click()
    page.get_by_text('Fictional test: the pace felt fast.',exact=False).wait_for()
    record('Mocked history screen','Recorded early exit and conversation visible','Both visible',True)
    record('Unhandled browser JS errors','None expected', '; '.join(errors) or 'none',not errors)

    # Simulated clock; checks UI timing logic, NOT a physical 70-second stopwatch.
    timed=browser.new_page(viewport={'width':1050,'height':800},reduced_motion='reduce')
    timed.clock.install()
    inject(timed)
    timed.get_by_role('button',name='Start 4–6 breathing').click()
    timed.get_by_role('button',name='Pause').wait_for()
    timed.clock.run_for(71000)
    timed.get_by_role('heading',name='You reached the end.').wait_for(timeout=15000)
    duration=timed.locator('text=/Guided time:/').first.inner_text()
    record('Virtual-clock exercise duration','Full exercise completes at about 70s simulated app time',duration,'70 seconds' in duration)
    timed.screenshot(path=str(ROOT/'06-completed-virtual-clock-mocked.png'),full_page=True)
    # Static crisis page visually inspected separately; pure HTML with no JavaScript required.
    support=browser.new_page(viewport={'width':1050,'height':800})
    support_html=(FRONTEND/'support.html').read_text()
    support_html=re.sub(r'<link rel="stylesheet"[^>]+>','',support_html)
    support.set_content(support_html)
    support.add_style_tag(content=(FRONTEND/'style.css').read_text())
    support.screenshot(path=str(ROOT/'07-static-support.png'),full_page=True)
    record('Static crisis page without JS','Support heading and US 988 information visible',
           'Static support and 988 visible',support.get_by_role('heading',name='Crisis support information').is_visible() and '988' in support.locator('body').inner_text())
    browser.close()

(ROOT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
for r in results:print(('PASS' if r['passed'] else 'FAIL'),r['check'],'—',r['observed'])
print('TOTAL',sum(r['passed'] for r in results),'/',len(results))

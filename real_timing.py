"""70-second real wall-clock browser run with mocked HTTP; no live backend fetch."""
import time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
p=Path(__file__).parent
preamble=(p/'browser_check.py').read_text().split('with sync_playwright() as playwright:')[0]
scope={'__file__':str(p/'browser_check.py')}
exec(preamble,scope)
inject=scope['inject']
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1050,'height':800},reduced_motion='reduce')
 inject(page)
 page.get_by_role('button',name='Start 4–6 breathing').click()
 page.get_by_role('button',name='Pause').wait_for()
 t0=time.perf_counter()
 page.get_by_role('heading',name='You reached the end.').wait_for(timeout=80000)
 t1=time.perf_counter()
 text=page.locator('text=/Guided time:/').first.inner_text()
 screenshot=str(p/'08-completed-real-clock-mocked.png')
 page.screenshot(path=screenshot,full_page=True)
 result={'wall_time_seconds_from_exercise_visible_to_completion_visible':round(t1-t0,2),
         'display':text,'http':'mocked','browser':'Chromium/Playwright','fictional_scenario':True}
 (p/'real-timing-results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result)
 browser.close()

from playwright.sync_api import sync_playwright
from pathlib import Path
import json, time
folder=Path('/mnt/data/se-primer')
css=(folder/'src/style.css').read_text().replace("@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');",'')
tutor=(folder/'src/tutor.mjs').read_text().replace('export const stagePrompts','const stagePrompts').replace('export function tutorRespond','function tutorRespond')
main=(folder/'src/main.js').read_text().replace("import { tutorRespond, stagePrompts } from './tutor.mjs';",'')
def visit(page):
 page.set_content('<html lang="tr"><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>')
 page.add_style_tag(content=css)
 page.evaluate(tutor+'\n'+main)
out=Path('/mnt/data/se-primer/evidence'); out.mkdir(exist_ok=True)
checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for case in range(8):
  page=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
  
  err=[];page.on('pageerror',lambda e:err.append(str(e)))
  visit(page); page.get_by_test_id('start').click()
  seq=''.join('B' if case&(1<<i) else 'A' for i in range(3))
  if case==0:page.screenshot(path=str(out/'01-scene.png'),full_page=True)
  for c in seq:
   page.get_by_test_id('option-'+c).click()
   assert page.get_by_test_id('feedback').count()==1
   page.get_by_test_id('next').click()
  assert page.get_by_test_id('ending').count()==1
  assert ('SON A' if seq=='AAA' else 'SON B') in page.locator('body').inner_text(),seq
  assert len(page.locator('.summary-row').all())==3
  if case==0:page.screenshot(path=str(out/'02-success.png'),full_page=True)
  if case==7:page.screenshot(path=str(out/'03-risk.png'),full_page=True)
  page.get_by_test_id('restart').click()
  assert page.get_by_test_id('intro').count()==1
  assert not err,err
  checks.append({'case':seq,'result':'PASS','errors':err})
  page.close()
 page=b.new_page(viewport={'width':390,'height':844});visit(page);page.screenshot(path=str(out/'00-intro.png'),full_page=True)
 page.get_by_test_id('role').select_option('tester');page.get_by_test_id('goal').select_option('security');page.get_by_test_id('start').click(); assert 'Test mühendisi olarak' in page.locator('body').inner_text();assert page.get_by_test_id('hint').count()==1
 page.locator('#student-input').fill('Doğru seçenek A mı?');page.get_by_test_id('ask-tutor').click();assert 'teknik kanıt' in page.locator('#tutor-response').inner_text()
 checks.append({'case':'personalization+student tutor input','result':'PASS'})
 visit(page);page.get_by_test_id('level').select_option('expert');page.get_by_test_id('start').click();assert '60 SN' in page.get_by_test_id('timer').inner_text()
 checks.append({'case':'expert 60 second countdown begins','result':'PASS'});page.close()
 b.close()
(out/'browser-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))

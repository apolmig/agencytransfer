"""Preview or live UX checks; run with Playwright on the publication runner."""
import hashlib,json,os,pathlib,shutil,subprocess,time,urllib.request
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'publication-browser-review';OUT.mkdir(exist_ok=True)
mode=os.environ.get('REVIEW_MODE','preview');process=None
if mode=='preview':
 serve=ROOT/'_publication_preview';serve.mkdir(exist_ok=True)
 link=serve/'agencytransfer'
 if not link.exists():link.symlink_to(ROOT/'dist',target_is_directory=True)
 process=subprocess.Popen(['python','-m','http.server','8765','--directory',str(serve)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 time.sleep(1);base='http://127.0.0.1:8765/agencytransfer/'
else:base='https://miguelguerrero.eu/agencytransfer/'
report={'mode':mode,'base':base,'pages':[],'checks':[],'result':'pending'}
try:
 with sync_playwright() as p:
  chrome=shutil.which('google-chrome') or shutil.which('chromium')
  browser=p.chromium.launch(executable_path=chrome)
  for w in (1440,390,320):
   ctx=browser.new_context(viewport={'width':w,'height':1000 if w==1440 else 844})
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for slug in ('','references/','research/part-i/','research/part-iv/','paper/','outputs/','explainers/','media/cde-rift-animation/'):
    response=page.goto(base+slug,wait_until='networkidle',timeout=30000)
    assert response.status==200,(slug,response.status)
    page.locator('h1').first.wait_for()
    if slug=='references/':page.locator('.reference-results>ol>li').first.wait_for()
    sw=page.evaluate('document.documentElement.scrollWidth');assert sw<=w+1,(slug,w,sw,'overflow')
    assert 'draft' in page.locator('body').inner_text().lower(),(slug,'draft absent')
    if slug=='':
     cards=page.locator('.v2-part-card a');assert cards.count()==4
     assert cards.nth(1).get_attribute('target')=='_blank'
     assert cards.nth(1).get_attribute('href')=='/agencytransfer/registry/'
     assert page.locator('.v2-hero-art img').evaluate('(e)=>e.complete&&e.naturalWidth>0')
     assert page.locator('a[href$="outputs/#poster"]').count()==0
    if slug=='research/part-i/':
     assert page.locator('h1').inner_text()=='How far can an adversarial actor go with $10?'
     assert 'Pretty far, actually.' in page.locator('.v2-page-lead').inner_text()
     page.locator('.budget-boundary summary').click()
     assert 'US$500' in page.locator('.budget-boundary').inner_text()
     page.locator('.budget-boundary summary').click()
    if slug=='references/':
     assert page.locator('.reference-results>ol>li').count()==25
     page.get_by_role('button',name='Cited in the flagship',exact=True).click()
     page.wait_for_timeout(80)
     assert '64 source records' in page.locator('.reference-count').inner_text()
     search=page.get_by_placeholder('For example: persuasion, Salvi, provenance…')
     search.fill('Nouwens');page.wait_for_timeout(80)
     assert page.locator('.reference-results>ol>li').count()==1
     page.get_by_role('button',name='Clear filters',exact=True).click();page.wait_for_timeout(80)
     page.get_by_role('button',name='Next',exact=True).click()
     assert 'Page 2 of' in page.locator('.reference-pagination').inner_text()
     page.get_by_role('button',name='Clear filters',exact=True).click()
     search.fill('zzzz-unmatched-11998');assert page.get_by_text('No matching source.',exact=False).is_visible()
     page.get_by_role('button',name='Clear filters',exact=True).click()
    if slug=='research/part-iv/':
     assert page.locator('.policy-example').count()==6
     assert all(x.get_attribute('open') is None for x in page.locator('.policy-example').all())
     for item in page.locator('.policy-example').all():
      item.locator('summary').click();assert item.locator('a').first.is_visible()
      item.locator('summary').click()
    if slug=='paper/':
     assert page.locator('.paper-coming-soon').inner_text() == 'Full working paper — coming soon'
     assert page.locator('a[href$="v1.5-20260901.pdf"]').count()==0
     assert page.locator('a[href$="v1.3-20260901.pdf"]').count()==0
     assert page.locator('a[href$="references/?scope=flagship"]').count()==1
    if slug=='explainers/':
     frame=page.frame_locator('iframe');frame.locator('#play').wait_for()
     assert frame.locator('#play').inner_text()=='Play'
    if slug=='media/cde-rift-animation/':
     assert page.locator('.v2-header nav a').count()==6
     frame=page.frame_locator('iframe')
     assert frame.locator('#play').inner_text()=='Play'
     page.wait_for_timeout(300);assert frame.locator('#time').inner_text()=='00:00 / 01:33'
     for i in range(6):
      frame.locator(f'[data-chapter="{i}"]').click()
      assert frame.locator(f'[data-chapter="{i}"]').get_attribute('aria-pressed')=='true'
     assert frame.locator('#time').inner_text()=='01:15 / 01:33'
     frame.locator('#play').click();page.wait_for_timeout(450);frame.locator('#play').click()
     assert frame.locator('#play').inner_text()=='Play'
     frame.locator('#restart').click()
     assert frame.locator('.landscape img').evaluate('(e)=>e.naturalWidth>0')
     assert not frame.locator('.player-heading').is_visible()
    report['pages'].append({'path':slug,'viewport':w,'status':response.status,'scrollWidth':sw,'title':page.locator('h1').first.inner_text()})
    page.evaluate("document.documentElement.style.scrollBehavior='auto';if(document.activeElement instanceof HTMLElement)document.activeElement.blur();window.scrollTo(0,0)")
    page.wait_for_timeout(100)
    name=(slug or 'home').strip('/').replace('/','-')
    if slug!='references/':page.screenshot(path=str(OUT/f'{name}-{w}.png'),full_page=True)
    else:page.screenshot(path=str(OUT/f'{name}-{w}.png'))
   assert not errors,errors
   ctx.close()
  ctx=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page=ctx.new_page()
  page.goto(base+'media/cde-rift-animation/',wait_until='networkidle')
  frame=page.frame_locator('iframe');assert 'Reduced motion' in frame.locator('#motion-note').inner_text();assert frame.locator('#play').inner_text()=='Play';ctx.close()
  ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});page=ctx.new_page()
  page.goto(base+'media/cde-rift-animation/');assert page.locator('.reading-fallback nav a').count()==6;assert page.frame_locator('iframe').locator('#text-agency').is_visible()
  page.goto(base+'research/references.html');assert page.locator('ol>li').count()==431;ctx.close()
  ctx=browser.new_context(viewport={'width':1280,'height':850});page=ctx.new_page()
  # A stable entry link must work outside the first result page.
  data=json.loads((ROOT/'public/research/references.json').read_text());target=data['records'][-1]['id']
  page.goto(base+'references/#'+target,wait_until='networkidle');page.locator('#'+target).wait_for()
  assert page.locator('#'+target).is_visible()
  page.get_by_placeholder('For example: persuasion, Salvi, provenance…').fill('Salvi');page.wait_for_timeout(100)
  assert not page.evaluate('location.hash'), 'Filtering should clear an old entry fragment'
  assert page.locator('.reference-results>ol>li').count()>0
  ctx.close();browser.close()
 report['checks']=['Manual playback; six chapters; correct minute timer','Reduced-motion setting','No-JavaScript transcript and full bibliography','Reference search, scope, pagination, reset and deep links','Independent new-tab Registry entry','Unpublished artifact labels','Draft notices and current/older manuscript links']
 files={
 'media/cde-gap3-hero-1672.webp':'5d41200d1aa40f4e76117cf542166c33905b7ec6343d98ba5718eff2b65f13ae',
 'research/harmful-manipulation-election-security-v1.3-20260901.pdf':'9049528ada708e9c5d591fac2343ef53d89a86d5e1d2703d22b1ef84bf701c5e',
 'research/harmful-manipulation-election-security-v1.5-20260901.pdf':'f222f33fcec2a6bd83110d7b9efd188d8a11bb1fcdba7dafeb8e43e00e3eb40b',
 'research/p4-source-linked-review-20260901.xlsx':'2104cb1851d5661ddacd0ae0b616e11a9c8ed6ef904d988d1ff7a305f9cdc421',
 }
 report['files']=[]
 for name,digest in files.items():
  with urllib.request.urlopen(base+name,timeout=40) as response:raw=response.read()
  assert hashlib.sha256(raw).hexdigest()==digest,name
  report['files'].append({'path':name,'sha256':digest,'bytes':len(raw)})
 report['result']='pass'
except Exception as e:report['result']='fail';report['error']=str(e);raise
finally:
 (OUT/'report.json').write_text(json.dumps(report,indent=2))
 if process:process.terminate()
print(json.dumps(report,indent=2))

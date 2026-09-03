"""Browser acceptance checks for the unpublished working-paper presentation."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.getenv('REVIEW_BASE','http://127.0.0.1:8765/agencytransfer/')
OUT=Path(os.getenv('REVIEW_OUTPUT',str(ROOT/'paper-status-review')))
ROUTES=('', 'paper/', 'about/', 'references/', 'outputs/', 'research/', 'research/part-i/', 'research/part-iii/', 'research/part-iv/', 'updates/', 'explainers/')
WIDTHS=tuple(map(int,os.getenv('REVIEW_WIDTHS','1440,390').split(',')))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    proc=None
    if BASE.startswith('http://127.0.0.1'):
        directory=ROOT/'_paper_preview';directory.mkdir(exist_ok=True)
        link=directory/'agencytransfer'
        if not link.exists():link.symlink_to(ROOT/'dist',target_is_directory=True)
        proc=subprocess.Popen(['python','-m','http.server','8765','--directory',str(directory)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.6)
    report={'base':BASE,'checks':[],'files':[],'result':'pending'}
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'))
            for width in WIDTHS:
                context=browser.new_context(viewport={'width':width,'height':1000 if width>800 else 844},reduced_motion='reduce')
                page=context.new_page();errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                for route in ROUTES:
                    response=page.goto(BASE+route,wait_until='networkidle',timeout=30000)
                    assert response and response.status==200,(route,'HTTP')
                    page.locator('h1').first.wait_for()
                    assert page.locator('h1').count()==1,(route,'heading')
                    text=page.locator('main').text_content() or ''
                    assert not re.search(r'\bv1\.\d+',text,re.I),(route,'numbered manuscript label')
                    assert not re.search(r'\bv1\.\d+',page.title(),re.I),(route,'title')
                    assert 'draft' in (page.locator('body').inner_text()).lower(),(route,'draft status')
                    assert page.locator('a[href*="harmful-manipulation-election-security"][href$=".pdf"]').count()==0,(route,'advertised manuscript download')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),(route,width,'overflow')
                    assert page.locator('.v2-header').count()==1,(route,'shared header')
                    if route=='':
                        assert page.locator('.v2-parts--simple .v2-part-card').count()==4
                        assert page.locator('a[href$="/registry/"]').first.get_attribute('target')=='_blank'
                        assert page.locator('.v2-hero-art img').get_attribute('src').endswith('cde-gap3-hero-1672.webp')
                    if route=='paper/':
                        status=page.locator('.paper-coming-soon')
                        assert status.inner_text()=='Full working paper — coming soon'
                        assert status.evaluate('(el) => el.tagName')=='SPAN' and status.get_attribute('href') is None
                        assert page.locator('main svg').count()==0,'Paper SVG still present'
                        image=page.locator('.paper-concept-figure img')
                        image.scroll_into_view_if_needed()
                        page.wait_for_function("document.querySelector('.paper-concept-figure img').naturalWidth > 0")
                        assert image.get_attribute('srcset') and image.get_attribute('width')=='1672'
                        assert image.get_attribute('height')=='941'
                        assert page.locator('.paper-concept-figure a').first.get_attribute('target')=='_blank'
                        citation=page.locator('.paper-citation').inner_text()
                        assert 'Unpublished draft.' in citation and len(citation)<210
                    if route=='references/':
                        page.locator('.reference-count').wait_for()
                        assert '431 source records' in page.locator('.reference-count').inner_text()
                        page.locator('input[type="search"]').fill('Salvi')
                        page.wait_for_timeout(120)
                        assert page.locator('.reference-results li').count()>0
                        page.get_by_role('button',name='Clear filters').click()
                    if route=='research/part-i/':
                        assert page.locator('h1').inner_text()=='How far can an adversarial actor go with $10?'
                    report['checks'].append({'path':route,'width':width,'status':200})
                    if route in ('paper/','about/',''):
                        page.evaluate("document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0,0)")
                        page.screenshot(path=str(OUT/f"{route.strip('/') or 'home'}-{width}.png"),full_page=True)
                assert not errors,errors
                context.close()
            request=browser.new_context().request
            for asset in ('media/cde-gap3-hero-1672.webp','media/cde-gap3-hero-824.webp','research/references.json'):
                response=request.get(BASE+asset)
                assert response.status==200,(asset,response.status)
                expected=hashlib.sha256((ROOT/'public'/asset).read_bytes()).hexdigest()
                actual=hashlib.sha256(response.body()).hexdigest()
                assert actual==expected,(asset,'content mismatch')
                report['files'].append({'path':asset,'sha256':actual})
            browser.close()
        report['result']='pass'
    except Exception as error:
        report['result']='fail';report['error']=repr(error);raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
        if proc:proc.terminate()
    print(json.dumps({'result':report['result'],'checks':len(report['checks']),'files':len(report['files'])}))

if __name__=='__main__':main()

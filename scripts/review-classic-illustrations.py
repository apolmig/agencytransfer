"""Verify the assigned classic artwork, source bytes and publication boundaries."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('REVIEW_BASE','http://127.0.0.1:8767/agencytransfer/')
OUT=Path(os.environ.get('REVIEW_OUTPUT',str(ROOT/'classic-artwork-review')))
WIDTHS=(1440,768,390,320)
TARGETS={
    'paper/':'anatomy',
    'research/part-i/':'anatomy',
    'research/part-iv/':'policy-atlas',
    'outputs/':'circuit',
}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    proc=None
    if BASE.startswith('http://127.0.0.1'):
        server=ROOT/'_artwork_preview';server.mkdir(exist_ok=True)
        link=server/'agencytransfer'
        if not link.exists():link.symlink_to(ROOT/'dist',target_is_directory=True)
        proc=subprocess.Popen(['python','-m','http.server','8767','--directory',str(server)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.6)
    report={'base':BASE,'checks':[],'files':[],'result':'pending'}
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'))
            for width in WIDTHS:
                ctx=browser.new_context(viewport={'width':width,'height':1000 if width>800 else 844},reduced_motion='reduce')
                page=ctx.new_page();errors=[]
                page.on('pageerror',lambda err:errors.append(str(err)))
                for slug,kind in TARGETS.items():
                    res=page.goto(BASE+slug,wait_until='networkidle',timeout=40000)
                    assert res and res.status==200,(slug,'HTTP')
                    page.locator('h1').first.wait_for()
                    assert page.locator('h1').count()==1
                    assert page.locator('.v2-header').count()==1
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(slug,width,'overflow')
                    figure=page.locator(f'figure.research-illustration--{kind}')
                    assert figure.count()==1,(slug,'figure count',kind)
                    image=figure.locator('img');image.scroll_into_view_if_needed()
                    image.evaluate('(img)=>img.decode()')
                    assert image.evaluate('(img)=>img.complete && img.naturalWidth>0')
                    assert 'illustrations/' in image.get_attribute('src')
                    assert image.get_attribute('srcset')
                    assert len(image.get_attribute('alt') or '')>50
                    assert figure.locator('a').first.get_attribute('target')=='_blank'
                    assert 'noopener' in figure.locator('a').first.get_attribute('rel')
                    figtext=figure.text_content() or ''
                    assert 'Working draft' in figtext and 'not' in figtext
                    details=figure.locator('details');details.locator('summary').click()
                    assert details.get_attribute('open') is not None
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    details.locator('summary').click()
                    if slug=='paper/':
                        assert page.locator('.paper-coming-soon').inner_text()=='Full working paper — coming soon'
                        assert page.locator('main svg').count()==0
                        assert 'Unpublished draft.' in page.locator('.paper-citation').inner_text()
                    if slug=='research/part-i/':assert '$10' in page.locator('h1').inner_text()
                    if slug=='research/part-iv/':
                        assert page.locator('.policy-example').count()==6
                        assert 'Where interventions act' in figtext
                        assert image.get_attribute('src').endswith('policy-intervention-atlas-1600.webp')
                    if slug=='outputs/':
                        assert figure.locator('a[href$="part-iv/#policy-examples"]').count()==1
                        assert image.get_attribute('src').endswith('policy-circuit-breakers-1448.webp')
                    text=page.locator('main').text_content() or ''
                    assert not re.search(r'\bv1\.\d+',text,re.I)
                    assert page.locator('main a[href*="harmful-manipulation-election-security"][href$=".pdf"]').count()==0
                    assert page.locator('.v2-header a[href$="/registry/"]').get_attribute('target')=='_blank'
                    name=slug.strip('/').replace('/','-')
                    figure.screenshot(path=str(OUT/f'{name}-figure-{width}.png'))
                    page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
                    if width in (1440,390):page.screenshot(path=str(OUT/f'{name}-page-{width}.png'),full_page=True)
                    report['checks'].append({'path':slug,'width':width,'artwork':kind,'status':200,'image':image.evaluate('(img)=>img.currentSrc')})
                page.goto(BASE+'research/part-iii/',wait_until='networkidle',timeout=40000)
                assert page.locator('.research-illustration').count()==0
                assert page.locator('main svg').count()==0
                page.goto(BASE+'explainers/',wait_until='networkidle',timeout=40000)
                assert page.locator('#mechanism-map').count()==0
                assert page.locator('main svg').count()==0
                assert page.locator('a[href$="research/part-i/"]').count()>=1
                page.goto(BASE,wait_until='networkidle',timeout=40000)
                assert page.locator('.v2-hero-art img').get_attribute('src').endswith('cde-gap3-hero-1672.webp')
                assert page.locator('.v2-part-card').count()==4
                assert page.locator('.research-illustration').count()==0,'Extra homepage image'
                assert all(c.locator('a').count()==1 for c in page.locator('.v2-part-card').all())
                assert not errors,errors
                report['checks'].append({'path':'','width':width,'hero':'unchanged','partIII':'no decorative figure','explainer':'animation dominant'})
                ctx.close()
            req=browser.new_context().request
            manifest=json.loads((ROOT/'programme/illustrations/classic-artwork.json').read_text())
            files=[v['path'].removeprefix('public/') for item in manifest for v in item['variants']]
            files += ['media/cde-gap3-hero-1672.webp','media/cde-gap3-hero-824.webp','research/references.json']
            for rel in files:
                res=req.get(BASE+rel);assert res.status==200,(rel,res.status)
                digest=hashlib.sha256(res.body()).hexdigest()
                assert digest==hashlib.sha256((ROOT/'public'/rel).read_bytes()).hexdigest(),(rel,'checksum')
                report['files'].append({'path':rel,'sha256':digest,'bytes':len(res.body())})
            browser.close()
        report['result']='pass'
    except Exception as err:
        report['result']='fail';report['error']=str(err);raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
        if proc:proc.terminate()
    print(json.dumps({'result':report['result'],'rendered_checks':len(report['checks']),'assets':len(report['files'])}))

if __name__=='__main__':main()

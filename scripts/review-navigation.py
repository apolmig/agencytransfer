"""Verify shared publication navigation without modifying the independent Registry.

Run after `npm run build`; set REVIEW_MODE=live to check deployed HTTPS pages.
Screenshots and the machine-readable report are written outside the public site.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'navigation-browser-review'
OUT.mkdir(exist_ok=True)
SCOPE = 'A research programme in progress on harmful manipulation and epistemic risk, with election security as its first focus.'
MENU = ['Programme', 'Research', 'Registry', 'References', 'Artifacts', 'About']
MODE = os.environ.get('REVIEW_MODE', 'preview')
server = None
if MODE == 'live':
    base = 'https://miguelguerrero.eu/agencytransfer/'
else:
    serve = ROOT / '_navigation_review'
    serve.mkdir(exist_ok=True)
    link = serve / 'agencytransfer'
    if not link.exists():
        link.symlink_to(ROOT / 'dist', target_is_directory=True)
    server = subprocess.Popen(['python', '-m', 'http.server', '8767', '--directory', str(serve)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = 'http://127.0.0.1:8767/agencytransfer/'
    time.sleep(1)

report = {'mode': MODE, 'base': base, 'pages': [], 'checks': [], 'files': [], 'result': 'pending'}
try:
    with sync_playwright() as p:
        chrome = shutil.which('google-chrome') or shutil.which('chromium')
        browser = p.chromium.launch(executable_path=chrome)
        for width in (1440, 768, 390, 320):
            context = browser.new_context(viewport={'width': width, 'height': 1000 if width > 768 else 844})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            for slug in ('', 'research/', 'research/part-i/', 'research/part-iii/', 'research/part-iv/', 'paper/', 'references/', 'outputs/', 'about/', 'explainers/', 'media/cde-rift-animation/', 'media/cde-rift-animation/index.html'):
                response = page.goto(base + slug, wait_until='networkidle', timeout=30000)
                assert response.status == 200, (slug, response.status)
                page.locator('main h1').first.wait_for()
                nav = page.locator('.v2-header nav[aria-label="Primary navigation"]')
                assert nav.count() == 1, (slug, 'missing or duplicate navigation')
                assert nav.locator('a').all_text_contents() == MENU
                assert all(a.is_visible() for a in nav.locator('a').all()), (slug, width, 'hidden menu item')
                assert nav.get_by_role('link', name='Registry', exact=True).get_attribute('target') == '_blank'
                assert nav.get_by_role('link', name='Research', exact=True).get_attribute('href') == '/agencytransfer/#research'
                assert page.locator('.v2-draftbar').count() == 1
                scroll_width = page.evaluate('document.documentElement.scrollWidth')
                assert scroll_width <= width + 1, (slug, width, scroll_width, 'horizontal overflow')
                assert page.locator('h1').count() == 1, (slug, 'multiple page titles')
                if slug == '':
                    assert page.locator('.v2-hero .v2-deck').inner_text() == SCOPE
                    cards = page.locator('.v2-part-card')
                    assert cards.count() == 4 and all(c.locator('a').count() == 1 for c in cards.all())
                    assert cards.nth(1).locator('a').get_attribute('target') == '_blank'
                    assert 'How far can an adversarial actor go with $10?' in cards.first.inner_text()
                    assert page.locator('.v2-actions a').count() == 2
                    assert page.locator('.v2-actions a').last.get_attribute('href') == '/agencytransfer/explainers/'
                    assert page.locator('.v2-hero-art img').evaluate('(e) => e.complete && e.naturalWidth > 0')
                    assert 'not yet published' not in page.locator('main').inner_text().lower()
                if slug in ('explainers/', 'media/cde-rift-animation/', 'media/cde-rift-animation/index.html'):
                    assert page.locator('h1').inner_text() == 'The CDE Gap, explained'
                    assert page.locator('link[rel="canonical"]').get_attribute('href') == 'https://miguelguerrero.eu/agencytransfer/explainers/'
                    iframe = page.locator('#cde-explainer iframe')
                    assert iframe.count() == 1 and iframe.get_attribute('src').endswith('/player.html')
                    frame = page.frame_locator('#cde-explainer iframe')
                    frame.locator('#play').wait_for()
                    assert frame.locator('#play').inner_text() == 'Play'
                    assert not frame.locator('.player-heading').is_visible()
                    assert not frame.locator('footer').is_visible()
                    assert page.locator('.publication-extra').get_attribute('open') is None
                    for chapter in range(6):
                        frame.locator(f'[data-chapter="{chapter}"]').click()
                        assert frame.locator(f'[data-chapter="{chapter}"]').get_attribute('aria-pressed') == 'true'
                    assert frame.locator('#time').inner_text() == '01:15 / 01:33'
                    frame.locator('#restart').click()
                    frame.locator('#play').click()
                    page.wait_for_timeout(200)
                    assert frame.locator('#play').inner_text() == 'Pause'
                    frame.locator('#play').click()
                    frame.locator('#transcript > summary').click()
                    assert frame.locator('#text-agency').is_visible()
                    page.wait_for_timeout(200)
                    frame_size = iframe.bounding_box()
                    player_height = frame.locator('#player').evaluate('(e) => e.getBoundingClientRect().height')
                    assert frame_size['height'] >= player_height - 2, (width, slug, 'clipped transcript')
                    frame.locator('#transcript > summary').click()
                    page.wait_for_timeout(150)
                if slug == 'outputs/':
                    assert page.locator('.artifact-directory li').count() == 8
                    assert all(row.locator('a').count() == 1 for row in page.locator('.artifact-directory li').all())
                    assert page.locator('#pending-artifacts').get_attribute('open') is None
                    assert page.locator('svg,img').count() == 0
                if slug == 'references/':
                    page.locator('.reference-results > ol > li').first.wait_for()
                    assert page.locator('.reference-results > ol > li').count() == 25
                # The same header remains available while reading, not only at the top.
                page.evaluate('window.scrollTo(0, 450)')
                page.wait_for_timeout(150)
                header_box = page.locator('.v2-header').bounding_box()
                assert abs(header_box['y']) <= 1, (slug, width, header_box['y'], 'header not sticky')
                page.evaluate("document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0, 0)")
                page.wait_for_timeout(100)
                report['pages'].append({'path': slug, 'viewport': width, 'status': response.status, 'scrollWidth': scroll_width, 'menu': MENU})
                if slug in ('', 'explainers/', 'media/cde-rift-animation/', 'outputs/') and width in (1440, 390, 320):
                    name = (slug or 'home').strip('/').replace('/', '-')
                    page.screenshot(path=str(OUT / f'{name}-{width}.png'), full_page=True)
            assert not errors, errors
            # Check the main user journey and all preserved scenario bookmarks.
            page.goto(base + 'outputs/', wait_until='networkidle')
            page.locator('.artifact-directory').get_by_role('link', name='The CDE Gap, explained', exact=False).click()
            assert page.url == base + 'explainers/'
            page.locator('.v2-header nav').get_by_role('link', name='Research', exact=True).click()
            page.locator('#research').wait_for()
            page.wait_for_timeout(250)
            assert page.url == base + '#research'
            page.goto(base + 'explainers/#manuel-miami', wait_until='networkidle')
            assert page.locator('.publication-extra').get_attribute('open') is not None
            assert page.locator('#manuel-miami').is_visible()
            context.close()
        # Unscripted fallback keeps navigation and the complete explanation.
        context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        page = context.new_page()
        for slug in ('explainers/', 'media/cde-rift-animation/'):
            page.goto(base + slug, wait_until='networkidle')
            assert page.locator('.reading-fallback nav a').all_text_contents() == MENU
            assert page.frame_locator('iframe').locator('#text-agency').is_visible()
        context.close()
        browser.close()
    for path in (
        'research/references.json',
        'research/harmful-manipulation-election-security-v1.5-20260901.pdf',
        'research/p4-source-linked-review-20260901.xlsx',
        'media/cde-gap3-hero-1672.webp',
    ):
        with urlopen(base + path, timeout=40) as response:
            raw = response.read()
        expected = (ROOT / 'public' / path).read_bytes()
        assert raw == expected, path
        report['files'].append({'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    report['checks'] = ['Same six-item sticky header on every publication page, including old CDE URLs', 'One page title and one draft notice', 'New programme scope and unchanged $10 hook', 'Independent new-tab Registry', 'Manual player controls and unclipped transcript', 'Direct artifact and scenario links', 'No-JavaScript navigation and full explanation', 'Source library, current paper, workbook and hero preserved']
    report['result'] = 'pass'
except Exception as error:
    report['result'] = 'fail'
    report['error'] = str(error)
    raise
finally:
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    if server:
        server.terminate()
print(json.dumps(report, indent=2))

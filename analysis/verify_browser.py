"""Optional real Firefox check, using an existing geckodriver and no Python browser package.

Only the test driver uses a loopback control socket. Reports are opened directly
from disk, with an unreachable browser proxy to prevent external asset loading.
"""
from __future__ import annotations
import argparse
import base64
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError


def check(root: Path, profile_root: Path, screenshots: Path) -> dict:
    root = root.resolve()
    screenshots.mkdir(parents=True, exist_ok=True)
    driver = shutil.which('geckodriver')
    if not driver:
        raise RuntimeError('Existing geckodriver is unavailable; no browser dependency was installed.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    opener = build_opener(ProxyHandler({}))
    base = f'http://127.0.0.1:{port}'
    def call(method, route, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(base + route, data=body, method=method, headers={'Content-Type': 'application/json'})
        try:
            with opener.open(req, timeout=55) as response:
                value = json.load(response).get('value')
        except HTTPError as exc:
            value = json.loads(exc.read()).get('value')
        if isinstance(value, dict) and value.get('error'):
            raise RuntimeError(value['error'] + ': ' + value.get('message', ''))
        return value
    profile_root.mkdir(parents=True, exist_ok=True)
    session = None
    with tempfile.TemporaryFile() as logs:
        process = subprocess.Popen([driver, '--host', '127.0.0.1', '--port', str(port),
                                    '--profile-root', str(profile_root), '--log', 'error'], stdout=logs, stderr=logs)
        try:
            for _ in range(60):
                try:
                    call('GET', '/status')
                    break
                except OSError:
                    if process.poll() is not None:
                        raise RuntimeError('Existing browser driver failed to start.')
                    time.sleep(.25)
            capabilities = call('POST', '/session', {'capabilities': {'alwaysMatch': {
                'browserName': 'firefox', 'moz:firefoxOptions': {'args': ['-headless'], 'prefs': {
                    'network.proxy.type': 1, 'network.proxy.http': '127.0.0.1', 'network.proxy.http_port': 9,
                    'network.proxy.ssl': '127.0.0.1', 'network.proxy.ssl_port': 9, 'network.proxy.no_proxies_on': '',
                    'network.captive-portal-service.enabled': False, 'network.connectivity-service.enabled': False,
                    'browser.startup.homepage': 'about:blank', 'datareporting.policy.dataSubmissionEnabled': False,
                    'toolkit.telemetry.enabled': False}}}}})
            session = capabilities['sessionId']
            prefix = '/session/' + session
            call('POST', prefix + '/window/rect', {'width': 1440, 'height': 1050})
            def js(script):
                return call('POST', prefix + '/execute/sync', {'script': script, 'args': []})
            def click(selector):
                element = call('POST', prefix + '/element', {'using': 'css selector', 'value': selector})
                element_id = element['element-6066-11e4-a52e-4f735466cecf']
                call('POST', prefix + '/element/' + element_id + '/click', {})
            def open_page(name):
                call('POST', prefix + '/url', {'url': (root / name).as_uri()})
                for _ in range(100):
                    if js('return document.readyState') == 'complete':
                        return
                    time.sleep(.1)
                raise AssertionError('Page did not finish loading: ' + name)
            def screenshot(name):
                data = call('GET', prefix + '/screenshot')
                (screenshots / name).write_bytes(base64.b64decode(data))
            open_page('CORPUS_REPORT.html')
            assert 'catalog60_8192_v2' in js('return document.querySelector("h1").textContent')
            assert js('return document.querySelectorAll(".stats div").length') == 5
            screenshot('main_report.png')
            # Follow an actual report link, then exercise the local catalog script.
            click('a[href="catalog/works.html"]')
            for _ in range(50):
                if js('return !!document.querySelector("[data-filter]")'):
                    break
                time.sleep(.1)
            assert js('return document.querySelector("table").tBodies[0].rows.length') == 153
            visible = js('const q=document.querySelector("[data-filter]");q.value="Thoreau";q.dispatchEvent(new Event("input"));return [...document.querySelector("table").tBodies[0].rows].filter(r=>!r.hidden).length;')
            assert visible == 2, 'Catalog search should show both Thoreau works'
            screenshot('catalog_filtered.png')
            open_page('catalog/plots.html')
            click('a[href="../visualizations/chapter_pca.html"]')
            for _ in range(100):
                if js('return !!(document.querySelector(".js-plotly-plot")||{})._fullLayout'):
                    break
                time.sleep(.1)
            assert js('return !!(document.querySelector(".js-plotly-plot")||{})._fullLayout'), 'Actual plot link failed'
            results = []
            for path in sorted((root / 'visualizations').glob('*.html')):
                relative = path.relative_to(root).as_posix()
                open_page(relative)
                info = None
                for _ in range(150):
                    info = js('const g=document.querySelector(".js-plotly-plot");if(!g||!g._fullLayout)return null;return {version:Plotly.version,traces:g.data.length,points:g.data.reduce((n,t)=>n+(t.ids?t.ids.length:0),0),svgs:g.querySelectorAll("svg.main-svg").length,resources:performance.getEntriesByType("resource").map(x=>({name:x.name,initiator:x.initiatorType})),title:g._fullLayout.title.text};')
                    if info and info['svgs']:
                        break
                    time.sleep(.1)
                assert info and info['svgs'] > 0, 'Chart did not render: ' + relative
                network_assets = [item for item in info['resources'] if item['name'].startswith(('http:', 'https:'))]
                assert not network_assets, 'Network resource requested'
                escaped_assets = [item for item in info['resources'] if item['name'].startswith('file:') and not Path(item['name'][7:]).resolve().is_relative_to(root)]
                assert not escaped_assets, 'Local resource escaped publication'
                if path.name.endswith('_cosine.html'):
                    expected = 120 if path.name.startswith('chapter_') else 153 if path.name.startswith('work_') else 35
                    assert js('return document.querySelector(".js-plotly-plot").data[0].x.length') == expected
                else:
                    expected = 1731 if path.name.startswith('chapter_') else 153 if path.name.startswith('work_') else 35
                    assert info['points'] == expected, 'Scatter point count mismatch'
                    zoom = js('const g=document.querySelector(".js-plotly-plot");Plotly.relayout(g,{"xaxis.range":[-0.1,0.1]});return g._fullLayout.xaxis.range;')
                    assert zoom == [-.1, .1], 'Interactive zoom failed'
                    js('const g=document.querySelector(".js-plotly-plot");Plotly.relayout(g,{"xaxis.autorange":true});Plotly.Fx.hover(g,[{curveNumber:0,pointNumber:0}]);return true;')
                    assert js('return document.querySelectorAll(".hoverlayer .hovertext").length') > 0, 'Interactive hover failed'
                    js('Plotly.Fx.unhover(document.querySelector(".js-plotly-plot"));return true;')
                if path.name in ('chapter_pca.html', 'chapter_umap.html', 'work_cosine.html'):
                    screenshot(path.stem + '.png')
                results.append({'file': '../' + relative, 'rendered': True, 'plotly_version': info['version'],
                                'displayed_rows': expected, 'traces': info['traces'], 'network_asset_requests': 0,
                                'zoom_and_hover_verified': not path.name.endswith('_cosine.html')})
            return {'status': 'passed', 'browser': 'Firefox', 'browser_version': capabilities['capabilities']['browserVersion'],
                    'mode': 'relocated folder opened directly from disk', 'external_asset_loading': 'blocked by unreachable proxy',
                    'report_navigation': True, 'catalog_filter_visible_results': visible, 'plot_catalog_navigation': True,
                    'charts': results, 'chart_count': len(results), 'inference_requests': 0,
                    'screenshots': sorted('browser/' + p.name for p in screenshots.glob('*.png'))}
        finally:
            if session:
                try:
                    call('DELETE', '/session/' + session)
                except OSError:
                    pass
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--profile-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--screenshots', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.root, args.profile_root, args.screenshots)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

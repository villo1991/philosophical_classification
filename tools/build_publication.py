"""Build a publication derivative from a separately supplied research checkout.

Never calls model clients, changes research inputs, or recomputes projections.
The finished publication does not need the research checkout to be viewed.
"""
from __future__ import annotations
import argparse, ast, csv, gzip, hashlib, html, importlib.metadata, json, os, re, shutil
from collections import Counter
from pathlib import Path
import numpy as np
from bs4 import BeautifulSoup

PUBLIC_NAME = 'catalog60_8192_v2'
ORIGINAL_ID = 'chapter_first_catalog60_8192_v2'
PUB = Path(__file__).resolve().parents[1]
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
LIMIT = ('Source-checked structure is not independent human approval. Embedding proximity can reflect topic, '
         'style, translation and unit length; it does not establish philosophical agreement. 2D distances are approximate.')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8')


def save(path,value):write(path,json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n')


def rel(target,source):return Path(os.path.relpath(target,Path(source).parent)).as_posix()


def esc(value):return html.escape(str(value))


def link(target,label,source,fragment=''):
    return f'<a href="{esc(rel(target,source)+fragment)}">{esc(label)}</a>'


def scrub(value):
    if isinstance(value,dict):return {k:scrub(v) for k,v in value.items()}
    if isinstance(value,list):return [scrub(v) for v in value]
    if not isinstance(value,str):return value
    value=re.sub(r'/home/[^\s\"\'<>;,]+','[research-local path omitted]',value)
    value=re.sub(r'https?://(?:127\.0\.0\.1|localhost)(?::\d+)?[^\s\"<>]*','[historical local endpoint omitted]',value)
    return EMAIL.sub('[contact omitted]',value)


def page(path,title,body):
    nav=''.join(link(PUB/p,label,path) for p,label in [('CORPUS_REPORT.html','Report'),('catalog/works.html','Works · 153'),
        ('catalog/sources.html','Sources · 60'),('catalog/attributions.html','Attributions · 35'),('catalog/plots.html','Plots'),
        ('verification/index.html','Verification'),('README.md','README')])
    write(path,'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
          f'<title>{esc(title)} · Philosophical classification</title><link rel="stylesheet" href="{rel(PUB/"assets/site.css",path)}">'
          f'<script defer src="{rel(PUB/"assets/catalog.js",path)}"></script></head><body><header><a class="brand" href="{rel(PUB/"CORPUS_REPORT.html",path)}">Philosophical classification</a><span>{PUBLIC_NAME}</span></header><nav>{nav}</nav>'
          f'<main><h1>{esc(title)}</h1>{body}</main><footer>{esc(LIMIT)}<p>{link(PUB/"LICENSE_NOTES.md","Rights and credits",path)} · '
          f'{link(PUB/"provenance/TRANSFORMATIONS.md","Publication transformations",path)}</p></footer></body></html>')


def table(headers,rows,search=False):
    box='<label class="search">Filter this catalog <input type="search" data-filter placeholder="Author, title, source, translator…"></label><p data-count></p>' if search else ''
    return box+'<div class="table-scroll"><table'+(' data-searchable' if search else '')+'><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def readable_types(types):
    labels={'whole_work':'whole-work unit','part':'part','book':'book','chapter':'chapter',
            'section':'section','essay':'essay','aphorism':'aphorism','letter':'letter',
            'poem':'poem','prologue':'prologue','lecture':'lecture'}
    return '; '.join(f'{count} {labels.get(kind,kind)}'+('s' if count!=1 else '') for kind,count in types.items())


def figure_payload(text):
    pos=text.rfind('Plotly.newPlot(')
    if pos<0:raise ValueError('Missing Plotly initialization')
    decoder=json.JSONDecoder();tail=text[pos+len('Plotly.newPlot('):].lstrip()
    _,end=decoder.raw_decode(tail);tail=tail[end:].lstrip();data,end=decoder.raw_decode(tail[1:].lstrip())
    tail=tail[1:].lstrip()[end:].lstrip();layout,_=decoder.raw_decode(tail[1:].lstrip())
    return data,layout


def build(root):
    for name in ['assets','notices','provenance','verification','catalog','visualizations']:
        (PUB/name).mkdir(parents=True,exist_ok=True)
    data=root/'data_HTML';run=data/'chapter_first/runs'/ORIGINAL_ID
    report=read(run/'CORPUS_REPORT.json');config=read(run/'config.json');coverage=read(run/'coverage_plan.json')
    progress=read(run/'progress.json');aggregate_path=data/read(run/'aggregate_current.json')['path'];aggregate=read(aggregate_path)
    plots=read(run/'visualizations/plots_current.json')['plots'];contributors=read(run/'contributors.json')
    assert report['represented_documents']==60 and len(aggregate['chapters'])==1731 and len(aggregate['works'])==153
    assert len(aggregate['philosophers'])==35 and len(progress['records'])==1996 and len(plots)==12
    assert progress['status']=='complete' and not aggregate['invalid']
    result_dir=PUB/'results'/PUBLIC_NAME;result_dir.mkdir(parents=True,exist_ok=True)
    original_files=set();transformations=[];preserve={}
    def track(path,role):
        path=Path(path);preserve[path.relative_to(root).as_posix()]=sha(path)
        return {'artifact_id':role,'sha256':sha(path),'bytes':path.stat().st_size}
    def derivative(source,target,role,changes):
        info=track(source,role);info.update(publication_file=rel(target,PUB/'provenance/original_artifacts.json'),transformations=changes)
        transformations.append(info)
    for f in ['SESSION_STATE.md','html_research/README.md','data_HTML/chapter_first/REPORT.md']:
        track(root/f,'documentation-inspected:'+Path(f).name)
    for f in [run/'CORPUS_REPORT.html',run/'CORPUS_REPORT.md',run/'CORPUS_REPORT.json',run/'config.json',run/'completion.json',run/'coverage_plan.json',run/'progress.json',run/'contributors.json',aggregate_path]:track(f,f.name)

    # Verify the actual original dependency graph, including every extraction review.
    graph=[]
    for start in [run/'CORPUS_REPORT.html',run/'CORPUS_REPORT.md']:
        if start.suffix=='.html':refs=[t['href'] for t in BeautifulSoup(start.read_text(),'html.parser').find_all(href=True)]
        else:refs=[url for _,url in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',start.read_text())]
        for url in refs:
            if url.startswith(('https:','http:','#')):continue
            target=(start.parent/url.split('#')[0]).resolve()
            assert target.is_file(),f'Outstanding original report link: {url}'
            graph.append({'report':start.name,'reference':url,'resolved_sha256':sha(target)})
    save(PUB/'provenance/original_dependency_graph.json',{'historical_references_are_identifiers_not_publication_links':True,'edges':graph})

    # Scientific matrices are copied/stacked with exact saved values, never inferred.
    matrix=np.load(data/aggregate['chapter_vectors_path'],allow_pickle=False)
    assert matrix.shape==(1731,1024) and np.isfinite(matrix).all()
    shutil.copyfile(data/aggregate['chapter_vectors_path'],result_dir/'chapter_vectors.npy')
    track(data/aggregate['chapter_vectors_path'],'original-chapter-matrix')
    windows=[];window_arrays=[];unit_to_windows={};sources=[];mappings={};unit_lookup={}
    for sid,pid in config['identity']['plans'].items():
        plan_path=data/'chapter_first/plans'/pid/'manifest.json';plan=read(plan_path);track(plan_path,'frozen-window-plan:'+sid)
        ex_dir=data/'chapter_first/extractions'/sid/plan['identity']['extraction_id'];ex=read(ex_dir/'manifest.json')
        track(ex_dir/'manifest.json','frozen-extraction:'+sid);track(ex_dir/'review.html','extraction-review:'+sid)
        meta_path=data/'downloads'/sid/'metadata.json';meta=read(meta_path);track(meta_path,'source-metadata:'+sid)
        raw=data/meta['original_path'];assert sha(raw)==meta['raw_sha256'];track(raw,'original-html:'+sid)
        structure_dir=data/read(data/'editions'/sid/'current.json')['path'];canonical_path=structure_dir/'canonical.txt';canonical=canonical_path.read_text();track(canonical_path,'original-canonical:'+sid)
        # Credit emails are not scientific evidence. Length-preserving redaction
        # retains all canonical Unicode offsets and public producer names.
        hits=list(EMAIL.finditer(canonical));clean_canonical=EMAIL.sub(lambda m:'_'*len(m.group()),canonical)
        canonical_target=PUB/'sources'/sid/'canonical.txt';write(canonical_target,clean_canonical)
        derivative(canonical_path,canonical_target,'canonical:'+sid,{'credit_emails_redacted':len(hits),'character_offsets_preserved':True})
        st=read(structure_dir/'structure.json');track(structure_dir/'structure.json','original-block-map:'+sid)
        notice='\n\n'.join(b['text'] for b in st['blocks'] if b['role']=='publisher_boilerplate')
        notice=EMAIL.sub('[contact omitted]',notice)
        write(PUB/'notices/sources'/f'{sid}.txt',notice+'\n')
        text_notice=PUB/'texts'/sid/'NOTICE.txt';write(text_notice,'Research extraction of a historical source. Publisher credits and applicable source notice follow.\n\n'+notice+'\n')
        ledger_path=data/'chapter_first/catalog60_audit/ledgers'/f'{sid}.json';ledger=read(ledger_path);track(ledger_path,'source-block-ledger:'+sid)
        save(PUB/'sources'/sid/'ledger.json',scrub(ledger))
        # Minimal source profiles avoid repeated work profiles in every unit.
        frozen_profile=ex['identity']['profile']
        profile={'source_id':sid,'raw_sha256':meta['raw_sha256'],'extraction_id':ex['id'],
          'profile_sha256':ex['identity']['profile_sha256'],'parser_version':ex['identity']['parser_version'],
          'extraction_version':ex['identity']['extraction_version'],'profile':scrub(frozen_profile)}
        def omit_old_locations(obj):
            if isinstance(obj,dict):return {k:omit_old_locations(v) for k,v in obj.items() if k not in {'audit_path','source_html'}}
            if isinstance(obj,list):return [omit_old_locations(x) for x in obj]
            return obj
        save(PUB/'sources'/sid/'profile.json',omit_old_locations(profile))
        source_info={'id':sid,'title':meta['catalog']['work'],'authors':meta['catalog']['authors'],'translator':meta['catalog'].get('translator'),
          'language':meta.get('language_html') or meta['catalog'].get('language'),'ebook_id':meta['ebook_id'],
          'catalog_url':meta['source_url'],'retrieved_utc':meta['retrieved_utc'],'raw_html_sha256':meta['raw_sha256'],
          'catalog_metadata_sha256':sha(meta_path),'publication':meta['catalog'].get('publication'),
          'translation':meta['catalog'].get('translation'),'metadata_note':meta['catalog'].get('metadata_note'),
          'rights':{k:v for k,v in meta['rights'].items() if k!='source_excerpt'},'substitution':meta.get('substitution'),
          'canonical_file':rel(canonical_target,PUB/'catalog/sources.json'),'ledger_file':rel(PUB/'sources'/sid/'ledger.json',PUB/'catalog/sources.json'),
          'profile_file':rel(PUB/'sources'/sid/'profile.json',PUB/'catalog/sources.json'),'notice_file':rel(PUB/'notices/sources'/f'{sid}.txt',PUB/'catalog/sources.json'),
          'extraction_id':ex['id'],'plan_id':pid,'canonical_original_sha256':sha(canonical_path),'canonical_publication_sha256':sha(canonical_target)}
        sources.append(scrub(source_info));mappings[sid]=[]
        for u in plan['units']:
            unit_lookup[u['id']]=u;unit_to_windows[u['id']]=u['windows']
            original_text=data/u['text_path'];target=PUB/'texts'/sid/(u['id']+'.txt')
            original_bytes=original_text.read_bytes();assert hashlib.sha256(original_bytes).hexdigest()==u['cleaned_sha256']
            assert not EMAIL.search(original_bytes.decode()),'Primary source text contains a contact requiring explicit handling'
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original_text,target);track(original_text,'primary-text:'+u['id'])
            mappings[sid].append({k:u[k] for k in ['id','source_start','source_end','mapping','removed','substantive_block_ids']})
        maps_target=PUB/'sources'/sid/'unit_mappings.json.gz'
        with maps_target.open('wb') as f:
            with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as zipped:zipped.write(json.dumps(scrub(mappings[sid]),ensure_ascii=False,separators=(',',':')).encode())

    record_by_id={r['window_id']:r for r in progress['records']}
    for unit_id,planned in unit_to_windows.items():
        indices=[]
        for w in planned:
            record=record_by_id[w['id']];path=data/record['path'];assert sha(path)==record['sha256'];track(path,'native-window:'+w['id'])
            vector=np.load(path,allow_pickle=False);assert vector.shape==(1024,) and np.isfinite(vector).all()
            index=len(windows);indices.append(index);window_arrays.append(vector)
            windows.append({'row_index':index,'id':w['id'],'unit_id':unit_id,'source_id':record['source_id'],
               **{k:w[k] for k in ['core_start','core_end','context_start','context_end','core_token_start','core_token_end','owned_tokens','total_input_tokens','input_sha256']},
               'native_cache_key':record['cache_key'],'original_native_file_sha256':record['sha256']})
        unit_lookup[unit_id]['publication_window_rows']=indices
    np.save(result_dir/'window_vectors.npy',np.stack(window_arrays),allow_pickle=False)
    chapters=[]
    for i,c in enumerate(aggregate['chapters']):
        original=data/c['vector_path'];track(original,'original-unit-vector:'+c['id']);assert np.array_equal(np.load(original,allow_pickle=False),matrix[i])
        u=unit_lookup[c['id']]
        row={k:c[k] for k in ['id','source_id','work_id','edition_id','title','unit_type','parent_title','status','human_approved','total_chapter_tokens','unique_chapter_tokens','owned_tokens','windows','window_ids','plan_id','cleaned_sha256','source_start','source_end','descriptor','dispersion','raw_centroid_norm']}
        row.update(row_index=i,authors=c['work']['authors'],attribution_status=c['work']['attribution_status'],
                   work_title=c['work']['title'],window_rows=u['publication_window_rows'],
                   text_file=rel(PUB/'texts'/c['source_id']/(c['id']+'.txt'),result_dir/'chapters.json'),
                   source_canonical_file=rel(PUB/'sources'/c['source_id']/'canonical.txt',result_dir/'chapters.json'),
                   original_vector_file_sha256=sha(original))
        chapters.append(row)
    save(result_dir/'chapters.json',{'matrix_file':'chapter_vectors.npy','rows':chapters})
    save(result_dir/'windows.json',{'matrix_file':'window_vectors.npy','rows':windows})
    works=[];work_vectors=[]
    source_by_id={s['id']:s for s in sources};override=contributors.get('work_overrides',{})
    for i,w in enumerate(aggregate['works']):
        path=data/w['vector_path'];track(path,'original-work-vector:'+w['id']);work_vectors.append(np.load(path,allow_pickle=False))
        sid=chapters[w['chapters'][0]]['source_id'];s=source_by_id[sid]
        row={k:v for k,v in w.items() if k!='vector_path'}
        row.update(row_index=i,source_id=sid,unit_types=dict(Counter(chapters[j]['unit_type'] for j in w['chapters'])),
                   window_count=sum(chapters[j]['windows'] for j in w['chapters']),
                   translator=override.get(w['id'],{}).get('translator',s['translator']),language=s['language'],
                   edition=s['publication'],catalog_url=s['catalog_url'],original_vector_file_sha256=sha(path),
                   catalog_anchor='work-'+hashlib.sha256(w['id'].encode()).hexdigest()[:16])
        works.append(row)
    np.save(result_dir/'work_vectors.npy',np.stack(work_vectors),allow_pickle=False)
    save(result_dir/'works.json',{'matrix_file':'work_vectors.npy','rows':works})
    phi=[]
    for balance in ['work-balanced','chapter-balanced']:
        arrays=[]
        for p in aggregate['philosophers']:
            path=data/(p['file_prefix']+'-'+balance+'.npy');arrays.append(np.load(path,allow_pickle=False));track(path,'philosopher-vector:'+p['name']+':'+balance)
        np.save(result_dir/('philosopher_'+balance+'.npy'),np.stack(arrays),allow_pickle=False)
    for i,p in enumerate(aggregate['philosophers']):
        row={k:v for k,v in p.items() if k!='file_prefix'};row.update(row_index=i,
             group_kind='traditional' if p['attribution_status']=='traditional' else 'joint' if len(p['authors'])>1 else 'individual',
             catalog_anchor='group-'+hashlib.sha256(p['name'].encode()).hexdigest()[:16]);phi.append(row)
    save(result_dir/'philosophers.json',{'matrices':{'work-balanced':'philosopher_work-balanced.npy','chapter-balanced':'philosopher_chapter-balanced.npy'},'rows':phi})
    save(PUB/'catalog/sources.json',{'sources':sources})
    save(PUB/'catalog/works.json',{'results_file':rel(result_dir/'works.json',PUB/'catalog/works.json'),'works':works})
    with (PUB/'catalog/works.csv').open('w',newline='',encoding='utf-8') as f:
        columns=['row_index','title','authors','attribution_status','source_id','translator','language','chapter_count','unit_types','window_count','catalog_url']
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for w in works:writer.writerow({k:json.dumps(w[k],ensure_ascii=False) if isinstance(w[k],(dict,list)) else w[k] for k in columns})

    # Keep scientifically important identities byte-for-byte where no redaction is needed.
    shutil.copyfile(run/'config.json',PUB/'provenance/run_identity.json')
    identity_text=(PUB/'provenance/run_identity.json').read_text();assert not re.search(r'/home/|file:/{2}',identity_text)
    save(PUB/'provenance/lineage.json',{'publication_name':PUBLIC_NAME,'original_run_identifier':ORIGINAL_ID,
         'original_aggregate_identifier':aggregate_path.parent.name,'original_aggregate_sha256':sha(aggregate_path),
         'identity_file':'run_identity.json','note':'Presentation alias only. Work/unit/window IDs, model/tokenizer/configuration hashes and vector values are preserved.'})
    save(PUB/'provenance/model_manifest.json',scrub(read(run/'model_manifest.json')))
    save(PUB/'provenance/dependencies.json',scrub(read(run/'dependency_changes.json')))
    summary={k:report[k] for k in ['requested_documents','represented_documents','vectors','dimensions','works','attribution_groups','individual_centroids','traditional_centroids','joint_centroids','native_unit_types','norms','gpu_summary']}
    summary.update(publication_name=PUBLIC_NAME,windows=len(windows),single_window_units=coverage['single_window_units'],multi_window_units=coverage['multi_window_units'],
         owned_tokens=sum(w['owned_tokens'] for w in windows),first_execution=scrub(report['first_execution']),
         eligible_sources=len(coverage['eligible_sources']),partially_eligible_sources=len(coverage['partially_eligible_sources']),blocked_sources=len(coverage['blocked_sources']))
    save(result_dir/'summary.json',summary)
    checks={}
    for name in ['final_completion.json','unit_coverage_validation.json','aggregation_and_preservation.json','completed_restart.json','final_visualization_checks.json','source_and_old_run_preservation.json','edition_duplicate_check.json']:
        checks[name]=scrub(read(run/'verification'/name));track(run/'verification'/name,'historical-verification:'+name)
    save(PUB/'verification/research_checks.json',checks)
    log=run/'verification/tests_final.txt';track(log,'historical-test-log')
    write(PUB/'verification/research_tests.txt',scrub(log.read_text()))

    # One exact shared Plotly bundle replaces sixteen redundant inline copies.
    distribution=importlib.metadata.distribution('plotly')
    vendor=Path(distribution.locate_file('plotly/package_data/plotly.min.js'));track(vendor if vendor.is_relative_to(root) else run/'dependency_changes.json','plotly-version-source')
    shutil.copyfile(vendor,PUB/'assets/plotly.min.js')
    shutil.copyfile(distribution.locate_file('plotly-6.9.0.dist-info/licenses/LICENSE.txt'),PUB/'notices/Plotly-LICENSE.txt')
    outputs=[];heatmaps={};payload_proofs=[]
    for p in plots:
        key=p['level']+('_'+p['balance'].replace('-','_') if p['balance'] else '')+'_'+p['method']
        target=PUB/'visualizations'/(key+'.html');original=Path(p['scatter']);before=original.read_text();soup=BeautifulSoup(before,'html.parser')
        bundle=next(s for s in soup.find_all('script') if 'plotly.js v' in (s.string or s.get_text()))
        assert (bundle.string or bundle.get_text())==vendor.read_text(),'Inline Plotly differs from installed bundle'
        bundle.clear();bundle['src']=rel(PUB/'assets/plotly.min.js',target)
        # Only presentation text outside scripts changes. Numerical figure payloads stay identical.
        for node in list(soup.find_all(string=True)):
            if node.parent.name not in {'script','style'} and ORIGINAL_ID in str(node):node.replace_with(str(node).replace(ORIGINAL_ID,PUBLIC_NAME))
        nav=soup.new_tag('nav');a_tag=soup.new_tag('a',href=rel(PUB/'CORPUS_REPORT.html',target));a_tag.string='← Corpus report';nav.append(a_tag)
        a_tag=soup.new_tag('a',href=rel(PUB/'catalog/works.html',target));a_tag.string=' · Browse works';nav.append(a_tag);soup.body.insert(0,nav)
        write(target,str(soup));assert figure_payload(before)==figure_payload(target.read_text())
        derivative(original,target,'scatter:'+key,{'bundle_deduplicated':True,'display_name_alias':True,'figure_data_and_layout_unchanged':True})
        # Compact coordinate sidecars retain exact IDs and coordinates, referring to shared metadata.
        coordinates=read(Path(p['coordinates']));coordinate_target=target.with_suffix('.coordinates.json')
        save(coordinate_target,{'rows':[{k:r[k] for k in ['id','row_index','x','y']} for r in coordinates['rows']],
             'level':p['level'],'balance':p['balance'],'diagnostics':p['diagnostics']})
        derivative(Path(p['coordinates']),coordinate_target,'coordinates:'+key,{'duplicate_metadata_factored_out':True,'coordinates_and_ids_unchanged':True})
        old_manifest=read(Path(p['manifest']));params=target.with_suffix('.json')
        result={'publication_name':PUBLIC_NAME,'level':p['level'],'balance':p['balance'],'method':p['method'],
                'vectors':p['vectors'],'works':p['works'],'html_file':target.name,'coordinates_file':coordinate_target.name,
                'reducer':old_manifest['identity']['reducer'],'diagnostics':p['diagnostics'],
                'original_plot_identity_sha256':hashlib.sha256(json.dumps(old_manifest['identity'],sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest(),
                'original_scatter_sha256':sha(original)}
        heatkey=p['level']+('_'+p['balance'].replace('-','_') if p['balance'] else '')
        heat_target=PUB/'visualizations'/(heatkey+'_cosine.html')
        if heatkey not in heatmaps:
            oldheat=Path(p['heatmap']);before_heat=oldheat.read_text();hs=BeautifulSoup(before_heat,'html.parser')
            inline=next(s for s in hs.find_all('script') if 'plotly.js v' in (s.string or s.get_text()));assert inline.string==vendor.read_text()
            inline.clear();inline['src']=rel(PUB/'assets/plotly.min.js',heat_target)
            nav2=hs.new_tag('p');back=hs.new_tag('a',href=rel(PUB/'CORPUS_REPORT.html',heat_target));back.string='← Corpus report';nav2.append(back);hs.body.insert(0,nav2)
            write(heat_target,str(hs));assert figure_payload(before_heat)==figure_payload(heat_target.read_text())
            heatmeta=read(oldheat.with_suffix('.json'));rows=heatmeta['rows']
            save(heat_target.with_suffix('.json'),{'level':p['level'],'balance':p['balance'],'rows':[{k:r[k] for k in ['row_index','id','title','unit_type']} for r in rows],
                 'selection':heatmeta['identity']['selection'],'original_html_sha256':sha(oldheat),'shape':heatmeta['shape']})
            nn=read(Path(p['nearest_neighbors']));save(PUB/'visualizations'/(heatkey+'_neighbors.json'),{k:nn[k] for k in ['neighbors','metric','k','score_block_rows','maximum_temporary_score_matrix_shape']})
            derivative(oldheat,heat_target,'cosine:'+heatkey,{'bundle_deduplicated':True,'figure_data_and_layout_unchanged':True})
            derivative(Path(p['nearest_neighbors']),PUB/'visualizations'/(heatkey+'_neighbors.json'),'neighbors:'+heatkey,{'duplicate_identity_metadata_omitted':True,'neighbor_ids_and_values_unchanged':True})
            heatmaps[heatkey]=heat_target
        result.update(cosine_file=heat_target.name,neighbors_file=heatkey+'_neighbors.json');save(params,result)
        outputs.append({**result,'html_file':rel(target,PUB/'catalog/plots.json'),'parameters_file':rel(params,PUB/'catalog/plots.json'),
                       'coordinates_file':rel(coordinate_target,PUB/'catalog/plots.json'),'cosine_file':rel(heat_target,PUB/'catalog/plots.json'),
                       'neighbors_file':rel(PUB/'visualizations'/(heatkey+'_neighbors.json'),PUB/'catalog/plots.json')})
        payload_proofs.append({'plot':key,'payload_unchanged':True})
    save(PUB/'catalog/plots.json',{'plots':outputs})
    save(PUB/'verification/chart_payloads.json',{'scatter_views':12,'cosine_views':4,'source_payload_equality':payload_proofs,'shared_plotly_sha256':sha(PUB/'assets/plotly.min.js')})
    render_pages(summary,sources,works,chapters,phi,outputs,result_dir,report)
    write_docs(summary,result_dir)

    # Original aggregation functions are reused as source, not recreated by a model.
    snippets=[]
    for filename,names in [('geometry.py',{'unit','describe'}),('chapter_pipeline.py',{'validate_vector','chapter_descriptor'})]:
        path=root/'html_research'/filename;source=path.read_text();tree=ast.parse(source)
        snippets.extend(ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
        track(path,'original-analysis-code:'+filename)
    write(PUB/'analysis/aggregations.py','"""Original aggregation functions; only local error/require helpers adapted."""\nimport numpy as np\n\ndef require(condition, category, message):\n    if not condition: raise ValueError(f"[{category}] {message}")\n\n'+'\n\n'.join(snippets)+'\n')
    save(PUB/'provenance/original_artifacts.json',{'derivatives':transformations})
    # Store original-file checksums outside public metadata, without a personal root.
    save(PUB/'verification/original_preservation.json',{'root_not_published':True,'files':preserve,'checked_files':len(preserve)})
    for name in ['publication_checks','vector_checks','relocation_checks','browser_checks']:
        target=PUB/'verification'/(name+'.json')
        if not target.exists():save(target,{'status':'pending'})
    # Build source paths in this last report are archival identifiers, never active links.
    assert all(sha(root/k)==v for k,v in preserve.items()),'Original research files changed during export'
    print(json.dumps({'publication':PUB.name,'sources':len(sources),'works':len(works),'units':len(chapters),
                      'windows':len(windows),'plots':len(outputs),'original_files_unchanged':len(preserve)}))


def render_pages(summary,sources,works,chapters,groups,plots,result_dir,original_report):
    bysource={s['id']:s for s in sources};wbyid={w['id']:w for w in works}
    graphpage=PUB/'catalog/plots.html';rows=[]
    for p in plots:
        rows.append([esc(p['level']),esc(p['balance'] or '—'),esc(p['method'].upper()),p['vectors'],
             link(PUB/'catalog'/p['html_file'],'Open scatter',graphpage),link(PUB/'catalog'/p['cosine_file'],'Original 1024D cosine',graphpage),
             link(PUB/'catalog'/p['neighbors_file'],'All-row neighbors',graphpage),link(PUB/'catalog'/p['parameters_file'],'Parameters',graphpage)])
    page(graphpage,'Interactive views',f'<p>All saved vectors are plotted. The chapter heatmap has 120 selected rows; work/philosopher heatmaps show 153/35 rows. Neighbors use original 1024D vectors.</p>'+table(['Level','Balance','Method','Points','Scatter','Cosine','Neighbors','Parameters'],rows))
    catalog=PUB/'catalog/works.html';rows=[]
    for w in works:
        detail=PUB/'catalog/works'/(w['catalog_anchor']+'.html')
        rows.append([esc('; '.join(w['authors'])),link(detail,w['title'],catalog),esc(w['attribution_status']),
                     link(PUB/'catalog/sources'/(w['source_id']+'.html'),w['source_id'],catalog),esc(w['translator'] or 'Unknown'),
                     esc(w['edition'].get('edition_year') or 'Edition year unknown'),w['chapter_count'],esc(readable_types(w['unit_types']))])
        detail_rows=[]
        evidence=[]
        for index in w['chapters']:
            u=chapters[index]
            text=(result_dir/u['text_file']).read_text()
            detail_rows.append([f'<a href="#{esc(u["id"])}">{esc(u["title"])}</a>',esc(u['unit_type'].replace('_',' ')),u['total_chapter_tokens'],u['windows'],
                link(result_dir/u['text_file'],'Primary text',detail),esc(u['id'])])
            evidence.append(f'<details id="{esc(u["id"])}"><summary>{esc(u["title"])} · {esc(u["unit_type"].replace("_"," "))}</summary>'
                f'<p>Canonical span [{u["source_start"]}, {u["source_end"]}); acceptance: {esc(u["status"])}; human-approved: {str(u["human_approved"]).lower()}.</p>'
                f'<p><strong>Starts</strong></p><blockquote>{esc(text[:300])}</blockquote><p><strong>Ends</strong></p><blockquote>{esc(text[-300:])}</blockquote>'
                +link(result_dir/u['text_file'],'Read the complete accepted unit',detail)+'</details>')
        body=f'<p class="eyebrow">Work row {w["row_index"]} · {esc("; ".join(w["authors"]))} · {esc(w["attribution_status"])}</p>'
        body+=f'<p>Translator: {esc(w["translator"] or "Unknown")}. Language: {esc(w["language"])}. '+link(PUB/'catalog/sources'/(w['source_id']+'.html'),'Edition and source evidence',detail)+'</p>'
        body+='<p>'+link(result_dir/'works.json','Work vector metadata and explicit row order',detail)+' · '+link(result_dir/'work_vectors.npy','1024D work vectors',detail)+'</p>'
        body+=table(['Native title','Type','Total unit tokens','Windows','Text','Unit ID'],detail_rows)
        body+='<h2>Source boundary excerpts</h2><p>Exact excerpts from the accepted text; these support inspection and do not confer independent human approval. Full canonical text, block dispositions and source mappings are linked from the edition page.</p>'+''.join(evidence)
        page(detail,w['title'],body)
    page(catalog,'Catalog of 153 represented works','<p>These are edition-level translated items and individual essays, drawn from 60 source documents. They are not 153 books or philosophers. Parent Books/Parts are not duplicate works.</p>'
         +f'<p>{link(PUB/"catalog/works.csv","Download CSV",catalog)} · {link(PUB/"catalog/works.json","Download JSON",catalog)}</p>'+table(['Author / attribution','Work','Status','Source document','Translator','Edition','Units','Types'],rows,True))
    catalog=PUB/'catalog/sources.html';rows=[]
    for s in sources:
        sid=s['id'];ws=[w for w in works if w['source_id']==sid];us=[u for u in chapters if u['source_id']==sid];path=PUB/'catalog/sources'/(sid+'.html')
        rows.append([link(path,s['title'],catalog),esc(sid),len(ws),len(us),sum(u['windows'] for u in us),esc(s['translator'] or 'Unknown')])
        source_dir=PUB/'sources'/sid
        details='<p>'+esc('; '.join(s['authors']))+' · '+esc(s['language'])+' · Translator: '+esc(s['translator'] or 'Unknown')+'</p>'
        details+='<p>'+link(source_dir/'canonical.txt','Complete canonical source (credit emails redacted; offsets preserved)',path)+' · '+link(source_dir/'ledger.json','Included/excluded block ledger',path)+' · '+link(source_dir/'unit_mappings.json.gz','Exact piecewise unit maps (gzip)',path)+' · '+link(source_dir/'profile.json','Source-checked profile',path)+'</p>'
        details+='<p><a href="'+esc(s['catalog_url'])+'">Publisher catalog and source information</a> · '+link(PUB/'notices/sources'/f'{sid}.txt','Source rights and credits',path)+'</p>'
        details+='<dl><dt>Original HTML SHA256</dt><dd class="hash">'+s['raw_html_sha256']+'</dd><dt>Retrieved</dt><dd>'+s['retrieved_utc']+'</dd><dt>Edition metadata (unknowns are null)</dt><dd><pre>'+esc(json.dumps(s['publication'],ensure_ascii=False,indent=2))+'</pre></dd></dl>'
        details+='<p>'+esc(s['metadata_note'] or '')+'</p>'
        details+=table(['Represented work','Units','Native types'],[[link(PUB/'catalog/works'/(w['catalog_anchor']+'.html'),w['title'],path),w['chapter_count'],esc(readable_types(w['unit_types']))] for w in ws])
        page(path,s['title'],details)
    page(catalog,'60 source documents','<p>Every requested source has represented units under the documented inclusion policy. Composition, translation, print-edition and digital release dates are distinct.</p>'+table(['Document title','Source ID','Works','Units','Windows','Translator'],rows,True))
    path=PUB/'catalog/attributions.html';rows=[]
    for g in groups:
        rows.append([f'<span id="{g["catalog_anchor"]}">{esc(g["name"])}</span>',esc(g['group_kind']),g['works'],g['chapters'],esc('; '.join(g['authors']))])
    page(path,'35 attribution groups','<p>30 individual centroid groups, four traditional groups and one joint Marx/Engels group. Joint authorship is not silently divided between individual centroids. Work-balanced means equal weight per work; chapter-balanced means equal weight per accepted native unit, not per independently identified idea.</p>'+table(['Group','Kind','Works','Native units','Attribution labels'],rows,True)+f'<p>{link(result_dir/"philosophers.json","Both aggregation methods and explicit row order",path)}</p>')
    path=PUB/'CORPUS_REPORT.html'
    hero='<p class="eyebrow">Completed dense BGE-M3 corpus · publication edition</p><div class="stats">'+''.join(f'<div><strong>{n}</strong><span>{esc(t)}</span></div>' for n,t in [('60','source documents'),('153','work identities'),('35','attribution groups'),('1,731','native-unit vectors'),('1,996','embedding windows')])+'</div>'
    hero+='<p class="lead">Explore the represented works, inspect source boundaries, and compare saved dense representations. This publication is a portable derivative of the completed research report; the original run identity and hashes are retained in provenance.</p>'
    hero+='<p class="actions">'+link(PUB/'catalog/works.html','Browse the work catalog',path)+' '+link(PUB/'catalog/plots.html','Open all twelve plots',path)+' '+link(PUB/'REPORT.md','Read the full Markdown report',path)+'</p>'
    hero+='<aside>'+esc(LIMIT)+' Genuine BGE-M3 ColBERT inference remains blocked and is not a result of this publication.</aside>'
    hero+='<h2 id="coverage">Coverage and extraction</h2><p>60 eligible sources, no partially eligible or blocked sources under the frozen policy; 1,560 single-window and 171 oversized units. All 51,744 canonical blocks are accounted for: 36,320 included and 15,424 excluded. Rule acceptance is separate from human approval.</p>'
    hero+='<p>Books and Parts remain native subdivisions; collections can contain several works. Epictetus has 51 native headings in this edition, Laozi has 81 sections, and the Analects source contains twenty Books, despite a title advertising other Classics. The Gita translator reports omitted concluding shlokas. See '+link(PUB/'REPORT.md','edition limits and inclusion policy',path)+'.</p>'
    hero+='<h2 id="visualizations">Interactive results</h2>'+table(['Level','Balance','Method','Points','Scatter','Cosine'],[[r[0],r[1],r[2],r[3],link(PUB/'catalog'/p['html_file'],'Open',path),link(PUB/'catalog'/p['cosine_file'],'Open',path)] for r,p in zip(rows_for_plots(plots),plots)])
    pca=[]
    for p in plots:
        if p['method']=='pca':
            ratios=p['diagnostics']['explained_variance_ratio'];pca.append([esc(p['level']),esc(p['balance'] or '—'),f'{ratios[0]:.2%}',f'{ratios[1]:.2%}',f'{sum(ratios):.2%}'])
    hero+='<h2 id="geometry">What the geometry measures</h2><p>Every unit descriptor is a normalized 1024D vector. Fitting units use one native embedding; oversized units use a normalized mean weighted by unique owned tokens. All native window vectors are included. Work vectors use equal unit weights; philosopher vectors have separate work-balanced and chapter-balanced methods. Means are computed in 1024D before projection. Separate projections are not overlaid.</p>'
    hero+='<p>Cosine heatmaps and nearest neighbors use the original vectors, not the plotted coordinates. Chapter heatmaps show a deterministic 120-row subset; work/group heatmaps show all 153/35 rows. All-row neighbor scores use bounded 128×N blocks.</p>'+table(['PCA level','Balance','PC1','PC2','Combined'],pca)
    hero+='<h2 id="verification">Verification and reproducibility</h2><p>The historical run made 1,828 new requests, reused 168 windows and recorded zero failed attempts in 571.964 seconds of inference/checkpointing. A completed restart dispatched zero new requests. Historical GPU samples reached 100% utilization and 1,194 MiB model-process VRAM; host offload was not quantified. No inference is performed by this publication.</p>'
    hero+='<p>'+link(PUB/'verification/index.html','Publication and research checks',path)+' · '+link(PUB/'analysis/README.md','Offline analysis reproduction',path)+' · '+link(PUB/'provenance/TRANSFORMATIONS.md','Publication transformations',path)+'</p>'
    page(path,'Corpus report · '+PUBLIC_NAME,hero)
    page(PUB/'verification/index.html','Verification evidence','<p>Publication checks are fresh checks on this exported copy. The historical 81-test result is retained separately and is not represented as a new model experiment.</p>'
        +'<ul>'+''.join('<li>'+link(PUB/p,label,PUB/'verification/index.html')+'</li>' for p,label in [
        ('verification/publication_checks.json','Static links, fragments and containment'),('verification/vector_checks.json','Saved-vector and aggregation checks'),
        ('verification/relocation_checks.json','Checks after relocation outside the research checkout'),('verification/browser_checks.json','Actual browser rendering and navigation'),
        ('verification/research_checks.json','Historical research verification derivative'),('verification/research_tests.txt','Historical 81-test log'),
        ('provenance/original_artifacts.json','Original and derivative artifact hashes')])+'</ul>')


def rows_for_plots(plots):return [[esc(p['level']),esc(p['balance'] or '—'),esc(p['method'].upper()),p['vectors']] for p in plots]


def write_docs(summary,result_dir):
    write(PUB/'README.md',f'''# Philosophical classification

A self-contained publication of **{PUBLIC_NAME}**: 60 source documents,
153 edition-level work identities, 35 attribution groups, and 1,731 normalized
1024-dimensional native-unit vectors. No model, Python, internet connection or
local service is needed to view the saved interactive results.

**Start here:** [CORPUS_REPORT.html](CORPUS_REPORT.html) ·
[Work catalog](catalog/works.html) · [All plots](catalog/plots.html) ·
[Full report](REPORT.md) · [Verification](verification/index.html).

## Open locally

Clone/download the repository or extract its ZIP. Keep the folder structure.
Double-click `CORPUS_REPORT.html`, or on Linux:

```sh
cd philosophical_classification
xdg-open CORPUS_REPORT.html
```

GitHub's regular file viewer shows HTML source; it does not execute the report
or Plotly charts. Download the files to view them interactively. The report,
catalog search, plots and local source evidence use relative paths and bundled
assets. Optional external source citations do not prevent offline viewing.

## Folder guide

- `CORPUS_REPORT.html`, `REPORT.md`: publication report and complete current scope.
- `catalog/`: searchable works, sources, attribution groups, CSV/JSON and plot index.
- `visualizations/`: twelve saved scatter views, four cosine heatmaps, coordinates,
  reducer parameters and all-row nearest neighbors. All refer to saved data.
- `results/{PUBLIC_NAME}/`: exact saved native/chapter/work/group vector values
  and explicit row metadata. Native window results are collated scientific arrays,
  not a copied inference cache.
- `texts/`, `sources/`: accepted text, canonical source derivatives, block ledgers,
  profiles and compressed exact source mappings. No raw book scripts/images run.
- `analysis/`: model-free validation and original aggregation functions.
- `assets/`, `notices/`: shared Plotly JavaScript, local styling and rights/credits.
- `provenance/`, `verification/`: original identities, transformations, hashes and checks.

## Scope and limits

60 documents do not mean 60 philosophers. The 35 groups comprise 30 individual
centroid groups, four traditional groups and one joint Marx/Engels group. Work
identities follow the translated items/essays represented by these editions.
Structural source inspection is not independent human approval. Proximity does
not establish philosophical agreement; 2D distances are approximate and chapter
descriptors are lossy. Genuine ColBERT output was unavailable and is not claimed.

## Optional analysis, not model inference

Viewing needs no environment. Optional validation uses a locally installed Python
3.10+ and NumPy; see [analysis instructions](analysis/README.md). The research
pipeline, model weights, virtual environments, download/inference caches,
redundant historical runs and temporary files are intentionally excluded.
This is sufficient to verify the published dense aggregation and saved plots;
it is not a complete model-inference installation.

The publication alias is a presentation name. Scientific IDs, hashes and lineage
remain recorded in [lineage.json](provenance/lineage.json). Private operational
paths and credit email addresses were removed in documented derivatives.

## GitHub upload and optional Pages

Create a new empty repository yourself. Upload **this folder's contents**, keeping
all subdirectories, then commit through GitHub or your own local Git workflow.
Do not upload the ZIP into that repository as a substitute for the folder contents.
No remote repository, push or Pages deployment was created by this packaging task.

For optional GitHub Pages, serve the repository root from your chosen branch.
`index.html` links/redirects to the report and `.nojekyll` keeps these static assets
unchanged. All report links work under a repository subpath. Rights vary by item:
read [LICENSE_NOTES.md](LICENSE_NOTES.md) before public redistribution. No umbrella
license was invented for the existing project code or research outputs.
''')
    pca=next(p for p in read(PUB/'catalog/plots.json')['plots'] if p['level']=='chapter' and p['method']=='pca')
    write(PUB/'REPORT.md',f'''# Completed philosophical corpus · {PUBLIC_NAME}

This is the publication edition of the completed corpus report, derived from the
actual full-corpus report and the chapter-first report. Original report hashes
and presentation changes are in [provenance](provenance/TRANSFORMATIONS.md).

| Object | Completed count |
|---|---:|
| Source documents / selected editions | 60 |
| Edition-level work identities | 153 |
| Attribution groups | 35 |
| Individual centroid groups | 30 |
| Traditional / joint groups | 4 / 1 |
| Final native-unit vectors | 1,731 × 1024 |
| Input windows / unique owned tokens | 1,996 / 5,214,383 |
| Single-window / multi-window units | 1,560 / 171 |
| Newly inferred / reused windows | 1,828 / 168 |
| Failed requests | 0 |

Browse the [153-work catalog](catalog/works.html), [60-source inventory](catalog/sources.html),
[attribution groups](catalog/attributions.html), [CSV](catalog/works.csv) and
[interactive report](CORPUS_REPORT.html). Work records expose original author or
tradition, translator, edition observations, source document, unit types/counts
and source/result links. Unknown dates remain unknown; composition, translation,
print-edition and digital-release dates are distinct.

## Completed full-corpus run versus history

The full accepted catalog completed in 571.964 seconds of inference/checkpointing,
excluding source inspection and token planning. Actual in-flight RTX 4060 samples
reached 100% utilization, 1,194 MiB model-process VRAM and 1,263 MiB total VRAM.
CPU layer offload was not quantified by the empty process table; host allocations
do not establish CPU-only execution. No embedding inference or training occurred
during publication packaging. The historical three-source 146-vector run is a
separate earlier result; its 146 vectors were verified bit-for-bit unchanged.

All 60 requested documents have represented accepted units under the recorded
inclusion policy. The original report records no unresolved substantive body
blocks: 36,320 included and 15,424 excluded blocks. This is source-checked structural
acceptance, not independent human approval or a semantic stance benchmark.

## Extraction and edition policy

57 new source-specific profiles share one range engine; the original three profiles
remain frozen. Guards pin original HTML hashes, parser identities, actual headings,
containers, contents destinations and work ranges. Chapters, Books, Parts, sections,
aphorisms, essays, letters, lectures and whole-work units remain distinguishable.
Parents and children are not duplicated as full primary inputs. In flat Critique
of Pure Reason markup the analysis uses exclusive source-heading sections with
their own prose. The lecture family includes James's native Postscript.

New profiles include author argument, verse, integral author appendices, scholia
and introductions within works. Standalone front prefaces/dedications and later
editorial introductions, translator notes/summaries, contents, pagination and
publisher matter are excluded from embedding inputs and retained separately.
Legacy profiles retain their historical appendix policy so previous vectors are
not silently changed. A dialogue speaker is not automatically its author or an
endorsed position. Notes are removed without fragmenting continuous paragraphs.

Edition limits are explicit: 51 native Epictetus headings; 81 Laozi sections;
130+52 Novum Organum aphorisms rather than internal Roman lists; only Analects
Books I–XX despite the title's wider advertised collection; three Machiavelli works;
translator-reported omissions of Gita concluding shlokas; a separate L. A. Magnus
credit for Nietzsche's closing poem. Complete installed-edition coverage does not
claim completeness of every original recension. Source texts and credits remain
traceable through each catalog source page.

## Dense algorithm and original-space geometry

BGE-M3 is frozen. Its verified limit is 8192 **total** tokens including special
tokens/headings: context=8192, physical token batch=8192, one text/request,
truncate=false. Inputs use the pinned tokenizer/adapter, not character counts.
Fitting units use one complete native embedding; only oversized units split,
with 256-token overlap and complete unique ownership. No generated summaries or
metadata prefixes replace source text.

One-window descriptors retain the native vector. Multiple windows use
`normalize(sum(unique_owned_tokens_i * window_vector_i) / sum(unique_owned_tokens_i))`.
Ownership removes duplicate weights, not residual contextual influence from overlap.
Work vectors use equal unit weights. Philosopher **work-balanced** vectors give
equal weight to work centroids; **chapter-balanced** vectors give equal weight to
accepted native units across works. Chapter-balanced is not idea-balanced.
Joint authorship and traditional groups remain explicit. All means are calculated
and normalized in original 1024D space before projection.

The chapter matrix is 1,731 × 1024. Cosine similarities use original normalized
vectors. PCA/UMAP/t-SNE produce approximate 2D views; independently fitted levels
are not overlaid. Chapter PCA explains **13.2128%** in two components, work PCA
17.0952%, philosopher work-balanced PCA 30.5294%, and chapter-balanced PCA 30.7928%.
Seeds, installed versions, parameters and exact coordinates are included per plot.
Chapter heatmaps use a deterministic 120-row subset; work/group heatmaps use all
153/35 vectors. All-row nearest neighbors use bounded 128×N score blocks.

## Results and checks

[All twelve scatter views and four cosine heatmaps](catalog/plots.html) include
the complete selected level. [Saved matrices and explicit row metadata](results/{PUBLIC_NAME}/chapters.json)
are aligned by IDs. [Analysis instructions](analysis/README.md) reproduce the
aggregation checks without model inference. All native window representations
and ownership weights are included for the transparent dense baseline.

Historical verification records 81 passing HTML tests, real short DOM fixtures,
source/window reconstruction, cache invalidation, interruption/resume, zero new
requests on completed restart, original-vector preservation and GPU measurements.
Fresh publication checks and actual browser outcomes are in the
[verification index](verification/index.html). Packaging checks are distinct from
historical model experiments. No genuine ColBERT inference was available; none
is claimed. No training was performed. Geometric proximity may reflect topic,
style, translation and length, and does not prove philosophical agreement.
''')
    write(PUB/'LICENSE_NOTES.md','''# Rights, credits and scope

No repository-wide license has been invented for the original project code,
research outputs or source material. The supplied research checkout contained no
project license file. The owner must choose any license they wish to grant for
their original contributions; publication here is not a new license grant.

The 60 source metadata records describe the editions as unrestricted/public-domain
under US law. These are the research source observations, not a new worldwide
rights determination. Source-specific rights/credits and applicable ebook notices
are preserved in `notices/sources/` and alongside extracted texts in `texts/`;
canonical copies preserve the corresponding material. Producer names are retained;
unnecessary volunteer contact emails are redacted in length-preserving canonical
derivatives. Original bytes remain untouched in the research checkout.

Project Gutenberg is acknowledged as a source, not used as this publication's
brand, and no endorsement is implied. Its [license](https://www.gutenberg.org/policy/license.html)
and [permission guidance](https://www.gutenberg.org/policy/permission.html) distinguish
US rights, source restrictions and trademark conditions. Check applicable local
copyright law before redistribution outside the US. Read the original source
notices, especially if redistributing individual texts separately.

The bundled Plotly JavaScript retains its upstream header (plotly.js 3.7.0) and
MIT notice in [Plotly-LICENSE.txt](notices/Plotly-LICENSE.txt). It is supplied from
the installed Plotly 6.9.0 distribution, with no external CDN dependency. The
embedded figures are presentation derivatives; figure data/layouts are unchanged.
Optional NumPy/scikit-learn/UMAP libraries are not vendored. Model weights and
tokenizer assets are not redistributed; model identity and hashes are provenance.
''')
    write(PUB/'provenance/TRANSFORMATIONS.md','''# Publication transformations

The presentation alias is `catalog60_8192_v2`. The original run identifier is
preserved only where required for scientific lineage, in [lineage.json](lineage.json).
No original research artifact was moved or modified.

- The main HTML/Markdown report is a clearly identified publication derivative,
  combining the completed run report with the relevant chapter-first REPORT.md.
  It adds a searchable work catalog, relative navigation and explicit counts.
- The 168 MB aggregate JSON repeated source profiles in every unit. Compact,
  normalized metadata replaces those repetitions; original artifact hashes,
  scientific IDs, model/tokenizer identities and saved vector values are retained.
- Chapter vectors are byte-copied. Existing individual work/group/native window
  arrays are collated into explicitly indexed matrices without changing values.
  Inference/download caches, intermediate runs, model weights and environments
  are not part of the publication.
- Twelve selected scatter charts and four heatmaps are exported from the explicit
  plot manifest. One byte-identical shared Plotly bundle replaces redundant inline
  copies. Only outer presentation text/navigation changes; original figure data
  and layouts are checked for equality, and embedded numerical JavaScript is not
  globally rewritten. The upstream library includes generic URL-scheme handling;
  this is not an active local-file or network dependency of these charts.
- Canonical credit-email redaction preserves Unicode character offsets; original
  and derivative hashes are recorded. Primary accepted text is copied unchanged.
  Full unit source maps are compressed, not discarded. No original HTML scripts
  or image dependencies are required for the publication's source views.
- Machine-local paths, usernames, operational contacts and service endpoints are
  omitted from publication derivatives of logs/metadata. Historical test results
  remain labeled historical. No scientific identifier is renamed to claim a new
  experiment. Private original root paths are not publication dependencies.
- Earlier pilots and intermediate visualizations are summarized, not redundantly
  republished. Optional analysis code validates existing arrays only; viewing has
  no Python or model requirement. The complete model-inference installation is
  intentionally outside this static publication.

[Original artifact hashes and derivative map](original_artifacts.json) ·
[Original dependency graph](original_dependency_graph.json) ·
[Preservation checks](../verification/original_preservation.json).
''')
    write(PUB/'analysis/README.md',f'''# Offline analysis of published results

Report viewing needs no Python. Optional scripts below use ordinary local Python
3.10+; no original virtual environment, local service, model, training framework
or inference is required.

```sh
cd philosophical_classification
python3 analysis/verify_portability.py
python3 analysis/verify_vectors.py
```

The portability checker uses the standard library. Vector validation needs NumPy;
the research used NumPy 1.26.4. [aggregations.py](aggregations.py) reuses the original
`unit`, `describe`, `validate_vector` and `chapter_descriptor` functions with only
local error-helper/import adaptation. It recomputes means for verification, not
new embeddings. [Dependencies](../provenance/dependencies.json) preserve the
research versions; no packages were installed by the packaging task.

[Chapter metadata](../results/{PUBLIC_NAME}/chapters.json) binds each vector row
to unit/work/edition IDs and native-window rows. [Windows](../results/{PUBLIC_NAME}/windows.json)
bind 1,996 native vectors to exact input hashes, core/context spans and ownership.
Work and philosopher metadata bind their row order and constituent indices.
Numeric matrices are NumPy `.npy` files with pickles disabled. Source mappings
are standard gzip-compressed JSON files, readable using `gzip` and `json`.

The saved scatter coordinates, reducer configurations and library versions are
linked from the [plot catalog](../catalog/plots.html). These suffice to inspect
the existing analysis; rerunning the full extraction/inference research requires
the separate source checkout, frozen tokenizer assets and model backend. They
are deliberately not installed or silently downloaded here. Code licensing is
documented in [LICENSE_NOTES.md](../LICENSE_NOTES.md).
''')
    write(PUB/'analysis/requirements.txt','numpy==1.26.4\n')
    write(PUB/'.gitignore','__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.env\n.env.*\n.DS_Store\nThumbs.db\n*.log\n*.tmp\nanalysis_outputs/\n*.zip\n')
    write(PUB/'.nojekyll','')
    write(PUB/'index.html','<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=CORPUS_REPORT.html"><title>Philosophical classification</title></head><body><a href="CORPUS_REPORT.html">Open the corpus report</a></body></html>')
    write(PUB/'assets/site.css',':root{--ink:#20312d;--muted:#62716d;--paper:#f7f6ef;--line:#d8ddd4;--accent:#18634e}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}header,nav,main,footer{max-width:1220px;margin:auto;padding:22px 28px}header{display:flex;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{font-weight:800;text-decoration:none}nav{display:flex;gap:20px;flex-wrap:wrap;padding-top:12px;padding-bottom:12px;border-bottom:1px solid var(--line)}a{color:var(--accent);text-underline-offset:3px}a:hover{color:#071c15}h1{font:600 clamp(32px,4vw,52px)/1.15 Georgia,serif;max-width:1000px}h2{font:600 28px Georgia,serif;margin-top:42px}.lead{font-size:20px;max-width:850px}.eyebrow{color:var(--muted);font-size:13px;text-transform:uppercase;letter-spacing:.09em}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:28px 0}.stats div{border:1px solid var(--line);padding:17px;background:white}.stats strong{display:block;font:600 32px Georgia,serif}.stats span{font-size:13px;color:var(--muted)}aside{border-left:4px solid var(--accent);padding:14px 22px;background:#e9efe6;margin:25px 0}.actions{display:flex;gap:14px;flex-wrap:wrap}.actions a{background:var(--accent);color:white;padding:10px 18px;text-decoration:none;border-radius:3px}.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td,th{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#e9ede5}tr:hover td{background:#f1f6ef}.search{display:block;margin:24px 0 4px;font-weight:600}input{display:block;width:min(700px,100%);font:inherit;padding:12px;border:1px solid #a4b4ab;border-radius:4px;margin-top:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:15px}.hash{font:12px monospace;overflow-wrap:anywhere}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line);margin-top:50px}dt{font-weight:700}dd{margin-left:0;margin-bottom:12px}@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}header{display:block}header span{display:block;font-size:12px}nav{gap:10px}main{padding:16px}td,th{padding:9px}}')
    write(PUB/'assets/catalog.js','document.querySelectorAll("[data-filter]").forEach(function(input){const table=document.querySelector("[data-searchable]");if(!table)return;const rows=Array.from(table.tBodies[0].rows),count=document.querySelector("[data-count]");function update(){const query=input.value.toLocaleLowerCase();let visible=0;rows.forEach(function(row){row.hidden=!row.textContent.toLocaleLowerCase().includes(query);if(!row.hidden)visible++});if(count)count.textContent=visible+" of "+rows.length+" entries"}input.addEventListener("input",update);update()});')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True)
    args=parser.parse_args();build(args.source_root.resolve())

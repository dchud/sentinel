#!/usr/bin/env python

from pylab import *

from canary.context import Context
from canary.loader import QueuedRecord
from canary.search import SearchIndex
from canary.study import Species, Study, Methodology


linkages = {
    'rel': 'Relationships', 
    'inter': 'Interspecies', 
    'exp': 'Exposures', 
    'out': 'Outcomes', 
    'exp_sh': 'Shared Exposures',
    'out_sh': 'Shared Outcomes',
    'gen': 'Genomic Data'}
linkages_attrs = (
    ('rel', 'relationships'),
    ('exp', 'exposures'),
    ('out', 'outcomes'),
    ('inter', 'interspecies'),
    ('gen', 'genomic'),
    ('exp_sh', 'exposure_linkage'),
    ('out_sh', 'outcome_linkage'),
    )
    
    
linkages_sorted = linkages.items()
linkages_sorted.sort()
linkage_keys = ('exp', 'out', 'rel', 'inter', 'exp_sh', 'out_sh', 'gen')

methodology_types = {}
for val, id in Methodology().TYPES.items():
    methodology_types[id] = val
start = dict(zip(methodology_types.keys(), array([0] * len(linkages))))


def makeplot (context, token, records):

    this_module = sys.modules[__name__]
    N = len(linkage_keys)
    ind = arange(N)
    width = 0.35

    meth_type_count = {}

    study_count = dict(zip(linkages, array([0] * len(linkages))))
    for id, type in linkages_attrs:
        meth_type_count[id] = start.copy()

    for rec in records:
        study = Study(context, rec.study_id)
        for attr, key in linkages_attrs:
            if getattr(study, 'has_%s' % key):
                study_count[attr] += 1
                for meth in study.methodologies:
                    meth_type_count[attr][meth.study_type_id] += 1
                            
                        
    rc('grid', color=0.85, linestyle='-', linewidth=0.3)
    grid(True)

    yoff = array([0] * N)
    
    s = """
            'experimental' : 1,
        'descriptive' : 2,
        'aggregate' : 3,
        'cross sectional' : 4,
        'cohort' : 5,
        'case control' : 6,
        'disease model' : 7,
        """
    
    print ['%s %s\n' % (k, v) for k, v in meth_type_count.items()]
    
    p_exp_x = [meth_type_count[key][1] for key in linkage_keys]
    p_exp = bar(ind, p_exp_x, width, color='#993333', bottom=yoff)
    yoff = yoff + p_exp_x
    
    p_coh_x = [meth_type_count[key][5] for key in linkage_keys]
    p_coh = bar(ind, p_coh_x, width, color='#FF9933', bottom=yoff)
    yoff = yoff + p_coh_x
    
    p_csec_x = [meth_type_count[key][4] for key in linkage_keys]
    p_csec = bar(ind, p_csec_x, width, color='#99CC99', bottom=yoff)
    yoff = yoff + p_csec_x
    
    p_desc_x = [meth_type_count[key][2] for key in linkage_keys]
    p_desc = bar(ind, p_desc_x, width, color='#6666CC', bottom=yoff)
    yoff = yoff + p_desc_x
        
    #p_agg_x = [meth_type_count[key][3] for key in linkage_keys]
    #p_agg = bar(ind, p_agg_x, width, color='#CCCC00', bottom=yoff)
    #yoff = yoff + p_agg_x
    
    #p_cc_x = [meth_type_count[key][6] for key in linkage_keys]
    #p_cc = bar(ind, p_cc_x, width, color='#CC66FF', bottom=yoff)
    #yoff = yoff + p_cc_x
    
    #p_dm_x = [meth_type_count[key][7] for key in linkage_keys]
    #p_dm = bar(ind, p_dm_x, width, color='#993366', bottom=yoff)
    #yoff = yoff + p_dm_x
    
    precords_x = array([len(records)] * N)
    #precords = bar(ind+width/3, precords_x, width/3, color='#999999', bottom=0)
    precords = plot(precords_x, color='#AAAAAA', marker='-', linewidth=1.5)
    
    pstudies_x = [study_count[k] for k in linkage_keys]
    pstudies = bar(ind+width/3, pstudies_x, width/3, color='#EEEEEE', bottom=0)

    max_val = max(yoff)
    xlabel('Linkages to Human Health')
    ylabel('# Methodologies by Type for Studies with Linkages')
    title('Animal Sentinels for "%s" (%s records)' % 
        (token, len(records)), size=12)
    xticks(ind+width/2, [linkages[k] for k in linkage_keys], 
        rotation=20, size=6)
    step = max_val / 5
    yticks(arange(0, max_val+(step*3), step))

    legend((p_exp[0], p_coh[0], p_csec[0], p_desc[0],
        precords[0], pstudies[0]),
        ('Experimental', 'Cohort', 
        'Cross-Sectional', 'Descriptive', 
        '# Studies Total', '# Records w/Linkage'))
##    legend((p_exp[0], p_desc[0], p_agg[0], p_csec[0], p_coh[0],
##        p_cc[0], p_dm[0], precords[0], pstudies[0]),
##        ('Experimental', 'Descriptive', 'Aggregate', 
##        'Cross-Sectional', 'Cohort', 'Case-Control', 'Disease Model',
    
    #savefig(('%s' % token.replace(' ', '_')))
    show()
    cla()



if __name__ == '__main__':
    context = Context()
    search_index = SearchIndex(context)
    searches = (
        'Lead [exposure]', 
        'Hantavirus [exposure]', 
        'peromyscus [species]',
        'Michigan [location]',
        'DDT [exposure]',
        '2003 [year]',
        'cats and dogs',
        '"Burger J" [author]',
        'cross-sectional [methodology]',
        'case-control [methodology] and cattle [species]',
        'disease-model [methodology]',
        '"age factors" [risk_factors]',
        'Sarin [exposure]',
        'Arsenic [exposure]',
        '"Bacillus anthracis" [exposure]',
        '"West Nile Virus" [exposure]',
        '"Water Pollutants, Chemical" [exposure]',
        ) 
    for t in searches:
        hits, searcher = search_index.search(t)
        result_set = []
        for i, doc in hits:
            uid = doc.get(str('uid'))
            record = QueuedRecord(context, uid)
            if record.status == record.STATUS_CURATED:
                result_set.append(record)
        searcher.close()
        makeplot(context, t, result_set)

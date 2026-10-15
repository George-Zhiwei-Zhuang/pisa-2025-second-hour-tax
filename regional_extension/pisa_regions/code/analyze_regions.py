#!/usr/bin/env python3
"""Regroup archived PV/Fay-BRR system estimates and test regional differences."""
from pathlib import Path
import hashlib
import itertools
import json
import platform
import sys

import numpy as np
import pandas as pd
from scipy import optimize, stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'tables'
CFG = json.loads((ROOT / 'config' / 'regions.json').read_text())
ORDER = [g['region'] for g in CFG['regions']]
ZH = {g['region']: g['region_zh'] for g in CFG['regions']}
MAP = {code: g['region'] for g in CFG['regions'] for code in g['codes']}
NAMES = json.loads((ROOT / 'config' / 'system_names.json').read_text())


def bh(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adjusted = np.minimum.accumulate((p[order] * len(p) / np.arange(1, len(p)+1))[::-1])[::-1]
    result = np.empty(len(p))
    result[order] = np.minimum(1, adjusted)
    return result


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    result = np.empty(len(p))
    result[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return result


def fit(data, mapping=None, fixed=False):
    """REML with region intercepts; modified Knapp-Hartung t/F inference."""
    d = data.copy()
    if mapping is not None:
        d['region'] = d['system'].map(mapping)
    assert d['region'].notna().all()
    assert d['system'].is_unique, 'Use one independent estimate per system.'
    assert np.isfinite(d[['b', 'se']]).all().all() and (d.se > 0).all()
    levels = [g for g in ORDER if g in d.region.unique()]
    levels += sorted(set(d.region) - set(levels))
    x = np.column_stack([(d.region == g).astype(float) for g in levels])
    y, v = d.b.to_numpy(float), d.se.to_numpy(float)**2
    k, g = x.shape
    df = k-g
    assert df > 0

    def restricted_nll(tau2):
        w = 1/(v+tau2)
        sw = x.T @ w
        mu = (x.T @ (w*y))/sw
        residual = y-x@mu
        return 0.5 * (np.log(v+tau2).sum() + np.log(sw).sum() + (w*residual**2).sum())

    if fixed:
        tau2 = 0.0
    else:
        upper = max(1e-6, np.var(y)*10, np.max(v)*5)
        result = optimize.minimize_scalar(restricted_nll, bounds=(0,upper), method='bounded',
                                          options={'xatol': max(1e-13,upper*1e-11)})
        assert result.success and result.x < upper*0.999, 'REML optimum must be interior or at zero.'
        tau2 = float(result.x) if result.fun < restricted_nll(0) else 0.0
    w = 1/(v+tau2)
    sw = x.T @ w
    mu = (x.T @ (w*y))/sw
    q = float((w*(y-x@mu)**2).sum())
    scale = max(1.0, q/df) if not fixed else 1.0
    covariance = np.diag(scale/sw)
    se = np.sqrt(np.diag(covariance))
    critical = float(stats.t.ppf(.975,df)) if not fixed else 1.959963984540054
    mean_p = 2*stats.t.sf(abs(mu/se),df) if not fixed else 2*stats.norm.sf(abs(mu/se))
    means=[]
    for j, region in enumerate(levels):
        group=d.loc[d.region == region]
        means.append({'region': region, 'region_zh': ZH.get(region,region),
                      'systems': len(group), 'students': int(group.n.sum()),
                      'negative_systems': int((group.b < 0).sum()),
                      'coefficient': float(mu[j]), 'standard_error': float(se[j]),
                      'ci_low': float(mu[j]-critical*se[j]), 'ci_high': float(mu[j]+critical*se[j]),
                      'p_value': float(mean_p[j]), 'df': int(df),
                      'equal_system_mean': float(group.b.mean()), 'sparse': len(group)<3})
    pairs=[]
    for a,b in itertools.combinations(range(g),2):
        diff=float(mu[a]-mu[b])
        diffse=float(np.sqrt(covariance[a,a]+covariance[b,b]-2*covariance[a,b]))
        p = float(2*stats.t.sf(abs(diff/diffse),df)) if not fixed else float(2*stats.norm.sf(abs(diff/diffse)))
        pairs.append({'region_a':levels[a], 'region_b':levels[b], 'difference_a_minus_b':diff,
                      'standard_error':diffse, 'ci_low': diff-critical*diffse,
                      'ci_high':diff+critical*diffse, 'p_value':p, 'df':int(df)})
    pairs=pd.DataFrame(pairs)
    if len(pairs):
        pairs['q_bh']=bh(pairs.p_value)
        pairs['p_holm']=holm(pairs.p_value)
    contrasts=np.zeros((g-1,g))
    contrasts[:,0]=-1
    contrasts[np.arange(g-1),np.arange(1,g)]=1
    difference=contrasts@mu
    wcov=contrasts@covariance@contrasts.T
    statistic=float(difference@np.linalg.solve(wcov,difference)/(g-1))
    if fixed:
        omnibus_p=float(stats.chi2.sf(statistic*(g-1),g-1))
    else:
        omnibus_p=float(stats.f.sf(statistic,g-1,df))
    info={'systems':k,'regions':g,'tau_squared':tau2,'residual_scale':scale,
          'residual_q':q,'omnibus_f':statistic,'df_num':g-1,'df_denom':df,
          'omnibus_p_value':omnibus_p,'method':'fixed' if fixed else 'REML modified Knapp-Hartung'}
    return pd.DataFrame(means),pairs,info


def extract(source, prefix='', mapping=MAP, ncol='n'):
    d=source[['system',ncol,f'{prefix}coefficient',f'{prefix}standard_error']].copy()
    d.columns=['system','n','b','se']
    d['region']=d.system.map(mapping)
    return d


def reference_summary(b,se):
    b,se=np.asarray(b),np.asarray(se)
    v=se**2
    w=1/v
    fixed=float(np.average(b,weights=w))
    q=float(np.sum(w*(b-fixed)**2))
    c=float(w.sum()-np.sum(w*w)/w.sum())
    tau=max(0,(q-(len(b)-1))/c)
    rw=1/(v+tau)
    return {'fixed_coefficient':fixed,'fixed_standard_error':float(np.sqrt(1/w.sum())),
            'random_coefficient':float(np.average(b,weights=rw)),
            'random_standard_error':float(np.sqrt(1/rw.sum())),
            'tau_squared':float(tau),'q':q}


def separate_group_summary(data):
    rows=[]
    for region,group in data.groupby('region',sort=False):
        b=group.b.to_numpy();se=group.se.to_numpy();k=len(b)
        dl=reference_summary(b,se); w=1/(se**2+dl['tau_squared'])
        mu=dl['random_coefficient']; scale=max(1,float(np.sum(w*(b-mu)**2)/(k-1)))
        hse=float(np.sqrt(scale/w.sum())); crit=stats.t.ppf(.975,k-1)
        eq=float(b.mean()); eqse=float(b.std(ddof=1)/np.sqrt(k))
        rows.append({'region':region,'systems':k,'dl_coefficient':mu,'dl_mkh_se':hse,
                     'dl_mkh_ci_low':mu-crit*hse,'dl_mkh_ci_high':mu+crit*hse,
                     'dl_mkh_p':float(2*stats.t.sf(abs(mu/hse),k-1)),
                     'equal_coefficient':eq,'equal_se':eqse,
                     'equal_ci_low':eq-crit*eqse,'equal_ci_high':eq+crit*eqse,
                     'tau_squared':dl['tau_squared']})
    return pd.DataFrame(rows)


def welch_contrasts(data):
    rows=[]
    levels=[g for g in ORDER if g in data.region.unique()]
    for a,b in itertools.combinations(levels,2):
        aa=data.loc[data.region==a,'b'].to_numpy();bb=data.loc[data.region==b,'b'].to_numpy()
        va=aa.var(ddof=1)/len(aa);vb=bb.var(ddof=1)/len(bb)
        df=(va+vb)**2/(va**2/(len(aa)-1)+vb**2/(len(bb)-1))
        diff=aa.mean()-bb.mean();se=np.sqrt(va+vb);crit=stats.t.ppf(.975,df)
        rows.append({'region_a':a,'region_b':b,'difference_a_minus_b':float(diff),
                     'standard_error':float(se),'df':float(df),'ci_low':float(diff-crit*se),
                     'ci_high':float(diff+crit*se),'p_value':float(2*stats.t.sf(abs(diff/se),df))})
    result=pd.DataFrame(rows)
    result['q_bh']=bh(result.p_value);result['p_holm']=holm(result.p_value)
    return result


def welch_omnibus(data):
    """Welch's one-way ANOVA on system effects, allowing unequal group variances."""
    groups=[g.b.to_numpy() for _,g in data.groupby('region')]
    n=np.asarray([len(g) for g in groups],float)
    y=np.asarray([g.mean() for g in groups]);v=np.asarray([g.var(ddof=1)/len(g) for g in groups])
    assert (n>=2).all() and (v>0).all()
    w=1/v;g=len(groups)
    correction=float(np.sum((1-w/w.sum())**2/(n-1)))
    f=float(np.sum(w*(y-np.average(y,weights=w))**2)/(g-1)/(1+2*(g-2)/(g*g-1)*correction))
    df2=float((g*g-1)/(3*correction))
    return {'systems':int(n.sum()),'regions':g,'omnibus_f':f,'df_num':g-1,'df_denom':df2,
            'omnibus_p_value':float(stats.f.sf(f,g-1,df2)),
            'method':'Equal-system Welch ANOVA, unequal region variances'}


def separate_contrasts(summary):
    """Independent regional DL/mKH summaries with Welch-Satterthwaite contrasts."""
    rows=[]
    for a,b in itertools.combinations([g for g in ORDER if g in set(summary.region)],2):
        aa=summary.loc[summary.region==a].iloc[0];bb=summary.loc[summary.region==b].iloc[0]
        va,vb=aa.dl_mkh_se**2,bb.dl_mkh_se**2
        df=(va+vb)**2/(va*va/(aa.systems-1)+vb*vb/(bb.systems-1))
        diff=aa.dl_coefficient-bb.dl_coefficient;se=np.sqrt(va+vb);crit=stats.t.ppf(.975,df)
        rows.append({'region_a':a,'region_b':b,'difference_a_minus_b':float(diff),
                     'standard_error':float(se),'df':float(df),'ci_low':float(diff-crit*se),
                     'ci_high':float(diff+crit*se),'p_value':float(2*stats.t.sf(abs(diff/se),df))})
    pairs=pd.DataFrame(rows);pairs['q_bh']=bh(pairs.p_value);pairs['p_holm']=holm(pairs.p_value)
    return pairs


def key_contrast(pairs, a='East Asia',b='Western Europe'):
    direct=pairs[(pairs.region_a==a)&(pairs.region_b==b)]
    if len(direct): return direct.iloc[0].to_dict()
    reverse=pairs[(pairs.region_a==b)&(pairs.region_b==a)].iloc[0].to_dict()
    low,high=reverse['ci_low'],reverse['ci_high']
    reverse.update(region_a=a,region_b=b,difference_a_minus_b=-reverse['difference_a_minus_b'],ci_low=-high,ci_high=-low)
    return reverse


def save(frame,name):
    frame.to_csv(OUT/name,index=False,float_format='%.14g')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    hashes=json.loads((ROOT/'inputs/input_hashes.json').read_text())
    for name,digest in hashes.items():
        assert hashlib.sha256((ROOT/'inputs'/name).read_bytes()).hexdigest()==digest,name
    source=pd.read_csv(ROOT/'inputs/system_main_effects.csv')
    assert source.system.is_unique and len(source)==84 and source.n.sum()==205114
    assert set(source.system)==set(MAP) and len(MAP)==sum(len(g['codes']) for g in CFG['regions'])
    reference=json.loads((ROOT/'inputs/main_effects.json').read_text())
    checks={}
    for scale in ['points','sd']:
        actual=reference_summary(source[f'{scale}_coefficient'],source[f'{scale}_standard_error'])
        for field,value in actual.items(): assert np.isclose(value,reference[scale][field],rtol=1e-11,atol=1e-11),(scale,field)
        checks[scale]=actual
    checks.update(students=int(source.n.sum()),systems=len(source),negative_systems=int((source.sd_coefficient<0).sum()),
                  sd_variance_identity_max_error=float(abs(source.sd_standard_error**2-source.sd_variance_sampling-source.sd_variance_plausible).max()))
    assert checks['negative_systems']==78 and checks['sd_variance_identity_max_error']<1e-13
    d=extract(source,'sd_')
    cross=source.copy();cross.insert(1,'system_name',cross.system.map(NAMES));cross['region']=cross.system.map(MAP);cross['region_zh']=cross.region.map(ZH)
    save(cross,'system_region_crosswalk.csv')
    means,pairs,info=fit(d)
    save(means,'regional_main_sd.csv');save(pairs,'regional_pairwise_sd.csv')
    points=extract(source,'points_')
    pointmeans,pointpairs,pointinfo=fit(points)
    save(pointmeans,'regional_main_points.csv');save(pointpairs,'regional_pairwise_points.csv')
    separate=separate_group_summary(d)
    save(separate,'regional_alternative_summaries.csv')
    separate_pairs=separate_contrasts(separate)
    save(separate_pairs,'separate_region_variance_contrasts.csv')
    welch=welch_contrasts(d);save(welch,'equal_system_welch_contrasts.csv')
    fixedmeans,fixedpairs,fixedinfo=fit(d,fixed=True)
    save(fixedmeans,'regional_fixed_sd.csv');save(fixedpairs,'regional_fixed_contrasts.csv')
    sensitivity=[]
    south_sensitivity=[]
    def record(label,frame=d,mapping=None,a='East Asia',b='Western Europe'):
        _,pp,ii=fit(frame,mapping=mapping)
        sensitivity.append({'specification':label,**key_contrast(pp,a,b),**ii})
        if a=='East Asia' and 'Southern Europe' in set(frame.region):
            south_sensitivity.append({'specification':label,**key_contrast(pp,a,'Southern Europe'),**ii})
    record('Primary 12-region REML model')
    science=pd.read_csv(ROOT/'inputs/system_comparative_effects.csv')
    science_d=extract(science.loc[science.pair=='science'],'ldw_sd_')
    record('Science-LDW pair only',science_d)
    support=pd.read_csv(ROOT/'inputs/system_support_sensitivity.csv')
    support2=extract(support.loc[support.minimum_students_per_order==2],'sd_',ncol='sd_n')
    record('At least two students per order within stratum',support2)
    record('Exclude Mongolia from East Asia',d.loc[d.system!='MNG'])
    singapore_map={**MAP,'SGP':'East Asia'}
    record('East Asia plus Singapore (alternative definition)',mapping=singapore_map)
    merged={c:('Western and Northern Europe' if r in ['Western Europe','Northern Europe'] else r) for c,r in MAP.items()}
    record('East Asia versus Western and Northern Europe',mapping=merged,b='Western and Northern Europe')
    for codes in [['ARM'],['LBN'],['ARM','LBN']]:record('Exclude '+', '.join(codes),d.loc[~d.system.isin(codes)])
    caucasus_map={c:('Caucasus' if c in ['ARM','AZE','GEO'] else r) for c,r in MAP.items()}
    record('Split Caucasus from Western Asia (diagnostic)',mapping=caucasus_map)
    supported=d.loc[~d.region.isin(['Northern America','Australia and New Zealand','Africa'])]
    record('Only regions with at least three systems',supported)
    sensitivity.append({'specification':'Equal-system means with Welch inference',**key_contrast(welch)})
    sensitivity.append({'specification':'Fixed-effect inverse-variance synthesis',**key_contrast(fixedpairs),**fixedinfo})
    save(pd.DataFrame(sensitivity),'east_asia_western_europe_robustness.csv')
    for label,pp in [('Equal-system Welch',welch),('Separate-region DL mKH',separate_pairs)]:
        south_sensitivity.append({'specification':label,**key_contrast(pp,'East Asia','Southern Europe')})
    save(pd.DataFrame(south_sensitivity),'east_asia_southern_europe_robustness.csv')
    loo=[]
    south_loo=[]
    for code in d.system:
        _,pp,ii=fit(d.loc[d.system!=code])
        loo.append({'omitted_system':code,**key_contrast(pp),**ii})
        south_loo.append({'omitted_system':code,**key_contrast(pp,'East Asia','Southern Europe'),**ii})
    save(pd.DataFrame(loo),'east_asia_western_europe_leave_one_out.csv')
    save(pd.DataFrame(south_loo),'east_asia_southern_europe_leave_one_out.csv')
    regional_sensitivity=[];regtest=[]
    for label,dd,mapping in [('Primary',d,MAP),('Support two',support2,MAP),('Science only',science_d,MAP),
                              ('Exclude ARM and LBN',d.loc[~d.system.isin(['ARM','LBN'])],MAP),
                              ('Split Caucasus',d,caucasus_map),('Exclude sparse regions',supported,MAP)]:
        mm,pp,ii=fit(dd,mapping=mapping);mm.insert(0,'specification',label)
        regional_sensitivity.append(mm);regtest.append({'specification':label,**ii})
    save(pd.concat(regional_sensitivity,ignore_index=True),'regional_robustness_means.csv')
    save(pd.DataFrame(regtest),'regional_robustness_omnibus.csv')
    equal_omnibus=[]
    for label,dd in [('All 12 groups',d),('At least three systems per region',supported),
                     ('Exclude ARM and LBN',d.loc[~d.system.isin(['ARM','LBN'])])]:
        equal_omnibus.append({'specification':label,**welch_omnibus(dd)})
    save(pd.DataFrame(equal_omnibus),'equal_system_welch_omnibus.csv')
    comparison=[]
    for label,pp in [('Primary REML common residual variance',pairs),('Separate-region DL mKH',separate_pairs),
                     ('Equal-system Welch',welch)]:
        rows=pp.copy();rows.insert(0,'method',label);comparison.append(rows)
    save(pd.concat(comparison,ignore_index=True),'all_contrasts_alternative_methods.csv')
    paired=[];pairedtests=[]
    for pair in ['science','reading','math']:
        s=science.loc[science.pair==pair]
        for outcome,prefix in [('LDW standardized','ldw_sd_'),('Conventional standardized','conventional_sd_'),('Direct point gap','gap_points_')]:
            dd=extract(s,prefix);mm,pp,ii=fit(dd)
            mm.insert(0,'outcome',outcome);mm.insert(0,'pair',pair)
            paired.append(mm);pairedtests.append({'pair':pair,'outcome':outcome,**ii})
    save(pd.concat(paired,ignore_index=True),'regional_mirrored_pairs.csv')
    pt=pd.DataFrame(pairedtests);pt['q_bh_9']=bh(pt.omnibus_p_value)
    save(pt,'regional_mirrored_pairs_omnibus.csv')
    processes=pd.read_csv(ROOT/'inputs/system_process_effects.csv')
    processmeans=[];processtests=[];processkey=[]
    for outcome in ['credit_assigned','disengaged','not_reached','total_time_log','actions_log']:
        dd=extract(processes.loc[processes.outcome==outcome]);mm,pp,ii=fit(dd)
        if outcome.endswith('_log'):
            transform=lambda arr: 100*np.expm1(arr)
            unit='percent change in (1 + outcome)'
        else:
            transform=lambda arr:100*arr
            unit='percentage points'
        for field in ['coefficient','ci_low','ci_high']:mm['display_'+field]=transform(mm[field])
        mm.insert(0,'outcome',outcome);mm['display_unit']=unit;processmeans.append(mm)
        processtests.append({'outcome':outcome,**ii})
        processkey.append({'outcome':outcome,**key_contrast(pp)})
    save(pd.concat(processmeans,ignore_index=True),'regional_process_outcomes.csv')
    pt=pd.DataFrame(processtests);pt['q_bh_5']=bh(pt.omnibus_p_value)
    save(pt,'regional_process_omnibus.csv')
    pk=pd.DataFrame(processkey);pk['q_bh_5']=bh(pk.p_value)
    save(pk,'east_asia_western_europe_process_contrasts.csv')
    result={'primary_sd':info,'secondary_points':pointinfo,'international_reference_checks':checks,
            'east_asia_western_europe':key_contrast(pairs),
            'east_asia_southern_europe':key_contrast(pairs,'East Asia','Southern Europe'),
            'equal_system_welch_omnibus':equal_omnibus,
            'significant_pairwise_raw':int((pairs.p_value<.05).sum()),
            'significant_pairwise_bh':int((pairs.q_bh<.05).sum()),
            'significant_pairwise_holm':int((pairs.p_holm<.05).sum()),
            'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
            'analysis_level':'archived system estimates, no microdata refit'}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print(means[['region','systems','students','coefficient','ci_low','ci_high','equal_system_mean']].to_string(index=False))
    print('\nContrasts passing BH across 66 tests:')
    print(pairs.loc[pairs.q_bh<.05].to_string(index=False))


if __name__=='__main__':main()

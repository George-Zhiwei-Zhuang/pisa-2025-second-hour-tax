#!/usr/bin/env python3
"""Make a regional forest plot and a compact report from analyzed tables."""
from pathlib import Path
from html import escape
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT=Path(__file__).resolve().parents[1]
TABLES=ROOT/'output/tables'
FIGS=ROOT/'output/figures'
RESULT=json.loads((TABLES/'results.json').read_text())
CFG=json.loads((ROOT/'config/regions.json').read_text())
NAMES=json.loads((ROOT/'config/system_names.json').read_text())
MAIN=pd.read_csv(TABLES/'regional_main_sd.csv')
INK='#182D4A';TEAL='#007F83';BLUE='#3466A4';GRAY='#778391';LIGHT='#F2F5F8'


def pformat(value):
    return '<0.0001' if value<.0001 else f'{value:.4f}'


def forest():
    FIGS.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.spines.left':False})
    fig=plt.figure(figsize=(11.2,7.2),facecolor='white')
    gs=fig.add_gridspec(1,2,width_ratios=[3.5,1.9],left=.30,right=.98,top=.82,bottom=.18,wspace=.05)
    ax=fig.add_subplot(gs[0]);txt=fig.add_subplot(gs[1],sharey=ax)
    y=np.arange(len(MAIN))[::-1]
    for i,row in MAIN.iterrows():
        color=GRAY if row['sparse'] else TEAL if row.region in ['East Asia','South-eastern Asia','Central Asia'] else BLUE if 'Europe' in row.region else INK
        if i%2==0:
            ax.axhspan(y[i]-.45,y[i]+.45,color=LIGHT,zorder=0)
            txt.axhspan(y[i]-.45,y[i]+.45,color=LIGHT,zorder=0)
        ax.errorbar(row.coefficient,y[i],xerr=[[row.coefficient-row.ci_low],[row.ci_high-row.coefficient]],
                    fmt='o',color=color,ecolor=color,markersize=6,capsize=3,elinewidth=1.8)
        txt.text(.02,y[i],f'{row.coefficient:+.3f}  [{row.ci_low:+.3f}, {row.ci_high:+.3f}]',
                 va='center',ha='left',fontsize=9.0,color=INK,fontfamily='DejaVu Sans Mono')
    ax.axvline(0,color='#7C8998',lw=1,ls='--',zorder=1)
    ax.set_xlim(-.22,.035);ax.set_ylim(-.6,len(MAIN)-.4)
    ax.set_xticks([-.20,-.15,-.10,-.05,0]);ax.set_xticklabels(['-0.20','-0.15','-0.10','-0.05','0.00'])
    labels=[f'{row.region}{" *" if row["sparse"] else ""}  (k={row.systems})' for _,row in MAIN.iterrows()]
    ax.set_yticks(y,labels=labels);ax.tick_params(axis='y',length=0,pad=12,labelsize=10)
    ax.tick_params(axis='x',colors=INK);ax.spines['bottom'].set_color('#C2CCD6')
    ax.set_xlabel('LDW second minus first (within-system SD)',labelpad=12,color=INK)
    txt.set_xlim(0,1);txt.axis('off')
    txt.text(.02,1.03,'Estimate and 95% CI',transform=txt.transAxes,color=INK,fontsize=10,fontweight='bold')
    fig.text(.045,.935,'The second-hour penalty differs across regions',fontsize=19,fontweight='bold',color=INK)
    fig.text(.045,.891,'84 education systems | 205,114 students | Geography based on UN M49',fontsize=11,color=GRAY)
    fig.text(.045,.080,'Negative values indicate a larger LDW second-hour penalty.',fontsize=10,color=INK)
    fig.text(.045,.046,'REML regional meta-regression; modified Knapp-Hartung intervals. * Only two systems; sparse coverage.',fontsize=9,color=GRAY)
    fig.savefig(FIGS/'PISA_Regional_Second_Hour_Effects.png',dpi=190,facecolor='white')
    fig.savefig(FIGS/'PISA_Regional_Second_Hour_Effects.pdf',facecolor='white')
    plt.close(fig)


def report():
    fontroot=Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('DV',str(fontroot/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DV-Bold',str(fontroot/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleX',fontName='DV-Bold',fontSize=22,leading=28,textColor=colors.HexColor(INK),spaceAfter=12))
    styles.add(ParagraphStyle(name='SubX',fontName='DV',fontSize=9,leading=13,textColor=colors.HexColor(GRAY),spaceAfter=14))
    styles.add(ParagraphStyle(name='HeadX',fontName='DV-Bold',fontSize=12,leading=17,textColor=colors.HexColor(INK),spaceBefore=10,spaceAfter=7))
    styles.add(ParagraphStyle(name='BodyX',fontName='DV',fontSize=9.2,leading=14,textColor=colors.HexColor(INK),spaceAfter=8))
    styles.add(ParagraphStyle(name='SmallX',fontName='DV',fontSize=8,leading=11.5,textColor=colors.HexColor(GRAY),spaceAfter=7))
    styles.add(ParagraphStyle(name='CellX',fontName='DV',fontSize=8.1,leading=11,textColor=colors.HexColor(INK)))
    styles.add(ParagraphStyle(name='CellHeadX',fontName='DV-Bold',fontSize=8,leading=11,textColor=colors.white))
    story=[]
    def para(text,style='BodyX'):story.append(Paragraph(text,styles[style]))
    def title(text,subtitle):para(text,'TitleX');para(subtitle,'SubX')
    def table(rows,widths,fs=8.1):
        converted=[]
        for i,row in enumerate(rows):
            style=styles['CellHeadX' if i==0 else 'CellX']
            converted.append([Paragraph(str(c),style) for c in row])
        tt=Table(converted,colWidths=widths,hAlign='LEFT',repeatRows=1)
        tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor(LIGHT)]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
            ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBELOW',(0,0),(-1,0),.4,colors.HexColor(INK))]))
        story.append(tt);story.append(Spacer(1,8))
    def page():story.append(PageBreak())
    width=A4[0]-88

    title('Regional heterogeneity in<br/>the second-hour tax','The Second-Hour Tax, PISA 2025 | Empirical supplement | 10 October 2026')
    para('<b>Finding.</b> The magnitude of the LDW second-hour penalty varies by region. '
         'The strongest main-sample contrast across alternative synthesis methods is East Asia versus Southern Europe. '
         'East Asia versus Western Europe is directionally consistent but fails correction across all regional comparisons.')
    para('The original archived estimates reproduce the paper: <b>84 systems, 205,114 students, 78 negative system effects</b>, '
         'and an international fixed-effect mean of -0.0931 within-system SD. The new analysis changes geographic synthesis, '
         'while retaining each system\'s original plausible-value and Fay-BRR uncertainty.')
    para('Regional LDW-second effects','HeadX')
    rows=[['Region','k','Students','Effect (SD)','95% CI']]
    for _,r in MAIN.iterrows():
        rows.append([r.region+(' *' if r['sparse'] else ''),r.systems,f'{r.students:,}',f'{r.coefficient:.3f}',f'[{r.ci_low:.3f}, {r.ci_high:.3f}]'])
    table(rows,[166,48,65,73,width-352])
    para('k = education systems. Primary synthesis: one region intercept per group, REML residual between-system variance, '
         'modified Knapp-Hartung intervals with 72 degrees of freedom. More negative means a larger penalty. '
         '* Two-system groups borrow the common residual variance and have limited regional coverage. Africa combines Kenya and Morocco.','SmallX')
    para('<b>Interpretation.</b> East Asian, South-eastern Asian and Central Asian averages are relatively close to zero, '
         'but their confidence intervals do not establish zero effects. Geography is an effect modifier, not a randomly assigned treatment.')

    page()
    title('The regional pattern','Primary model and explicit between-region tests')
    story.append(Image(str(FIGS/'PISA_Regional_Second_Hour_Effects.png'),width=width,height=width*7.2/11.2))
    para('Two comparisons of substantive interest','HeadX')
    comparisons=pd.read_csv(TABLES/'all_contrasts_alternative_methods.csv')
    rows=[['Contrast','Method','Difference (SD)','p','BH q']]
    method_short={'Primary REML common residual variance':'REML / mKH','Separate-region DL mKH':'Separate-region DL / mKH','Equal-system Welch':'Equal-system / Welch'}
    for b in ['Western Europe','Southern Europe']:
        subset=comparisons[(comparisons.region_a=='East Asia')&(comparisons.region_b==b)]
        for _,r in subset.iterrows():
            rows.append(['East Asia - '+b,method_short[r.method],f'+{r.difference_a_minus_b:.3f}',pformat(r.p_value),pformat(r.q_bh)])
    table(rows,[135,153,85,60,width-433])
    para('Each BH correction uses the same complete family of 66 regional pairs. Positive contrasts mean a smaller penalty in East Asia. '
         'The primary East Asia - Southern Europe contrast is 0.092 SD, 95% CI [0.036, 0.148]. Its primary Holm-adjusted p is 0.101; '
         'the main claim is therefore about FDR-controlled exploratory evidence, rather than uniform familywise significance.','SmallX')
    para('Five primary comparisons pass BH, but only East Asia versus Southern Europe also passes BH under both '
         'separate regional variance estimation and equal-system Welch inference. The strong East Asia versus Western Asia '
         'comparison in the common-variance model weakens when Western Asia\'s larger dispersion is allowed.')

    page()
    title('What survives the checks','Separate overall heterogeneity from certainty about a particular pair')
    para('Overall equality of regional means','HeadX')
    rr=pd.read_csv(TABLES/'regional_robustness_omnibus.csv')
    ew=pd.read_csv(TABLES/'equal_system_welch_omnibus.csv')
    rows=[['Specification','Systems / regions','p']]
    for label in ['Primary','Support two','Science only','Exclude ARM and LBN','Exclude sparse regions']:
        r=rr.loc[rr.specification==label].iloc[0]
        label2={'Primary':'REML: all regions','Support two':'REML: at least two students per order','Science only':'REML: science-LDW pair only',
                'Exclude ARM and LBN':'REML: omit Armenia and Lebanon','Exclude sparse regions':'REML: regions with at least three systems'}[label]
        rows.append([label2,f'{r.systems} / {r.regions}',pformat(r.omnibus_p_value)])
    for _,r in ew.iloc[:2].iterrows():
        rows.append(['Welch: '+r.specification,f'{r.systems} / {r.regions}',pformat(r.omnibus_p_value)])
    table(rows,[width-162,100,62])
    para('The equal-system, unequal-variance test over all 12 groups is borderline (p=0.0510). '
         'Its degrees of freedom are constrained by the three two-system groups. With the pre-specified minimum of '
         'three systems per region, the nine-group Welch test gives p=0.0016. Regional heterogeneity is therefore supported '
         'in the adequately covered groups, while the sparse groups deserve descriptive interpretation.')
    para('East Asia versus Southern Europe: narrower samples','HeadX')
    ss=pd.read_csv(TABLES/'east_asia_southern_europe_robustness.csv')
    rows=[['Specification','Difference','p','BH q']]
    for label in ['Primary 12-region REML model','Science-LDW pair only','At least two students per order within stratum','Exclude Mongolia from East Asia']:
        r=ss.loc[ss.specification==label].iloc[0]
        short={'Primary 12-region REML model':'Primary main sample','Science-LDW pair only':'Science-LDW pair only',
               'At least two students per order within stratum':'At least two students per order','Exclude Mongolia from East Asia':'Exclude Mongolia'}[label]
        rows.append([short,f'+{r.difference_a_minus_b:.3f}',pformat(r.p_value),pformat(r.q_bh)])
    table(rows,[width-193,69,62,62])
    para('The contrast retains its direction under stricter support and a common paired domain, but fails their '
         '66-comparison FDR correction. Across all 84 leave-one-system-out models its point estimate ranges from '
         '+0.084 to +0.102 SD, while BH q ranges from 0.005 to 0.089. It is promising evidence, not a universally significant result.')
    para('Influence and geographic choices','HeadX')
    para('Omitting Armenia and Lebanon changes Western Asia\'s mean from -0.153 to -0.115 SD, yet the regional REML '
         'omnibus remains significant (p=0.0031). East Asia - Western Europe stays positive in every leave-one-system-out '
         'run (+0.060 to +0.080 SD); its unadjusted p can rise to 0.073. Singapore remains in South-eastern Asia in the '
         'primary classification, and an East Asia-plus-Singapore sensitivity is recorded separately.')

    page()
    title('Secondary evidence','Domain pairing and response/process outcomes')
    para('Does geography matter within the same mirrored pair?','HeadX')
    pp=pd.read_csv(TABLES/'regional_mirrored_pairs_omnibus.csv')
    rows=[['Mirrored pair','LDW: p / BH q','Paired domain: p','Direct point gap: p / BH q']]
    for pair in ['science','reading','math']:
        s=pp[pp.pair==pair]
        l=s.loc[s.outcome=='LDW standardized'].iloc[0];c=s.loc[s.outcome=='Conventional standardized'].iloc[0];g=s.loc[s.outcome=='Direct point gap'].iloc[0]
        rows.append([pair.title()+' - LDW',pformat(l.omnibus_p_value)+' / '+pformat(l.q_bh_9),pformat(c.omnibus_p_value),pformat(g.omnibus_p_value)+' / '+pformat(g.q_bh_9)])
    table(rows,[105,128,107,width-340])
    para('BH uses the nine outcome-by-pair omnibus tests. There is regional variation in LDW penalties and direct '
         'LDW-minus-conventional point-gap effects in all three pairings. The tests do not detect regional heterogeneity '
         'in the conventional-domain gain when that domain moves earlier. A nonsignificant test does not establish equal effects. '
         'Reading and mathematics use 83 systems because the conventional-domain plausible values are unavailable in Uzbekistan.','SmallX')
    para('Response and process effects by selected region','HeadX')
    process=pd.read_csv(TABLES/'regional_process_outcomes.csv')
    rows=[['Region','Credit (pp)','Disengaged (pp)','Time (%)','Actions (%)']]
    for region in ['East Asia','South-eastern Asia','Western Europe','Southern Europe','Western Asia']:
        s=process[process.region==region].set_index('outcome')
        rows.append([region]+[f'{s.loc[o,"display_coefficient"]:+.2f}' for o in ['credit_assigned','disengaged','total_time_log','actions_log']])
    table(rows,[137,85,100,85,width-407])
    para('Credit is normalized item credit; disengagement is the share with the released disengagement status. '
         'Time and actions are 100[exp(beta)-1] from log(1 + outcome), so the exact percentage interpretation concerns '
         '(1 + time) and (1 + actions). Full regional estimates and intervals are in the CSV outputs.','SmallX')
    para('Five process-outcome omnibus tests','HeadX')
    tests=pd.read_csv(TABLES/'regional_process_omnibus.csv')
    rows=[['Outcome','p','BH q (five tests)']]
    labels={'credit_assigned':'Normalized credit','disengaged':'Disengaged share','not_reached':'Not-reached share','total_time_log':'Total time: log(1 + time)','actions_log':'Actions: log(1 + actions)'}
    for _,r in tests.iterrows():rows.append([labels[r.outcome],pformat(r.omnibus_p_value),pformat(r.q_bh_5)])
    table(rows,[width-198,82,116])
    para('All five process outcomes show regional heterogeneity in the primary model. Nevertheless, none of the five '
         'East Asia - Western Europe process contrasts passes its five-test BH correction (q=0.070 to 0.972). '
         'These patterns characterize responses to test position; they do not identify a causal mediation pathway.')

    page()
    title('Geography and reproducibility','An explicit crosswalk for every participating system')
    rows=[['Region','Participating systems']]
    for group in CFG['regions']:
        names=', '.join(NAMES[c] for c in group['codes'])
        rows.append([group['region'],escape(names)])
    table(rows,[140,width-140])
    para('M49 places Armenia, Azerbaijan, Georgia and Turkiye in Western Asia, and the Baltic systems in Northern Europe. '
         'Chinese Taipei is assigned to East Asia and Kosovo to Southern Europe for statistical geography. '
         'B-S-J-Z is Beijing, Shanghai, Jiangsu and Zhejiang rather than all mainland China. Ukrainian regions represent '
         '17 of 27 regions. Oceania here contains only Australia and New Zealand.','SmallX')
    para('Data level and model','HeadX')
    para('This supplement uses archived system coefficients and total variances from replication version 1.1.0. '
         'It does not download student microdata or refit the student regressions. The primary model is '
         '<b>tau_hat(c) = mu(region(c)) + u(c) + e(c)</b>, with released Var[e(c)] and common REML Var[u(c)]. '
         'Modified Knapp-Hartung scales covariance by max{1, residual Q/(K-G)}. All regional contrasts retain their '
         'complete multiple-testing families. No two estimates from the same system are treated as independent in one model.')
    para('Run and sources','HeadX')
    para('The accompanying package contains untouched estimate inputs and hashes, the geographic crosswalk, analysis code, '
         'all comparison and robustness tables, and this report. Run <b>python3 code/analyze_regions.py</b>, then '
         '<b>python3 code/make_deliverables.py</b>. Integrity checks reproduce original international summaries and sample totals.','SmallX')
    para('United Nations Statistics Division, M49: <link href="https://unstats.un.org/unsd/methodology/m49/" color="#3466A4">unstats.un.org/unsd/methodology/m49/</link><br/>'
         'OECD (2026), PISA 2025 Results, Volume I, Reader\'s Guide: '
         '<link href="https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en/full-report/reader-s-guide_0364240f.html" color="#3466A4">PISA system names and codes</link><br/>'
         'Original analysis: The Second-Hour Tax LaTeX manuscript and replication package version 1.1.0.','SmallX')

    report_path=ROOT/'output/PISA_Regional_Heterogeneity_Report.pdf'
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#D9E1E8'))
        canvas.line(44,38,A4[0]-44,38);canvas.setFont('DV',7.5);canvas.setFillColor(colors.HexColor(GRAY))
        canvas.drawString(44,25,'PISA LDW regional supplement | Archived system-level estimates')
        canvas.drawRightString(A4[0]-44,25,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(report_path),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=42,bottomMargin=48,
                          title='Regional Heterogeneity in the PISA LDW Second-Hour Tax',author='Zhiwei Zhuang')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(report_path)


if __name__=='__main__':
    forest()
    report()

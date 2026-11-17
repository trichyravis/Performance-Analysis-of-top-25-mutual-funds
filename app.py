
from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="Top 25 Mutual Fund Analytics | Mountain Path Academy", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

NAVY, NAVY2, BLUE, GOLD, GOLD2, PALE = "#081F3A", "#0B2545", "#124A78", "#F3C84B", "#D4A017", "#EEF3F8"

st.markdown("""
<style>

.stApp{background:#223247;color:#E6EEF5;font-family:Arial,sans-serif}
.block-container{padding-top:2rem;max-width:1500px}
h1,h2,h3{font-family:Arial,sans-serif!important;color:#E6EEF5!important;letter-spacing:-.02em}
p,li,label{font-size:1.05rem;line-height:1.65}
.hero{background:#101F34;padding:1.5rem 1.7rem;border-radius:12px;border:1px solid #19476A;margin-bottom:1rem}
.hero h1{font-size:2rem!important;margin:.7rem 0;color:#E6EEF5!important}.hero p{color:#B9D7E2}.hero b,.eyebrow{color:#FFD23F}
.eyebrow{display:inline-block;background:#FFD23F;color:#101F34;padding:.3rem .65rem;border-radius:4px;font-size:.75rem;font-weight:800;letter-spacing:.08em}
.kpi{background:#101F34;border:1px solid #19476A;border-top:3px solid #FFD23F;border-radius:10px;padding:1rem;min-height:125px}.kpi .v{font-size:1.3rem;font-weight:700;color:#F0F5FA;overflow-wrap:anywhere}.kpi .l{font-size:.85rem;color:#B9D7E2;margin-bottom:.5rem}
section[data-testid="stSidebar"]{background:#101F34;border-right:1px solid #19476A}
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#FFD23F!important}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] label p{color:#B9D7E2!important}
section[data-testid="stSidebar"] input{background:#0B1728!important;color:#E6EEF5!important;-webkit-text-fill-color:#E6EEF5!important}
[data-baseweb="select"]>div{background:#101F34!important;color:#E6EEF5!important;border-color:#38617C!important}
[data-baseweb="tag"]{background:#284761!important;color:#FFFFFF!important}
[data-baseweb="popover"]{color:#E6EEF5}
[role="tablist"]{gap:8px;flex-wrap:wrap;overflow:visible;height:auto;background:transparent;padding:6px 0 12px}
[role="tab"]{background:#101F34!important;color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;border:1px solid #63829C!important;border-radius:7px!important;padding:.65rem .9rem!important;min-height:46px;height:auto!important;opacity:1!important;white-space:normal}
[role="tab"] *{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;font-weight:700!important;opacity:1!important;visibility:visible!important}
[role="tab"][aria-selected="true"]{background:#FFD23F!important;border-color:#FFD23F!important;color:#101F34!important;-webkit-text-fill-color:#101F34!important}
[role="tab"][aria-selected="true"] *{color:#101F34!important;-webkit-text-fill-color:#101F34!important}
[role="tab"]:focus-visible{outline:3px solid #FFFFFF;outline-offset:3px}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:#E6EEF5!important;-webkit-text-fill-color:#E6EEF5!important}
[data-testid="stCaptionContainer"] p{color:#B9CDDD!important}
.stButton button,.stDownloadButton button{background:#FFD23F!important;color:#101F34!important;border:1px solid #FFD23F!important;font-weight:700!important}
.stButton button:hover,.stDownloadButton button:hover{background:#FFE27B!important}
.pill,.note{background:#101F34;color:#D9E8F2;padding:.8rem 1rem;border-radius:8px;border:1px solid #19476A;margin:.5rem 0 1rem}
.note{border-left:3px solid #FFD23F}.pill{font-weight:600}
.footer{color:#D9E8F2;padding:1.2rem;text-align:center;margin-top:2rem;border-top:2px solid #FFD23F}.footer a{color:#FFD23F!important;font-weight:700}
@media(max-width:768px){.hero{padding:1rem}.hero h1{font-size:1.5rem!important}.block-container{padding:1rem}.kpi{min-height:100px}}
</style>
""", unsafe_allow_html=True)

# A balanced educational universe: five established Direct–Growth schemes in each
# of five diversified-equity categories. Scheme aliases handle AMC name changes.
# AUM is deliberately used as an eligibility/ranking input only when a verified
# value is maintained. The public MFAPI NAV feed does not publish scheme AUM.
FUND_UNIVERSE = {
    # Large Cap
    "Nippon India Large Cap": {"category": "Large Cap", "aliases": ["Nippon India Large Cap Fund - Direct Plan Growth Plan", "Nippon India Large Cap Fund - Direct Plan - Growth Plan"]},
    "ICICI Pru Large Cap": {"category": "Large Cap", "aliases": ["ICICI Prudential Large Cap Fund - Direct Plan Growth", "ICICI Prudential Bluechip Fund - Direct Plan - Growth"]},
    "HDFC Large Cap": {"category": "Large Cap", "aliases": ["HDFC Large Cap Fund - Direct Plan - Growth Option", "HDFC Top 100 Fund -Direct Plan - Growth Option"]},
    "Canara Robeco Large Cap": {"category": "Large Cap", "aliases": ["Canara Robeco Large Cap Fund - Direct Plan - Growth Option", "Canara Robeco Bluechip Equity Fund - Direct Plan - Growth Option"]},
    "Baroda BNP Paribas Large Cap": {"category": "Large Cap", "aliases": ["BARODA BNP PARIBAS LARGE CAP Fund - Direct Plan - Growth Option", "Baroda Large cap Fund - Plan B (Direct) - Growth Option"]},
    # Flexi Cap
    "Parag Parikh Flexi Cap": {"category": "Flexi Cap", "aliases": ["Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "Parag Parikh Flexi Cap Fund-Direct-Growth"]},
    "HDFC Flexi Cap": {"category": "Flexi Cap", "aliases": ["HDFC Flexi Cap Fund - Direct Plan - Growth Option"]},
    "JM Flexicap": {"category": "Flexi Cap", "aliases": ["JM Flexicap Fund (Direct) - Growth Option", "JM Flexicap Fund - Direct Plan - Growth Option"]},
    "Franklin India Flexi Cap": {"category": "Flexi Cap", "aliases": ["Franklin India Flexi Cap Fund - Direct - Growth", "Franklin India Flexi Cap Fund-Direct-Growth"]},
    "Quant Flexi Cap": {"category": "Flexi Cap", "aliases": ["quant Flexi Cap Fund - Direct Plan Growth", "Quant Flexi Cap Fund Direct Plan Growth"]},
    # Large & Mid Cap
    "Motilal Oswal Large & Midcap": {"category": "Large & Mid Cap", "aliases": ["Motilal Oswal Large and Midcap Fund-Direct Plan-Growth Option"]},
    "ICICI Pru Large & Mid Cap": {"category": "Large & Mid Cap", "aliases": ["ICICI Prudential Large & Mid Cap Fund - Direct Plan Growth"]},
    "HDFC Large & Mid Cap": {"category": "Large & Mid Cap", "aliases": ["HDFC Large and Mid Cap Fund - Direct Plan - Growth Option"]},
    "Bandhan Large & Mid Cap": {"category": "Large & Mid Cap", "aliases": ["Bandhan Large & Mid Cap Fund - Direct Plan - Growth", "Bandhan Core Equity Fund-Direct Plan-Growth", "IDFC Core Equity Fund - Direct Plan - Growth"]},
    "Edelweiss Large & Mid Cap": {"category": "Large & Mid Cap", "aliases": ["Edelweiss Large & Mid Cap Fund - Direct Plan - Growth Option"]},
    # Mid Cap
    "Motilal Oswal Midcap": {"category": "Mid Cap", "aliases": ["Motilal Oswal Midcap Fund-Direct Plan-Growth Option"]},
    "HDFC Mid Cap": {"category": "Mid Cap", "aliases": ["HDFC Mid Cap Fund - Growth Option - Direct Plan", "HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth Option"]},
    "Nippon India Growth Mid Cap": {"category": "Mid Cap", "aliases": ["Nippon India Growth Fund - Direct Plan Growth Plan", "Nippon India Growth Fund - Direct Plan - Growth Plan"]},
    "Kotak Midcap": {"category": "Mid Cap", "aliases": ["Kotak Midcap Fund - Direct Plan - Growth", "Kotak Emerging Equity Scheme - Direct Plan - Growth"]},
    "Invesco India Mid Cap": {"category": "Mid Cap", "aliases": ["Invesco India Mid Cap Fund - Direct Plan - Growth"]},
    # Small Cap
    "Nippon India Small Cap": {"category": "Small Cap", "aliases": ["Nippon India Small Cap Fund - Direct Plan - Growth Plan"]},
    "Bandhan Small Cap": {"category": "Small Cap", "aliases": ["Bandhan Small Cap Fund-Direct Plan-Growth"]},
    "SBI Small Cap": {"category": "Small Cap", "aliases": ["SBI Small Cap Fund - DIRECT PLAN - Growth"]},
    "HDFC Small Cap": {"category": "Small Cap", "aliases": ["HDFC Small Cap Fund - Direct Plan - Growth Option"]},
    "Franklin India Small Cap": {"category": "Small Cap", "aliases": ["Franklin India Small Cap Fund - Direct - Growth", "Franklin India Smaller Companies Fund-Direct-Growth"]},
}
TARGETS = {name: meta["aliases"] for name, meta in FUND_UNIVERSE.items()}
CATEGORIES = ["Large Cap", "Flexi Cap", "Large & Mid Cap", "Mid Cap", "Small Cap"]
MIN_HISTORY_YEARS = 5

def req_json(url):
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"}); r.raise_for_status(); return r.json()

@st.cache_data(ttl=86400, show_spinner=False)
def catalogue():
    return req_json("https://api.mfapi.in/mf")

@st.cache_data(ttl=21600, show_spinner=False)
def nav_history(code):
    raw=req_json(f"https://api.mfapi.in/mf/{code}")
    x=pd.DataFrame(raw.get("data",[]));
    if x.empty: return pd.Series(dtype=float)
    x["date"]=pd.to_datetime(x["date"],dayfirst=True,errors="coerce"); x["nav"]=pd.to_numeric(x["nav"],errors="coerce")
    return x.dropna().drop_duplicates("date").sort_values("date").set_index("date")["nav"]

def resolve_targets(cat):
    names=pd.DataFrame(cat)
    if names.empty or "schemeName" not in names or "schemeCode" not in names: return {}
    scheme_names=names.schemeName.fillna("").str.lower()
    out={}
    for short, wishes in TARGETS.items():
        candidate_codes=[]
        for w in wishes:
            hit=names[scheme_names==w.lower()]
            candidate_codes.extend(hit.schemeCode.astype(int).tolist())
        if not candidate_codes:
            tokens=[t for t in short.lower().replace("&"," ").split() if len(t)>3 and t not in {"india","fund"}]
            hit=names[scheme_names.apply(lambda s: all(t in s for t in tokens)) & scheme_names.str.contains("direct") & scheme_names.str.contains("growth")]
            candidate_codes.extend(hit.schemeCode.astype(int).tolist())
        if candidate_codes: out[short]=list(dict.fromkeys(candidate_codes))
    return out

def load_all(selected):
    try: codes=resolve_targets(catalogue())
    except Exception: codes={}
    series={}; errors=[]
    def fetch_one(name):
        candidates=[]
        for code in codes.get(name,[]):
            try:
                candidate=nav_history(code)
                if len(candidate)>50: candidates.append(candidate)
            except Exception:
                continue
        # Keep a single scheme history: do not splice potentially distinct plans.
        return max(candidates,key=lambda x:(x.index.max(),len(x))) if candidates else pd.Series(dtype=float)
    progress=st.progress(0,text="Loading selected fund histories…")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch_one,name):name for name in selected}
        for completed,future in enumerate(as_completed(futures),1):
            name=futures[future]
            try:
                result=future.result()
                if len(result)>50: series[name]=result
                else: errors.append(name)
            except Exception: errors.append(name)
            progress.progress(completed/len(selected),text=f"Loaded {completed} of {len(selected)} funds · {name}")
    progress.empty()
    ordered={name:series[name] for name in selected if name in series}
    return pd.concat(ordered,axis=1).sort_index() if ordered else pd.DataFrame(), errors

def period_start(idx, label):
    end=idx.max(); years={"1 Year":1,"3 Years":3,"5 Years":5}.get(label)
    if years: return end-pd.DateOffset(years=years)
    if label=="YTD": return pd.Timestamp(end.year,1,1)
    return idx.min()

def sliced(nav,label):
    return nav.loc[nav.index>=period_start(nav.index,label)].dropna(how="all")

def cagr(s):
    s=s.dropna()
    if len(s)<2 or s.iloc[0]<=0 or s.iloc[-1]<=0: return np.nan
    yrs=(s.index[-1]-s.index[0]).days/365.25
    return (s.iloc[-1]/s.iloc[0])**(1/yrs)-1 if yrs>0 else np.nan

def max_dd(s):
    s=s.dropna()
    if s.empty or s.iloc[0]<=0: return np.nan
    w=s/s.iloc[0]; return (w/w.cummax()-1).min()

def history_years(s):
    s=s.dropna()
    return (s.index[-1]-s.index[0]).days/365.25 if len(s)>1 else 0

def rolling_consistency(s, years=3):
    """Share of rolling periods with a positive annualised return."""
    s=s.dropna()
    window=252*years
    if len(s)<=window: return np.nan
    rolling=(s/s.shift(window))**(1/years)-1
    return (rolling.dropna()>0).mean()

def percentile_score(x, higher_is_better=True):
    x=x.replace([np.inf,-np.inf],np.nan)
    if x.notna().sum()==0: return pd.Series(0.5,index=x.index)
    filled=x.fillna(x.median())
    score=filled.rank(pct=True,method="average")
    return score if higher_is_better else 1-score+1/len(score)

def metrics(nav):
    rows=[]
    for n in nav:
        s=nav[n].dropna(); r=s.pct_change().dropna(); downside=r[r<0].std()*np.sqrt(252)
        ann=r.mean()*252; vol=r.std()*np.sqrt(252); dd=max_dd(s)
        rows.append([n,cagr(s),ann,vol,ann/vol if vol else np.nan,ann/downside if downside else np.nan,downside,dd,rolling_consistency(s),r.quantile(.05),r[r<=r.quantile(.05)].mean()])
    return pd.DataFrame(rows,columns=["Fund","CAGR","Annual Return","Volatility","Sharpe*","Sortino*","Downside Risk","Max Drawdown","Rolling Consistency","Daily VaR 95%","Daily CVaR 95%"]).set_index("Fund")

def selection_score(nav):
    """Five-year category-relative score using the published methodology."""
    five=sliced(nav,"5 Years")
    base=metrics(five)
    base["Category"]=[FUND_UNIVERSE[n]["category"] for n in base.index]
    base["History (years)"]=[history_years(nav[n]) for n in base.index]
    base["Eligible"]=(base["History (years)"]>=MIN_HISTORY_YEARS)
    parts=[]
    for _,g in base.groupby("Category",sort=False):
        s=pd.DataFrame(index=g.index)
        s["5Y CAGR score"]=percentile_score(g["CAGR"])*20
        s["Sharpe score"]=percentile_score(g["Sharpe*"])*20
        s["Rolling consistency score"]=percentile_score(g["Rolling Consistency"])*20
        s["Downside-risk score"]=percentile_score(g["Downside Risk"],False)*15
        # Max drawdown is negative: a value closer to zero is better.
        s["Drawdown score"]=percentile_score(g["Max Drawdown"])*15
        # MFAPI does not publish AUM. Keep the 10-point component neutral and
        # disclose it rather than presenting an invented live AUM value.
        s["AUM score (neutral)"]=5.0
        parts.append(s)
    scores=pd.concat(parts) if parts else pd.DataFrame(index=base.index)
    scores["Composite / 100"]=scores.sum(axis=1)
    return base.join(scores).sort_values(["Category","Composite / 100"],ascending=[True,False])

def fmt_pct(x): return "—" if pd.isna(x) else f"{x:.2%}"
def chart(fig,h=460):
    fig.update_layout(height=h,margin=dict(l=20,r=20,t=55,b=20),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#101F34",font=dict(color="#D9E8F2"),title_font=dict(color="#E6EEF5",family="Arial"),legend_title_text="",legend=dict(font=dict(color="#E6EEF5")),xaxis=dict(tickfont=dict(color="#D9E8F2"),title_font=dict(color="#D9E8F2")),yaxis=dict(tickfont=dict(color="#D9E8F2"),title_font=dict(color="#D9E8F2")))
    fig.update_xaxes(gridcolor="#28435A", zerolinecolor="#38617C")
    fig.update_yaxes(gridcolor="#28435A", zerolinecolor="#38617C")
    return fig
def kpi(label,value): st.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="hero"><span class="eyebrow">FREE LEARNING TOOL · MBA · CFA · FRM</span><h1>Mutual Fund Performance Explorer</h1><p>Compare 25 selected Indian equity funds across five categories. Explore returns, risk, consistency and investment outcomes using Direct–Growth NAV histories.</p></div>',unsafe_allow_html=True)
st.markdown('<div class="note"><b style="color:#FFD23F">How to start</b><br>1. Choose a category and funds in the sidebar.<br>2. Select an analysis horizon and a fund for detailed study.<br>3. Explore the tabs; download data from Selection & Ranking.<br><small>This is a curated educational universe, not a market-wide list of the 25 best funds.</small></div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="pill"><span class="eyebrow">THE MOUNTAIN PATH ACADEMY</span><br>Mutual Fund Performance Explorer</div>',unsafe_allow_html=True)
    st.markdown("### Analysis controls")
    selected_categories=st.multiselect("Fund categories",CATEGORIES,default=["Large Cap"])
    available=[n for n,v in FUND_UNIVERSE.items() if v["category"] in selected_categories]
    with st.expander("Choose funds", expanded=False):
        chosen=st.multiselect("Fund universe",available,default=available)
    st.caption(f"{len(chosen)} funds selected · Direct–Growth universe")
    horizon=st.selectbox("Analysis horizon",["1 Year","3 Years","5 Years","YTD","Since Available"],index=1)
    primary=st.selectbox("Detailed fund",chosen or list(TARGETS))
    st.markdown(f'<div class="pill">Selected: {primary}</div>',unsafe_allow_html=True)
    investment=st.number_input("Lump-sum investment (₹)",10000,10000000,100000,10000)
    sip=st.number_input("Monthly SIP (₹)",500,1000000,10000,500)
    if st.button("↻ Refresh NAV data",use_container_width=True):
        nav_history.clear(); catalogue.clear(); st.rerun()
    st.markdown("---\n**Prof. V. Ravichandran**  \nFounder, The Mountain Path Academy  \n[Academy](https://themountainpathacademy.com/) · [LinkedIn](https://www.linkedin.com/in/trichyravis/) · [GitHub](https://github.com/trichyravis)")

if not chosen: st.warning("Select at least one fund from the sidebar."); st.stop()
with st.spinner("Retrieving NAV histories; repeated requests use the six-hour cache…"):
    nav,failed=load_all(chosen)
if nav.empty:
    st.error("Live NAV data could not be loaded. Please use Refresh after checking internet access."); st.stop()
if failed: st.warning("Unavailable funds skipped: "+", ".join(failed))
short_history=[n for n in nav if history_years(nav[n])<MIN_HISTORY_YEARS]
if short_history:
    st.warning("Excluded for having less than five years of available NAV history: "+", ".join(short_history))
    nav=nav.drop(columns=short_history)
if nav.empty:
    st.error("None of the selected funds currently meets the minimum five-year NAV-history rule."); st.stop()

latest_dates=nav.apply(lambda x:x.dropna().index.max())
st.caption(f"NAV observation dates: {latest_dates.min():%d %b %Y} – {latest_dates.max():%d %b %Y} · Source: MFAPI · NAV cache: up to 6 hours")
with st.expander("Data coverage and freshness"):
    coverage=pd.DataFrame({"Category":[FUND_UNIVERSE[n]["category"] for n in nav],"First observation":[nav[n].dropna().index.min().date() for n in nav],"Latest NAV date":[latest_dates[n].date() for n in nav],"Observations":[nav[n].count() for n in nav]},index=nav.columns)
    st.dataframe(coverage,use_container_width=True)
    st.caption("NAV dates describe the data, not today's page date. Missing observations are not forward-filled. Exact plan identity should be verified against the source before investment use.")
pnav=sliced(nav,horizon)
period_unavailable=[n for n in pnav if pnav[n].dropna().shape[0]<2]
if period_unavailable:
    st.warning(f"No usable {horizon} observations; excluded from this horizon: "+", ".join(period_unavailable))
    pnav=pnav.drop(columns=period_unavailable)
if pnav.empty:
    st.error(f"No selected fund has sufficient observations for the {horizon} analysis."); st.stop()
m=metrics(pnav).sort_values("CAGR",ascending=False); primary=primary if primary in nav else nav.columns[0]
best=m.index[0]; rank=int(m.index.get_loc(primary)+1) if primary in m.index else 0
c1,c2,c3,c4,c5=st.columns(5)
with c1:kpi("Period leader",best)
with c2:kpi("Leader CAGR",fmt_pct(m.iloc[0]["CAGR"]))
with c3:kpi("Lowest volatility",m["Volatility"].idxmin())
with c4:kpi("Best Sharpe*",m["Sharpe*"].idxmax())
with c5:kpi(f"{primary} rank",f"#{rank} of {len(m)}")

tabs=st.tabs(["Executive Dashboard","Returns","Risk Analytics","Rolling Returns","SIP & Lump Sum","Correlation","Fund Detail","Selection & Ranking","Methodology","How to Navigate"])

with tabs[0]:
    st.subheader(f"Performance snapshot · {horizon}")
    norm=pnav.div(pnav.apply(lambda s:s.dropna().iloc[0] if not s.dropna().empty else np.nan))*100
    st.plotly_chart(chart(px.line(norm,title="Growth of ₹100 (NAV-normalised)",labels={"value":"Indexed wealth","date":"Date"})),use_container_width=True)
    a,b=st.columns(2)
    with a: st.plotly_chart(chart(px.bar(m.reset_index(),x="Fund",y="CAGR",color="CAGR",color_continuous_scale=["#A7C7E7",GOLD,NAVY2],title="CAGR ranking")),use_container_width=True)
    with b: st.plotly_chart(chart(px.scatter(m.reset_index(),x="Volatility",y="CAGR",size=m["Sharpe*"].abs().fillna(0)+.1,color="Sharpe*",hover_name="Fund",title="Risk–return map",color_continuous_scale="Blues")),use_container_width=True)
    st.caption("*Sharpe and Sortino are educational excess-return proxies using a 0% risk-free rate.")

with tabs[1]:
    st.subheader("Trailing and calendar-year returns")
    horizons={"1Y":1,"3Y":3,"5Y":5}
    tr={}
    for n in nav:
        fund_nav=nav[n].dropna()
        tr[n]={k:cagr(fund_nav.loc[fund_nav.index>=fund_nav.index.max()-pd.DateOffset(years=y)]) for k,y in horizons.items()}
    trailing=pd.DataFrame(tr).T
    st.dataframe(trailing.style.format("{:.2%}"),use_container_width=True)
    yr=nav.resample("YE").last().pct_change(); yr.index=yr.index.year
    st.plotly_chart(chart(px.bar(yr.reset_index().melt("date"),x="date",y="value",color="variable",barmode="group",title="Calendar-year NAV returns",labels={"date":"Year","value":"Return","variable":"Fund"}),520),use_container_width=True)

with tabs[2]:
    st.subheader("Risk, downside and drawdown diagnostics")
    st.dataframe(m.style.format({c:"{:.2%}" for c in ["CAGR","Annual Return","Volatility","Downside Risk","Max Drawdown","Rolling Consistency","Daily VaR 95%","Daily CVaR 95%"]}).format({"Sharpe*":"{:.2f}","Sortino*":"{:.2f}"}),use_container_width=True)
    dd=pnav.div(pnav.cummax())-1
    st.plotly_chart(chart(px.line(dd,title="Drawdown from prior NAV peak",labels={"value":"Drawdown","date":"Date"}),500),use_container_width=True)

with tabs[3]:
    st.subheader("Rolling 1-year return consistency")
    roll=(nav/nav.shift(252)-1).dropna(how="all")
    st.plotly_chart(chart(px.line(roll,title="Rolling 252-trading-day return",labels={"value":"Rolling return","date":"Date"}),500),use_container_width=True)
    summary=pd.DataFrame({"Average":roll.mean(),"Minimum":roll.min(),"Maximum":roll.max(),"Positive periods":(roll>0).mean()})
    st.dataframe(summary.style.format("{:.2%}"),use_container_width=True)

with tabs[4]:
    st.subheader("Investment outcome simulator")
    wealth=pnav.div(pnav.apply(lambda s:s.dropna().iloc[0]))*investment
    lumpsum=wealth.iloc[-1].sort_values(ascending=False)
    monthly=nav.resample("ME").last().pct_change().fillna(0)
    sip_values={}
    for n in monthly:
        v=0
        for r in monthly[n].dropna(): v=(v+sip)*(1+r)
        sip_values[n]=v
    sim=pd.DataFrame({"Lump-sum final value":lumpsum,"Total SIP invested":sip*len(monthly),"SIP final value":pd.Series(sip_values)}).dropna()
    st.dataframe(sim.style.format("₹{:,.0f}"),use_container_width=True)
    st.plotly_chart(chart(px.bar(sim.reset_index(),x="index",y=["Lump-sum final value","SIP final value"],barmode="group",title="Simulated final values",labels={"index":"Fund","value":"₹"}),500),use_container_width=True)

with tabs[5]:
    st.subheader("Diversification and correlation")
    corr=pnav.pct_change(fill_method=None).corr()
    st.plotly_chart(chart(px.imshow(corr,text_auto=".2f",color_continuous_scale="RdBu_r",zmin=-1,zmax=1,title="Daily return correlation matrix"),620),use_container_width=True)
    st.markdown('<div class="note">High correlation means funds may behave similarly. Holding many highly correlated funds does not necessarily create meaningful diversification.</div>',unsafe_allow_html=True)

with tabs[6]:
    st.subheader(primary)
    s=nav[primary].dropna(); r=s.pct_change().dropna(); pm=m.loc[primary] if primary in m.index else metrics(s.to_frame(primary)).iloc[0]
    q1,q2,q3,q4=st.columns(4)
    with q1:kpi("Latest NAV",f"₹{s.iloc[-1]:,.2f}")
    with q2:kpi("CAGR",fmt_pct(pm["CAGR"]))
    with q3:kpi("Volatility",fmt_pct(pm["Volatility"]))
    with q4:kpi("Max drawdown",fmt_pct(pm["Max Drawdown"]))
    st.plotly_chart(chart(px.line(s,title=f"{primary} NAV history",labels={"value":"NAV","date":"Date"}),470),use_container_width=True)
    st.plotly_chart(chart(px.histogram(r,nbins=60,title="Daily-return distribution",marginal="box",color_discrete_sequence=[BLUE]),400),use_container_width=True)

with tabs[7]:
    st.subheader("Five-year category-relative selection and ranking")
    selection=selection_score(nav)
    selection["Category Rank"]=selection.groupby("Category")["Composite / 100"].rank(method="min",ascending=False).astype(int)
    eligible=selection[selection["Eligible"]].sort_values(["Category","Category Rank"])
    show_cols=["Category","Category Rank","History (years)","CAGR","Sharpe*","Rolling Consistency","Downside Risk","Max Drawdown","Composite / 100"]
    st.dataframe(
        eligible[show_cols].style.format({
            "History (years)":"{:.1f}","CAGR":"{:.2%}","Sharpe*":"{:.2f}",
            "Rolling Consistency":"{:.2%}","Downside Risk":"{:.2%}",
            "Max Drawdown":"{:.2%}","Composite / 100":"{:.1f}"
        }),use_container_width=True
    )
    category_choice=st.selectbox("Scorecard chart category",["All Categories"]+CATEGORIES)
    plotted=eligible if category_choice=="All Categories" else eligible[eligible["Category"]==category_choice]
    st.plotly_chart(chart(px.bar(plotted.reset_index(),x="Fund",y="Composite / 100",color="Category",title="Transparent multi-factor scorecard"),540),use_container_width=True)
    export=m.join(selection.drop(columns=["CAGR","Annual Return","Volatility","Sharpe*","Sortino*","Downside Risk","Max Drawdown","Rolling Consistency","Daily VaR 95%","Daily CVaR 95%"],errors="ignore")).reset_index()
    csv=export.to_csv(index=False).encode()
    bio=io.BytesIO()
    with pd.ExcelWriter(bio,engine="openpyxl") as w:
        export.to_excel(w,index=False,sheet_name="Ranking"); nav.to_excel(w,sheet_name="NAV History"); pnav.pct_change(fill_method=None).to_excel(w,sheet_name="Daily Returns")
        pd.DataFrame([
            ["Minimum NAV history","5 years","Eligibility filter"],
            ["Plan type","Direct–Growth","Eligibility filter"],
            ["Category representation","5 funds × 5 categories","Universe construction"],
            ["Five-year CAGR","20%","Higher is better"],
            ["Sharpe ratio","20%","Higher is better; 0% risk-free proxy"],
            ["Rolling-return consistency","20%","Share of positive 3-year rolling annualised returns"],
            ["Downside risk","15%","Lower is better"],
            ["Maximum drawdown","15%","Closer to zero is better"],
            ["Category-wise AUM","10%","Neutral pending a verified scheme-AUM source"],
        ],columns=["Criterion","Rule / Weight","Treatment"]).to_excel(w,index=False,sheet_name="Methodology")
    d1,d2=st.columns(2)
    d1.download_button("⬇ Download ranking CSV",csv,"top_25_mutual_fund_ranking.csv","text/csv",use_container_width=True)
    d2.download_button("⬇ Download complete Excel",bio.getvalue(),"top_25_mutual_fund_analytics.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    st.caption("Funds are scored within their own category. The composite score is an educational model—not a recommendation or official rating.")

with tabs[8]:
    st.subheader("Selection methodology and interpretation")
    with st.expander("Learn the calculation · CAGR, volatility and drawdown", expanded=True):
        study=pnav[primary].dropna()
        years=(study.index[-1]-study.index[0]).days/365.25
        st.markdown(f"**Worked example: {primary} · {horizon}**")
        st.latex(r"CAGR=\left(\frac{NAV_{end}}{NAV_{start}}\right)^{1/T}-1")
        st.write(f"Start NAV ₹{study.iloc[0]:,.2f}; end NAV ₹{study.iloc[-1]:,.2f}; elapsed time {years:.3f} years → CAGR {cagr(study):.2%}.")
        st.code("=(End_NAV/Start_NAV)^(365.25/(End_Date-Start_Date))-1",language=None)
        st.markdown("**Annualised volatility:** sample standard deviation of daily returns × √252. Excel: `=STDEV.S(Daily_Returns)*SQRT(252)`. This assumes 252 trading observations per year.")
        st.markdown("**Drawdown:** NAV ÷ highest prior NAV − 1. Maximum drawdown is the most negative observation; it measures the worst historical decline from a prior peak.")
        st.markdown("**Sharpe (0% proxy):** annualised arithmetic return ÷ annualised volatility, using a 0% risk-free proxy. A proper excess-return comparison requires a matched risk-free series.")
        st.caption("CAGR is a geometric growth rate; the arithmetic annual return used in Sharpe is a different measure. Both are based on historical NAVs.")
    st.markdown("""
### Universe construction

- **25 diversified-equity schemes:** five each from Large Cap, Flexi Cap, Large & Mid Cap, Mid Cap and Small Cap.
- **Plan rule:** Direct–Growth variants only, avoiding mixing Regular plans or payout options.
- **History rule:** at least five years of NAV history available from the public data feed.
- **Category rule:** funds are ranked against peers in the same category; a small-cap return is not treated as directly comparable with a large-cap return.

### Composite score

| Quantitative criterion | Weight | Scoring direction |
|---|---:|---|
| Five-year CAGR | 20% | Higher is better |
| Sharpe ratio | 20% | Higher is better |
| Positive three-year rolling-return consistency | 20% | Higher is better |
| Annualised downside risk | 15% | Lower is better |
| Maximum drawdown | 15% | A smaller loss is better |
| Category-wise AUM | 10% | Neutral until verified scheme AUM is supplied |

Each measured factor is converted to a **within-category percentile score**. This avoids allowing the naturally higher risk and return of small-cap funds to dominate lower-risk categories.

### Important AUM disclosure

The live MFAPI/AMFI-linked NAV endpoint used by this project does not provide scheme-level AUM. The model therefore assigns every fund the same neutral 5/10 AUM contribution instead of displaying or scoring an unverified number. Once a dated AMC/AMFI AUM file is added, the app can calculate the AUM percentile automatically without changing the other weights.
""")
    st.info("The displayed 25-fund universe is a balanced educational comparison set. It is not a claim that these are permanently the 25 best funds in India.")

with tabs[9]:
    st.subheader("How to navigate this app")
    st.markdown("""
1. Select the fund universe in the sidebar and choose a ranking horizon.
2. Select one fund for detailed diagnosis; the gold confirmation pill shows the active choice.
3. Start with **Executive Dashboard** for the ranking, indexed wealth and risk–return position.
4. Use **Returns** to compare trailing CAGR and calendar-year performance.
5. Use **Risk Analytics** for volatility, Sharpe, Sortino, VaR, CVaR and drawdowns.
6. Use **Rolling Returns** to judge consistency instead of relying on one start/end date.
7. Enter lump-sum and SIP amounts to run the educational investment simulation.
8. Review **Correlation** before assuming that several funds provide diversification.
9. Review **Selection & Ranking** for the category-relative composite score and downloads.
10. Read **Methodology** for eligibility rules, factor weights and the AUM data limitation.

**Interpretation caution:** Past NAV performance does not assure future returns. Compare funds within suitable categories, review expense ratios, exit loads, taxes, portfolio concentration and investment objectives before taking a decision.
""")
    st.info("Data source: public NAV history supplied through MFAPI/AMFI-linked records. NAV is not adjusted here for investor-specific tax, load or expense differences beyond what is reflected in the published plan NAV.")

st.markdown("""<div class="footer"><b>The Mountain Path Academy</b><br>Developed by Prof. V. Ravichandran · Visiting Professor & Professor of Practice at leading business schools<br><a href="https://themountainpathacademy.com/">Academy</a> · <a href="https://www.linkedin.com/in/trichyravis/">LinkedIn</a> · <a href="https://github.com/trichyravis">GitHub</a><br><small>Educational analytics project · Not investment advice · © 2026 The Mountain Path Academy</small></div>""",unsafe_allow_html=True)


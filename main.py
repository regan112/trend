import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="🌡️ 기온 쇼핑 날씨",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════
# 귀여운 파스텔 스타일
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.hero {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 30%, #a1c4fd 70%, #c2e9fb 100%);
    border-radius: 24px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.hero h1 { font-size: 2.6rem; font-weight: 900; color: #2d3436; margin: 0; }
.hero p  { font-size: 1rem; color: #636e72; margin-top: 0.4rem; }

.cute-card {
    background: white;
    border-radius: 20px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.07);
    margin-bottom: 1rem;
    border-top: 4px solid;
}
.rank-card {
    background: linear-gradient(135deg, #fff9f0, #fff);
    border-radius: 16px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.rank-num { font-size: 1.5rem; font-weight: 900; min-width: 2rem; }
.rank-bar-bg {
    background: #f1f3f5;
    border-radius: 10px;
    height: 12px;
    flex: 1;
    overflow: hidden;
}
.rank-bar-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.8s ease;
}

.tip-box {
    background: linear-gradient(135deg, #e0f7fa, #f3e5f5);
    border-radius: 16px;
    padding: 1rem 1.3rem;
    font-size: 0.95rem;
    color: #37474f;
    margin: 0.8rem 0;
}
.corr-badge {
    display: inline-block;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    color: white;
}

[data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
.stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════
@st.cache_data
def load_data():
    df = pd.read_csv("temperature_data.csv")
    df.columns = df.columns.str.strip()
    df["날짜"] = df["날짜"].str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["연도"] = df["날짜"].dt.year
    df["월"]  = df["날짜"].dt.month
    df["계절"] = df["월"].map(lambda m:
        "봄🌸" if m in [3,4,5] else
        "여름☀️" if m in [6,7,8] else
        "가을🍁" if m in [9,10,11] else "겨울❄️"
    )
    df["기온구간"] = pd.cut(
        df["평균기온(℃)"],
        bins=[-30, 0, 5, 10, 15, 20, 25, 30, 45],
        labels=["0°이하","0~5°","5~10°","10~15°","15~20°","20~25°","25~30°","30°이상"]
    )
    return df

df = load_data()

# ══════════════════════════════════════════════
# 품목 정의
# ══════════════════════════════════════════════
FOODS = {
    "아이스크림 🍦": dict(color="#FF6B6B", formula=lambda t: max(0, (t-15)*6  + np.random.normal(0,3)), desc="15°C↑ 부터 불티나게 팔려요!", category="음식"),
    "핫초코 ☕":    dict(color="#8B5E3C", formula=lambda t: max(0, (10-t)*5+20 + np.random.normal(0,3)), desc="10°C↓ 달달한 핫초코가 생각나죠", category="음식"),
    "맥주 🍺":     dict(color="#FFC300", formula=lambda t: max(0, (t-18)*7+10  + np.random.normal(0,4)), desc="더울수록 맥주 한 캔이 최고!", category="음식"),
    "냉면 🍜":     dict(color="#45B7D1", formula=lambda t: max(0, (t-20)*8     + np.random.normal(0,5)), desc="폭염엔 시원한 냉면으로!", category="음식"),
    "삼겹살 🥩":   dict(color="#FF8C69", formula=lambda t: max(0, 40+abs(t-10)*(-0.5)+np.random.normal(0,6)), desc="봄·가을 나들이 삼겹살!", category="음식"),
    "핫도그 🌭":   dict(color="#FFB347", formula=lambda t: max(0, 35-abs(t-15)*0.8+np.random.normal(0,4)), desc="선선한 날씨에 딱인 간식!", category="음식"),
    "패딩 🧥":     dict(color="#A29BFE", formula=lambda t: max(0, (5-t)*8+10   + np.random.normal(0,5)), desc="5°C↓ 두꺼운 패딩이 필요해요", category="물건"),
    "우산 ☔":     dict(color="#74B9FF", formula=lambda t: max(0, 30+(t-10)*1.5 + np.random.normal(0,8)), desc="여름 장마철 우산 필수!", category="물건"),
}

FOOD_ITEMS  = [k for k,v in FOODS.items() if v["category"]=="음식"]
GOODS_ITEMS = [k for k,v in FOODS.items() if v["category"]=="물건"]
ALL_ITEMS   = list(FOODS.keys())

# ══════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎛️ 설정")
    year_range = st.slider("📅 분석 기간", int(df["연도"].min()), int(df["연도"].max()), (2000, 2026))
    selected = st.multiselect("🛒 품목 선택", ALL_ITEMS, default=["아이스크림 🍦","핫초코 ☕","맥주 🍺","패딩 🧥"])
    show_trend = st.checkbox("📈 기온 추세선 표시", True)
    st.markdown("---")
    st.markdown("**📊 데이터 출처**")
    st.caption("기상청 서울 관측소 (지점 108)\n1907 ~ 2026년 · 총 42,912일")
    st.markdown("---")
    st.caption("💡 소비 지수는 기온 기반 모델 추정값입니다")

# ══════════════════════════════════════════════
# 데이터 필터 & 소비지수 계산
# ══════════════════════════════════════════════
df_f = df[(df["연도"]>=year_range[0]) & (df["연도"]<=year_range[1])].copy()
np.random.seed(42)
for name, info in FOODS.items():
    df_f[name] = df_f["평균기온(℃)"].apply(info["formula"]).clip(0,100).round(1)

# ══════════════════════════════════════════════
# 히어로 헤더
# ══════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <h1>🌡️ 날씨가 바꾸는 쇼핑 트렌드</h1>
  <p>서울 기상 관측 데이터(1907~2026) · 기온에 따라 어떤 음식과 물건이 잘 팔릴까요? 🛍️</p>
</div>
""", unsafe_allow_html=True)

# ── 오늘의 요약 지표 ───────────────────────────────────────
avg_temp = df_f["평균기온(℃)"].mean()
max_temp = df_f["최고기온(℃)"].max()
min_temp = df_f["최저기온(℃)"].min()
total_days = len(df_f)

c1,c2,c3,c4 = st.columns(4)
c1.metric("🌡️ 기간 평균 기온", f"{avg_temp:.1f}°C")
c2.metric("🔥 최고 기온",      f"{max_temp:.1f}°C")
c3.metric("🧊 최저 기온",      f"{min_temp:.1f}°C")
c4.metric("📅 분석 일수",      f"{total_days:,}일")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 탭
# ══════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🍱 음식 연도별 랭킹",
    "🏆 전체 합산 랭킹",
    "📊 기온 vs 소비",
    "📅 월별 패턴",
    "📈 기온 100년 트렌드",
])

# ══════════════════════════════════════════════
# TAB 1 : 음식 연도별 랭킹
# ══════════════════════════════════════════════
with tab1:
    st.markdown("### 🍱 연도별 음식 인기 순위")
    st.markdown(
        '<div class="tip-box">📌 기온 모델을 기반으로 <b>연도별 음식 소비 지수 합계</b>를 계산해 순위를 매겼어요. '
        '연도를 바꿔가며 그 해 날씨에 가장 잘 팔렸을 음식을 확인해보세요! 🎉</div>',
        unsafe_allow_html=True
    )

    years = sorted(df_f["연도"].unique(), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", years, key="food_year")

    df_yr = df_f[df_f["연도"] == sel_year]
    food_scores = {f: df_yr[f].sum() for f in FOOD_ITEMS}
    food_sorted = sorted(food_scores.items(), key=lambda x: x[1], reverse=True)
    max_score = food_sorted[0][1] if food_sorted else 1

    avg_yr_temp = df_yr["평균기온(℃)"].mean()
    st.markdown(f"**{sel_year}년 평균 기온**: {avg_yr_temp:.1f}°C &nbsp;|&nbsp; **{sel_year}년 가장 핫한 음식 👑 {food_sorted[0][0]}**")

    rank_colors = ["#FFD700","#C0C0C0","#CD7F32","#A29BFE","#74B9FF","#FF6B6B"]
    rank_medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣"]

    for i, (name, score) in enumerate(food_sorted):
        pct = score / max_score * 100
        color = rank_colors[i] if i < len(rank_colors) else "#dfe6e9"
        medal = rank_medals[i] if i < len(rank_medals) else f"{i+1}"
        desc  = FOODS[name]["desc"]
        st.markdown(f"""
        <div class="rank-card">
            <div class="rank-num">{medal}</div>
            <div style="flex:1">
                <div style="font-weight:700; font-size:1.05rem; margin-bottom:4px">{name} &nbsp;<span style="font-size:0.8rem;color:#636e72">{desc}</span></div>
                <div class="rank-bar-bg">
                    <div class="rank-bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
                </div>
            </div>
            <div style="font-weight:800;font-size:1rem;color:{color};min-width:60px;text-align:right">{score:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # 연도별 전체 음식 순위 변화 (라인차트)
    st.markdown("#### 📉 연도별 음식 순위 변화")
    st.caption("소비 지수 합계 기준 · 위로 올라갈수록 더 많이 팔린 음식이에요")

    yr_food_df = df_f.groupby("연도")[FOOD_ITEMS].sum().reset_index()
    fig_rank = go.Figure()
    for food in FOOD_ITEMS:
        fig_rank.add_trace(go.Scatter(
            x=yr_food_df["연도"], y=yr_food_df[food],
            name=food, mode="lines",
            line=dict(color=FOODS[food]["color"], width=2),
        ))
    fig_rank.update_layout(
        height=360, hovermode="x unified",
        plot_bgcolor="#fafafa",
        margin=dict(l=10,r=10,t=20,b=10),
        legend=dict(orientation="h", y=-0.25, font_size=11),
        xaxis_title="연도", yaxis_title="소비 지수 합계",
    )
    st.plotly_chart(fig_rank, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2 : 전체 합산 랭킹
# ══════════════════════════════════════════════
with tab2:
    st.markdown("### 🏆 연도별 전체 품목 합산 랭킹")
    st.markdown(
        '<div class="tip-box">🛍️ <b>음식 + 물건</b> 전체 소비 지수의 연도별 합계 순위예요. '
        '특별히 더웠거나 추웠던 해에 어떤 품목이 가장 많이 팔렸는지 확인해보세요!</div>',
        unsafe_allow_html=True
    )

    sel_year2 = st.selectbox("📅 연도 선택", years, key="all_year")
    df_yr2 = df_f[df_f["연도"] == sel_year2]

    all_scores = {name: df_yr2[name].sum() for name in ALL_ITEMS}
    all_sorted = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
    max_all = all_sorted[0][1] if all_sorted else 1

    avg_yr2 = df_yr2["평균기온(℃)"].mean()
    st.markdown(f"**{sel_year2}년 평균 기온**: {avg_yr2:.1f}°C &nbsp;|&nbsp; **{sel_year2}년 1위 👑 {all_sorted[0][0]}**")

    # 음식 / 물건 구분해서 표시
    col_f, col_g = st.columns(2)
    with col_f:
        st.markdown("##### 🍽️ 음식 순위")
        food_part = [(n,s) for n,s in all_sorted if FOODS[n]["category"]=="음식"]
        for i,(name,score) in enumerate(food_part):
            pct = score/max_all*100
            color = rank_colors[i] if i<len(rank_colors) else "#dfe6e9"
            medal = rank_medals[i] if i<len(rank_medals) else f"{i+1}"
            st.markdown(f"""
            <div class="rank-card">
                <span class="rank-num">{medal}</span>
                <div style="flex:1">
                    <div style="font-weight:700">{name}</div>
                    <div class="rank-bar-bg">
                        <div class="rank-bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
                    </div>
                </div>
                <span style="font-weight:800;color:{color}">{score:,.0f}</span>
            </div>""", unsafe_allow_html=True)

    with col_g:
        st.markdown("##### 🛒 물건 순위")
        goods_part = [(n,s) for n,s in all_sorted if FOODS[n]["category"]=="물건"]
        for i,(name,score) in enumerate(goods_part):
            pct = score/max_all*100
            color = rank_colors[i] if i<len(rank_colors) else "#dfe6e9"
            medal = rank_medals[i] if i<len(rank_medals) else f"{i+1}"
            st.markdown(f"""
            <div class="rank-card">
                <span class="rank-num">{medal}</span>
                <div style="flex:1">
                    <div style="font-weight:700">{name}</div>
                    <div class="rank-bar-bg">
                        <div class="rank-bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
                    </div>
                </div>
                <span style="font-weight:800;color:{color}">{score:,.0f}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("#### 📊 연도별 전체 소비 합계 추이")
    yr_all_df = df_f.groupby("연도")[ALL_ITEMS].sum()
    yr_all_df["합계"] = yr_all_df.sum(axis=1)
    yr_all_df = yr_all_df.reset_index()

    fig_total = px.bar(
        yr_all_df, x="연도", y=ALL_ITEMS,
        color_discrete_map={n: FOODS[n]["color"] for n in ALL_ITEMS},
        labels={"value":"소비 지수 합계","variable":"품목"},
        height=360,
    )
    fig_total.update_layout(
        barmode="stack",
        plot_bgcolor="#fafafa",
        margin=dict(l=10,r=10,t=10,b=10),
        legend=dict(orientation="h", y=-0.3, font_size=10),
        hovermode="x unified",
    )
    st.plotly_chart(fig_total, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 3 : 기온 vs 소비 (산점도)
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### 📊 기온이 오르면 뭐가 팔릴까요?")
    st.markdown(
        '<div class="tip-box">🔍 각 점은 하루치 데이터예요. 색깔은 계절을 나타내고, '
        '굵은 선은 기온에 따른 소비 추세를 보여줘요!</div>',
        unsafe_allow_html=True
    )

    if not selected:
        st.warning("👈 왼쪽에서 품목을 선택해주세요!")
    else:
        sample = df_f.sample(min(4000, len(df_f)), random_state=42)
        cols2 = st.columns(min(len(selected), 2))
        for idx, prod in enumerate(selected):
            with cols2[idx % 2]:
                color = FOODS[prod]["color"]
                corr  = df_f[["평균기온(℃)", prod]].corr().iloc[0,1]

                if corr > 0.6:   cl, ct = "#FF6B6B", "🔴 강한 양의 상관"
                elif corr > 0.3: cl, ct = "#FF9F43", "🟠 중간 양의 상관"
                elif corr <-0.6: cl, ct = "#74B9FF", "🔵 강한 음의 상관"
                elif corr <-0.3: cl, ct = "#A29BFE", "🟣 중간 음의 상관"
                else:            cl, ct = "#b2bec3", "⬜ 약한 상관"

                fig_sc = px.scatter(
                    sample, x="평균기온(℃)", y=prod,
                    color="계절",
                    color_discrete_map={"봄🌸":"#00b894","여름☀️":"#e17055","가을🍁":"#fdcb6e","겨울❄️":"#74B9FF"},
                    opacity=0.3,
                    trendline="lowess", trendline_scope="overall",
                    trendline_color_override=color,
                    labels={"평균기온(℃)":"기온 (°C)", prod:"소비 지수"},
                    height=300,
                )
                fig_sc.update_traces(marker=dict(size=3))
                fig_sc.update_layout(
                    title=dict(text=prod, font_size=15, x=0.02),
                    margin=dict(l=10,r=10,t=40,b=10),
                    legend=dict(orientation="h",y=-0.25,font_size=10),
                    plot_bgcolor="#fafafa",
                )
                st.plotly_chart(fig_sc, use_container_width=True)
                st.markdown(
                    f'<span class="corr-badge" style="background:{cl}">r = {corr:.2f} &nbsp; {ct}</span>'
                    f'&nbsp; <small style="color:#636e72">{FOODS[prod]["desc"]}</small>',
                    unsafe_allow_html=True
                )
                st.markdown("")


# ══════════════════════════════════════════════
# TAB 4 : 월별 패턴
# ══════════════════════════════════════════════
with tab4:
    st.markdown("### 📅 월별로 보는 기온 & 소비 패턴")
    st.markdown(
        '<div class="tip-box">📆 1월~12월 각 달의 평균 기온(막대)과 품목별 소비 지수(선)를 한눈에 비교해요!</div>',
        unsafe_allow_html=True
    )

    if not selected:
        st.warning("👈 왼쪽에서 품목을 선택해주세요!")
    else:
        monthly = df_f.groupby("월")[["평균기온(℃)"]+selected].mean().reset_index()
        monthly["월명"] = monthly["월"].map({1:"1월",2:"2월",3:"3월",4:"4월",5:"5월",6:"6월",
                                             7:"7월",8:"8월",9:"9월",10:"10월",11:"11월",12:"12월"})

        fig_m = make_subplots(specs=[[{"secondary_y":True}]])
        fig_m.add_trace(go.Bar(
            x=monthly["월명"], y=monthly["평균기온(℃)"],
            name="🌡️ 평균기온",
            marker_color=["#74B9FF" if t<5 else "#55efc4" if t<15 else "#fdcb6e" if t<25 else "#e17055"
                          for t in monthly["평균기온(℃)"]],
            opacity=0.65,
        ), secondary_y=False)
        for prod in selected:
            fig_m.add_trace(go.Scatter(
                x=monthly["월명"], y=monthly[prod], name=prod,
                mode="lines+markers",
                line=dict(color=FOODS[prod]["color"], width=2.5),
                marker=dict(size=8, line=dict(color="white",width=1.5)),
            ), secondary_y=True)
        fig_m.update_layout(
            height=400, hovermode="x unified", plot_bgcolor="#fafafa",
            margin=dict(l=10,r=10,t=10,b=10),
            legend=dict(orientation="h",y=-0.25,font_size=11),
        )
        fig_m.update_yaxes(title_text="평균기온 (°C)", secondary_y=False)
        fig_m.update_yaxes(title_text="소비 지수", secondary_y=True)
        st.plotly_chart(fig_m, use_container_width=True)

        # 계절 히트맵
        st.markdown("#### 🌈 계절별 소비 히트맵")
        seasonal = df_f.groupby("계절")[selected].mean().round(1)
        season_order = ["봄🌸","여름☀️","가을🍁","겨울❄️"]
        seasonal = seasonal.reindex([s for s in season_order if s in seasonal.index])
        fig_h = px.imshow(
            seasonal.T,
            color_continuous_scale=["#cce5ff","#fff3cd","#ffd6a5","#ff6b6b"],
            aspect="auto",
            labels=dict(x="계절", y="품목", color="소비 지수"),
            height=260,
            text_auto=".1f",
        )
        fig_h.update_layout(margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_h, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 5 : 기온 장기 트렌드
# ══════════════════════════════════════════════
with tab5:
    st.markdown("### 📈 서울 기온 100년의 변화")
    st.markdown(
        '<div class="tip-box">🌍 1907년부터 현재까지 서울의 기온이 어떻게 변해왔는지 살펴봐요. '
        '기후 변화가 소비 패턴에도 큰 영향을 준답니다!</div>',
        unsafe_allow_html=True
    )

    yearly = df[df["연도"]>=1920].groupby("연도")["평균기온(℃)"].mean().reset_index()
    yearly.columns = ["연도","연평균기온"]

    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=yearly["연도"], y=yearly["연평균기온"],
        mode="lines", name="연평균기온",
        line=dict(color="#dfe6e9", width=1), opacity=0.8,
        fill="tozeroy", fillcolor="rgba(116,185,255,0.08)"
    ))

    if show_trend:
        yearly["MA10"] = yearly["연평균기온"].rolling(10, center=True).mean()
        fig_t.add_trace(go.Scatter(
            x=yearly["연도"], y=yearly["MA10"],
            mode="lines", name="10년 이동평균",
            line=dict(color="#e17055", width=3)
        ))
        mask = yearly["연평균기온"].notna()
        xv, yv = yearly.loc[mask,"연도"].values, yearly.loc[mask,"연평균기온"].values
        coef = np.polyfit(xv, yv, 1)
        fig_t.add_trace(go.Scatter(
            x=xv, y=np.polyval(coef, xv), mode="lines",
            name=f"추세 (+{coef[0]*100:.2f}°C/100년)",
            line=dict(color="#6c5ce7", width=2, dash="dash")
        ))

    fig_t.update_layout(
        height=400, plot_bgcolor="#fafafa", hovermode="x unified",
        margin=dict(l=10,r=10,t=10,b=10),
        legend=dict(orientation="h",y=-0.2),
        xaxis_title="연도", yaxis_title="연평균기온 (°C)",
    )
    st.plotly_chart(fig_t, use_container_width=True)

    # 시대별 기온 비교 카드
    st.markdown("#### 🕰️ 시대별 평균 기온")
    periods = [("1920~1950s",1920,1959),("1960~1990s",1960,1999),("2000년~현재",2000,2026)]
    pc = st.columns(3)
    avgs = []
    for i,(label,y1,y2) in enumerate(periods):
        avg = yearly[(yearly["연도"]>=y1)&(yearly["연도"]<=y2)]["연평균기온"].mean()
        avgs.append(avg)
        with pc[i]:
            delta = f"+{avg-avgs[0]:.1f}°C" if i>0 else None
            st.metric(label, f"{avg:.2f}°C", delta=delta)

    delta_total = avgs[-1] - avgs[0]
    st.markdown(f"""
    <div class="tip-box">
    🌡️ <b>1920~50년대 대비 2000년 이후 서울 연평균 기온이 +{delta_total:.1f}°C 올랐어요!</b><br>
    더워진 날씨 덕분에 🍦 아이스크림·🍺 맥주·🍜 냉면 시즌이 길어지고,
    🧥 패딩·☕ 핫초코 수요는 조금씩 줄어드는 추세랍니다.
    </div>
    """, unsafe_allow_html=True)

# ── 푸터 ─────────────────────────────────────
st.markdown("---")
st.caption("📡 데이터: 기상청 서울 관측소 (지점 108) · 소비 지수는 기온 기반 모델 추정값입니다 · Made with ❤️ & Streamlit")

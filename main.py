import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="기온 & 소비 트렌드 분석",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 스타일 ──────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f97316, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle { color: #64748b; font-size: 1rem; margin-bottom: 1.5rem; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid;
    }
    .season-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 ──────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("temperature_data.csv")
    df.columns = df.columns.str.strip()
    df["날짜"] = df["날짜"].str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    df["월일"] = df["날짜"].dt.strftime("%m-%d")
    df["계절"] = df["월"].map(lambda m:
        "봄🌸" if m in [3,4,5] else
        "여름☀️" if m in [6,7,8] else
        "가을🍁" if m in [9,10,11] else "겨울❄️"
    )
    df["기온구간"] = pd.cut(
        df["평균기온(℃)"],
        bins=[-30, 0, 5, 10, 15, 20, 25, 30, 45],
        labels=["0°이하", "0~5°", "5~10°", "10~15°", "15~20°", "20~25°", "25~30°", "30°이상"]
    )
    return df

df = load_data()

# ── 계절별 판매 지수 (가상 데이터 기반 공식) ──────────────────
PRODUCTS = {
    "아이스크림 🍦": dict(
        color="#f97316",
        formula=lambda t: max(0, (t - 15) * 6 + np.random.normal(0, 3)),
        desc="기온 15°C 이상부터 급증"
    ),
    "핫초코 ☕": dict(
        color="#92400e",
        formula=lambda t: max(0, (10 - t) * 5 + 20 + np.random.normal(0, 3)),
        desc="기온 10°C 이하에서 수요 폭발"
    ),
    "우산 ☔": dict(
        color="#3b82f6",
        formula=lambda t: max(0, 30 + (t - 10) * 1.5 + np.random.normal(0, 8)),
        desc="장마철(여름) 집중 수요"
    ),
    "패딩 🧥": dict(
        color="#6366f1",
        formula=lambda t: max(0, (5 - t) * 8 + 10 + np.random.normal(0, 5)),
        desc="5°C 이하에서 수요 급증"
    ),
    "맥주 🍺": dict(
        color="#eab308",
        formula=lambda t: max(0, (t - 18) * 7 + 10 + np.random.normal(0, 4)),
        desc="더운 날씨일수록 소비 증가"
    ),
    "삼겹살 🥩": dict(
        color="#ef4444",
        formula=lambda t: max(0, 40 + abs(t - 10) * (-0.5) + np.random.normal(0, 6)),
        desc="연중 꾸준, 봄·가을 소폭 증가"
    ),
    "냉면 🍜": dict(
        color="#06b6d4",
        formula=lambda t: max(0, (t - 20) * 8 + np.random.normal(0, 5)),
        desc="여름 고온에서 소비 집중"
    ),
    "핫도그 🌭": dict(
        color="#f59e0b",
        formula=lambda t: max(0, 35 - abs(t - 15) * 0.8 + np.random.normal(0, 4)),
        desc="봄·가을 날씨에 최고"
    ),
}

# ── 헤더 ──────────────────────────────────────────────────
st.markdown('<div class="main-title">🌡️ 기온이 바꾸는 소비 트렌드</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">서울 기상 관측 데이터(1907~2026) 기반 · 기온과 상품/음식 수요의 상관관계 분석</div>', unsafe_allow_html=True)

# ── 사이드바 ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 분석 설정")

    year_range = st.slider(
        "📅 분석 기간",
        min_value=int(df["연도"].min()),
        max_value=int(df["연도"].max()),
        value=(2000, 2026),
        step=1
    )

    selected_products = st.multiselect(
        "🛒 분석할 품목 선택",
        options=list(PRODUCTS.keys()),
        default=["아이스크림 🍦", "핫초코 ☕", "맥주 🍺", "패딩 🧥"]
    )

    show_trend = st.checkbox("📈 장기 기온 추세선 표시", value=True)

    st.markdown("---")
    st.markdown("#### 📊 데이터 정보")
    st.markdown(f"- **출처**: 기상청 서울 관측소")
    st.markdown(f"- **기간**: 1907 ~ 2026년")
    st.markdown(f"- **총 관측일**: {len(df):,}일")

# ── 데이터 필터링 ──────────────────────────────────────────
df_f = df[(df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])].copy()

# 판매지수 계산 (시드 고정으로 재현 가능)
np.random.seed(42)
for name, info in PRODUCTS.items():
    df_f[name] = df_f["평균기온(℃)"].apply(info["formula"]).clip(0, 100).round(1)

# ── 탭 ────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 기온 vs 소비 지수",
    "📅 월별·계절별 패턴",
    "🔥 기온 구간 분석",
    "📈 기온 장기 트렌드"
])

# ═══════════════════════════════════════════════
# TAB 1 : 기온 vs 소비 지수 산점도
# ═══════════════════════════════════════════════
with tab1:
    st.markdown("### 기온과 소비 지수의 상관관계")
    st.caption("각 점은 일별 데이터 · 추세선은 LOWESS 스무딩")

    if not selected_products:
        st.warning("왼쪽에서 품목을 선택해주세요.")
    else:
        # 샘플링 (너무 많으면 느림)
        sample = df_f.sample(min(5000, len(df_f)), random_state=42)

        cols = st.columns(min(len(selected_products), 2))
        for idx, prod in enumerate(selected_products):
            col = cols[idx % 2]
            with col:
                color = PRODUCTS[prod]["color"]
                desc = PRODUCTS[prod]["desc"]

                # 상관계수
                corr = df_f[["평균기온(℃)", prod]].corr().iloc[0, 1]
                corr_label = "🔴 강한 양의 상관" if corr > 0.6 else \
                             "🟠 중간 양의 상관" if corr > 0.3 else \
                             "🔵 강한 음의 상관" if corr < -0.6 else \
                             "🟦 중간 음의 상관" if corr < -0.3 else "⬜ 약한 상관"

                fig = px.scatter(
                    sample, x="평균기온(℃)", y=prod,
                    color="계절",
                    color_discrete_map={
                        "봄🌸": "#10b981", "여름☀️": "#f97316",
                        "가을🍁": "#f59e0b", "겨울❄️": "#3b82f6"
                    },
                    opacity=0.35,
                    trendline="lowess",
                    trendline_scope="overall",
                    trendline_color_override=color,
                    title=f"{prod}",
                    labels={"평균기온(℃)": "평균기온 (°C)", prod: "소비 지수 (0~100)"},
                    height=320
                )
                fig.update_traces(marker=dict(size=3))
                fig.update_layout(
                    margin=dict(l=10, r=10, t=40, b=10),
                    legend=dict(orientation="h", y=-0.2, font_size=10),
                    showlegend=True,
                    title_font_size=14,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"**상관계수 r = {corr:.3f}** &nbsp; {corr_label}")
                st.caption(desc)

# ═══════════════════════════════════════════════
# TAB 2 : 월별·계절별 패턴
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("### 월별 평균 기온 & 소비 지수")

    if not selected_products:
        st.warning("왼쪽에서 품목을 선택해주세요.")
    else:
        monthly = df_f.groupby("월")[["평균기온(℃)"] + selected_products].mean().reset_index()
        monthly["월명"] = monthly["월"].map({
            1:"1월",2:"2월",3:"3월",4:"4월",5:"5월",6:"6월",
            7:"7월",8:"8월",9:"9월",10:"10월",11:"11월",12:"12월"
        })

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # 기온 막대
        fig.add_trace(
            go.Bar(
                x=monthly["월명"], y=monthly["평균기온(℃)"],
                name="평균기온(°C)",
                marker_color=[
                    "#3b82f6" if t < 5 else "#10b981" if t < 15 else "#f97316" if t < 25 else "#ef4444"
                    for t in monthly["평균기온(℃)"]
                ],
                opacity=0.6,
                yaxis="y1"
            ),
            secondary_y=False,
        )

        # 품목별 라인
        for prod in selected_products:
            fig.add_trace(
                go.Scatter(
                    x=monthly["월명"], y=monthly[prod],
                    name=prod,
                    mode="lines+markers",
                    line=dict(color=PRODUCTS[prod]["color"], width=2.5),
                    marker=dict(size=7),
                ),
                secondary_y=True,
            )

        fig.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified",
            plot_bgcolor="rgba(248,250,252,1)",
        )
        fig.update_yaxes(title_text="평균기온 (°C)", secondary_y=False)
        fig.update_yaxes(title_text="소비 지수", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

        # 계절별 통계
        st.markdown("#### 계절별 소비 지수 평균")
        seasonal = df_f.groupby("계절")[selected_products].mean().round(1)
        season_order = ["봄🌸", "여름☀️", "가을🍁", "겨울❄️"]
        seasonal = seasonal.reindex([s for s in season_order if s in seasonal.index])

        fig2 = px.imshow(
            seasonal.T,
            color_continuous_scale="RdYlBu_r",
            aspect="auto",
            labels=dict(x="계절", y="품목", color="소비 지수"),
            title="계절별 소비 지수 히트맵",
            height=280
        )
        fig2.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 3 : 기온 구간별 소비
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("### 기온 구간별 평균 소비 지수")
    st.caption("기온을 구간으로 나눠 각 품목의 평균 소비 지수를 비교합니다.")

    if not selected_products:
        st.warning("왼쪽에서 품목을 선택해주세요.")
    else:
        temp_group = df_f.groupby("기온구간", observed=True)[selected_products].mean().round(1).reset_index()

        fig = go.Figure()
        for prod in selected_products:
            fig.add_trace(go.Bar(
                name=prod,
                x=temp_group["기온구간"].astype(str),
                y=temp_group[prod],
                marker_color=PRODUCTS[prod]["color"],
            ))

        fig.update_layout(
            barmode="group",
            height=400,
            xaxis_title="기온 구간",
            yaxis_title="평균 소비 지수",
            legend=dict(orientation="h", y=-0.25),
            margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="rgba(248,250,252,1)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # 최고 소비 구간 표시
        st.markdown("#### 📍 품목별 최적 판매 기온 구간")
        c1, c2 = st.columns(2)
        for i, prod in enumerate(selected_products):
            best_row = temp_group.loc[temp_group[prod].idxmax()]
            col = c1 if i % 2 == 0 else c2
            with col:
                st.success(f"**{prod}**  →  **{best_row['기온구간']}** 구간에서 최고 (지수: {best_row[prod]:.1f})")

# ═══════════════════════════════════════════════
# TAB 4 : 기온 장기 트렌드
# ═══════════════════════════════════════════════
with tab4:
    st.markdown("### 서울 연평균 기온 장기 변화 (1907~2026)")

    yearly = df[(df["연도"] >= 1920)].groupby("연도")["평균기온(℃)"].mean().reset_index()
    yearly.columns = ["연도", "연평균기온"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yearly["연도"], y=yearly["연평균기온"],
        mode="lines",
        name="연평균기온",
        line=dict(color="#94a3b8", width=1.2),
        opacity=0.7
    ))

    if show_trend:
        # 10년 이동평균
        yearly["MA10"] = yearly["연평균기온"].rolling(10, center=True).mean()
        fig.add_trace(go.Scatter(
            x=yearly["연도"], y=yearly["MA10"],
            mode="lines",
            name="10년 이동평균",
            line=dict(color="#f97316", width=3)
        ))

        # 선형 추세
        from numpy.polynomial import polynomial as P
        mask = yearly["연평균기온"].notna()
        xv = yearly.loc[mask, "연도"].values
        yv = yearly.loc[mask, "연평균기온"].values
        coef = np.polyfit(xv, yv, 1)
        fig.add_trace(go.Scatter(
            x=xv, y=np.polyval(coef, xv),
            mode="lines",
            name=f"추세선 (+{coef[0]*100:.2f}°C/100년)",
            line=dict(color="#ef4444", width=2, dash="dash")
        ))

    fig.update_layout(
        height=420,
        xaxis_title="연도",
        yaxis_title="연평균기온 (°C)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="rgba(248,250,252,1)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 기간별 평균
    st.markdown("#### 🌡️ 시대별 연평균 기온 비교")
    periods = [
        ("1920~1950년대", 1920, 1959),
        ("1960~1990년대", 1960, 1999),
        ("2000~2026년", 2000, 2026),
    ]
    pcols = st.columns(3)
    for i, (label, y1, y2) in enumerate(periods):
        avg = yearly[(yearly["연도"] >= y1) & (yearly["연도"] <= y2)]["연평균기온"].mean()
        with pcols[i]:
            st.metric(label=label, value=f"{avg:.2f}°C")

    # 시사점
    early = yearly[yearly["연도"] <= 1959]["연평균기온"].mean()
    recent = yearly[yearly["연도"] >= 2000]["연평균기온"].mean()
    delta = recent - early
    st.info(
        f"📌 **기후변화 시사점**: 1920~50년대 대비 2000년 이후 서울 연평균 기온이 "
        f"**+{delta:.1f}°C** 상승했습니다. 이는 냉방·음료·아이스크림 등 더위 관련 "
        f"품목의 연간 판매 시즌이 길어지고, 패딩·핫초코 등 방한 품목의 수요가 "
        f"장기적으로 감소하는 추세와 직결됩니다."
    )

# ── 푸터 ──────────────────────────────────────────────────
st.markdown("---")
st.caption("📡 기상 데이터: 기상청 서울 기상관측소 (지점 108) · 소비 지수는 기온과의 상관관계를 시각화하기 위한 모델 기반 추정값입니다.")

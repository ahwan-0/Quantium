"""
Quantium Retail Analytics — Interactive Dashboard
Run: python app.py  →  http://127.0.0.1:8050
"""

import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback
from copy import deepcopy
import os

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'Data', 'QVI_data.csv')

df = pd.read_csv(DATA_PATH, parse_dates=['DATE'])
df['YEARMONTH'] = df['DATE'].dt.year * 100 + df['DATE'].dt.month
df['MONTH_LABEL'] = df['DATE'].dt.to_period('M').astype(str)

# ── PRECOMPUTE METRICS ────────────────────────────────────────────────────────
# Monthly sales
monthly_sales = (
    df.groupby('MONTH_LABEL')
    .agg(SALES=('TOT_SALES', 'sum'), TXN=('TXN_ID', 'nunique'))
    .reset_index()
    .sort_values('MONTH_LABEL')
)

# KPI totals
TOTAL_SALES   = df['TOT_SALES'].sum()
TOTAL_CUSTS   = df['LYLTY_CARD_NBR'].nunique()
TOTAL_TXN     = df['TXN_ID'].nunique()
AVG_PRICE     = df['TOT_SALES'].sum() / df['PROD_QTY'].sum()

# Segment metrics
seg = (
    df.groupby(['LIFESTAGE', 'PREMIUM_CUSTOMER'])
    .apply(lambda g: pd.Series({
        'TOTAL_SALES'      : g['TOT_SALES'].sum(),
        'NUM_CUSTOMERS'    : g['LYLTY_CARD_NBR'].nunique(),
        'AVG_UNITS'        : g['PROD_QTY'].sum() / g['LYLTY_CARD_NBR'].nunique(),
        'AVG_PRICE'        : g['TOT_SALES'].sum() / g['PROD_QTY'].sum(),
    }), include_groups=False)
    .reset_index()
)

# Brand totals
brand_sales = (
    df.groupby('BRAND')['TOT_SALES']
    .sum().reset_index()
    .sort_values('TOT_SALES', ascending=False)
    .head(12)
)

# Pack size totals
pack_sales = (
    df.groupby('PACK_SIZE')['TOT_SALES']
    .sum().reset_index()
    .sort_values('PACK_SIZE')
)
pack_sales['PACK_SIZE'] = pack_sales['PACK_SIZE'].astype(int).astype(str) + 'g'

# Trial store data — control mapping
TRIAL_CTRL = {77: 233, 86: 155, 88: 237}
TRIAL_START = 201902
TRIAL_END   = 201904

store_monthly = (
    df.groupby(['STORE_NBR', 'YEARMONTH'])
    .agg(SALES=('TOT_SALES', 'sum'), CUSTS=('LYLTY_CARD_NBR', 'nunique'))
    .reset_index()
)

# ── THEME ─────────────────────────────────────────────────────────────────────
BG       = '#0A0E1A'
SURFACE  = '#111827'
SURFACE2 = '#1C2333'
ORANGE   = '#F28C28'
ORANGE2  = '#E07B1A'
TEAL     = '#38BDF8'
WHITE    = '#F0F4FF'
MUTED    = '#8892A4'
GREEN    = '#34D399'
RED      = '#F87171'
YELLOW   = '#FBBF24'

FONT = 'DM Sans, Segoe UI, sans-serif'

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=FONT, color=WHITE),
    margin=dict(l=16, r=16, t=40, b=16),
    xaxis=dict(gridcolor='#1E2A3A', linecolor='#1E2A3A', tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor='#1E2A3A', linecolor='#1E2A3A', tickfont=dict(color=MUTED)),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=MUTED)),
    hoverlabel=dict(bgcolor=SURFACE2, font=dict(color=WHITE, family=FONT)),
)

COLORSCALE = [ORANGE, TEAL, '#A78BFA', GREEN, '#FB7185', YELLOW, '#60A5FA', '#F472B6']

# ── HELPER COMPONENTS ─────────────────────────────────────────────────────────
def kpi_card(label, value, sub=None, color=ORANGE):
    return html.Div([
        html.P(label, style={'color': MUTED, 'fontSize': '11px', 'letterSpacing': '1.5px',
                             'textTransform': 'uppercase', 'margin': '0 0 6px 0', 'fontWeight': '600'}),
        html.H2(value, style={'color': WHITE, 'fontSize': '28px', 'fontWeight': '700',
                              'margin': '0', 'letterSpacing': '-0.5px'}),
        html.P(sub or '', style={'color': color, 'fontSize': '12px', 'margin': '4px 0 0 0'}),
    ], style={
        'background': SURFACE,
        'borderRadius': '12px',
        'padding': '20px 24px',
        'borderLeft': f'3px solid {color}',
        'flex': '1',
        'minWidth': '180px',
    })

def section_title(text, sub=None):
    return html.Div([
        html.H3(text, style={'color': WHITE, 'fontSize': '16px', 'fontWeight': '700',
                             'margin': '0', 'letterSpacing': '-0.3px'}),
        html.P(sub or '', style={'color': MUTED, 'fontSize': '12px', 'margin': '4px 0 0 0'}),
    ], style={'marginBottom': '16px'})

def card(children, style=None):
    base = {
        'background': SURFACE,
        'borderRadius': '14px',
        'padding': '24px',
        'border': f'1px solid #1E2A3A',
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)

# ── STATIC FIGURES ────────────────────────────────────────────────────────────
def fig_monthly_sales():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_sales['MONTH_LABEL'],
        y=monthly_sales['SALES'],
        fill='tozeroy',
        fillcolor='rgba(242,140,40,0.08)',
        line=dict(color=ORANGE, width=2.5),
        mode='lines',
        name='Monthly Sales',
        hovertemplate='<b>%{x}</b><br>$%{y:,.0f}<extra></extra>',
    ))
    # Trial period shade
    trial_months = [m for m in monthly_sales['MONTH_LABEL'] if '2019-02' <= m <= '2019-04']
    if trial_months:
        fig.add_vrect(x0='2019-02', x1='2019-04',
                      fillcolor='rgba(56,189,248,0.06)',
                      layer='below', line_width=0,
                      annotation_text='Trial Period', annotation_position='top left',
                      annotation_font=dict(color=TEAL, size=11))
    layout = deepcopy(PLOTLY_LAYOUT)
    layout['title'] = dict(text='Monthly Chip Sales', font=dict(size=14, color=WHITE), x=0)
    layout['yaxis']['tickprefix'] = '$'
    layout['yaxis']['tickformat'] = ',.0f'
    fig.update_layout(**layout)
    return fig

def fig_pack_dist():
    fig = go.Figure(go.Bar(
        x=pack_sales['PACK_SIZE'],
        y=pack_sales['TOT_SALES'],
        marker=dict(
            color=pack_sales['TOT_SALES'],
            colorscale=[[0, SURFACE2], [1, ORANGE]],
            showscale=False,
        ),
        hovertemplate='<b>%{x}</b><br>$%{y:,.0f}<extra></extra>',
    ))
    layout = deepcopy(PLOTLY_LAYOUT)
    layout['title'] = dict(text='Sales by Pack Size', font=dict(size=14, color=WHITE), x=0)
    layout['yaxis']['tickprefix'] = '$'
    layout['yaxis']['tickformat'] = ',.0f'
    fig.update_layout(**layout)
    return fig

def fig_brand_sales():
    fig = go.Figure(go.Bar(
        y=brand_sales['BRAND'],
        x=brand_sales['TOT_SALES'],
        orientation='h',
        marker=dict(
            color=brand_sales['TOT_SALES'],
            colorscale=[[0, SURFACE2], [1, ORANGE]],
            showscale=False,
        ),
        hovertemplate='<b>%{y}</b><br>$%{x:,.0f}<extra></extra>',
    ))
    layout = deepcopy(PLOTLY_LAYOUT)
    layout['title'] = dict(text='Sales by Brand', font=dict(size=14, color=WHITE), x=0)
    layout['xaxis']['tickprefix'] = '$'
    layout['xaxis']['tickformat'] = ',.0f'
    layout['yaxis']['categoryorder'] = 'total ascending'
    layout['margin'] = dict(l=16, r=16, t=40, b=16)
    fig.update_layout(**layout)
    return fig

# ── APP ───────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}]
)
app.title = 'Quantium Analytics'

# ── LAYOUT ────────────────────────────────────────────────────────────────────
app.layout = html.Div([

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    html.Div([
        # Logo
        html.Div([
            html.Div('Q', style={
                'width': '36px', 'height': '36px', 'borderRadius': '10px',
                'background': f'linear-gradient(135deg, {ORANGE}, {ORANGE2})',
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                'fontSize': '18px', 'fontWeight': '800', 'color': BG,
            }),
            html.Div([
                html.P('QUANTIUM', style={'margin': '0', 'fontSize': '12px', 'fontWeight': '800',
                                          'color': WHITE, 'letterSpacing': '2px'}),
                html.P('Analytics', style={'margin': '0', 'fontSize': '10px', 'color': MUTED}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginBottom': '40px'}),

        # Nav
        html.P('NAVIGATION', style={'color': MUTED, 'fontSize': '10px', 'letterSpacing': '2px',
                                     'fontWeight': '700', 'marginBottom': '8px'}),
        dcc.Tabs(
            id='main-tabs',
            value='overview',
            vertical=True,
            children=[
                dcc.Tab(label='⬡  Overview',    value='overview'),
                dcc.Tab(label='⬡  Segments',    value='segments'),
                dcc.Tab(label='⬡  Brand & Pack', value='affinity'),
                dcc.Tab(label='⬡  Trial Stores', value='trial'),
            ],
            style={'border': 'none'},
            colors={'border': 'transparent', 'primary': ORANGE, 'background': 'transparent'},
            parent_style={'border': 'none', 'width': '100%'},
        ),

        # Footer
        html.Div([
            html.Hr(style={'borderColor': '#1E2A3A', 'margin': '24px 0 16px 0'}),
            html.P('Chips Category', style={'color': MUTED, 'fontSize': '11px', 'margin': '0'}),
            html.P('FY 2018–2019', style={'color': MUTED, 'fontSize': '11px', 'margin': '0'}),
            html.P('246,740 transactions', style={'color': MUTED, 'fontSize': '11px', 'margin': '4px 0 0 0'}),
        ]),
    ], style={
        'width': '200px',
        'minWidth': '200px',
        'background': SURFACE,
        'padding': '28px 20px',
        'display': 'flex',
        'flexDirection': 'column',
        'borderRight': f'1px solid #1E2A3A',
        'height': '100vh',
        'position': 'sticky',
        'top': '0',
        'overflowY': 'auto',
    }),

    # ── MAIN CONTENT ─────────────────────────────────────────────────────────
    html.Div([
        html.Div(id='page-content', style={'padding': '32px', 'maxWidth': '1400px'})
    ], style={'flex': '1', 'overflowY': 'auto', 'height': '100vh'}),

], style={
    'display': 'flex',
    'fontFamily': FONT,
    'background': BG,
    'minHeight': '100vh',
    'color': WHITE,
})

# ── TAB STYLES (override defaults) ────────────────────────────────────────────
app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: ''' + BG + '''; }
  ::-webkit-scrollbar-thumb { background: #1E2A3A; border-radius: 2px; }

  .custom-tabs .tab {
    background: transparent !important;
    border: none !important;
    color: ''' + MUTED + ''' !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
    font-family: ''' + FONT + ''' !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
  }
  .custom-tabs .tab:hover {
    background: rgba(242,140,40,0.08) !important;
    color: ''' + WHITE + ''' !important;
  }
  .custom-tabs .tab--selected {
    background: rgba(242,140,40,0.12) !important;
    color: ''' + ORANGE + ''' !important;
    font-weight: 600 !important;
  }
  .custom-tabs .tab-container { border: none !important; }

  /* Dash 4 dropdown styles */
  .dash-dropdown .Select-control,
  .dash-dropdown .dropdown { 
    background: #1C2333 !important; 
    border-color: #1E2A3A !important;
    color: #F0F4FF !important;
  }
  .dash-dropdown .Select-value-label,
  .dash-dropdown .Select-placeholder { color: #F0F4FF !important; }
  .dash-dropdown .Select-menu-outer,
  .dash-dropdown .dropdown-menu { background: #1C2333 !important; border-color: #1E2A3A !important; }
  .dash-dropdown .VirtualizedSelectOption,
  .dash-dropdown .dropdown-item { color: #F0F4FF !important; background: #1C2333 !important; }
  .dash-dropdown .VirtualizedSelectFocusedOption,
  .dash-dropdown .dropdown-item:hover { background: rgba(242,140,40,0.15) !important; color: #F28C28 !important; }
  .dash-dropdown .Select-arrow { border-top-color: #8892A4 !important; }
  /* Dash 4 new dropdown */
  .dash-dropdown input { color: #F0F4FF !important; background: transparent !important; }
  .Select-control { background: #1C2333 !important; border-color: #1E2A3A !important; }
  .Select-value-label { color: #F0F4FF !important; }
  .Select-menu-outer { background: #1C2333 !important; }
  .VirtualizedSelectOption { color: #F0F4FF !important; }
  .VirtualizedSelectFocusedOption { background: rgba(242,140,40,0.1) !important; }
</style>
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>'''

# ── CALLBACKS ─────────────────────────────────────────────────────────────────
@app.callback(Output('page-content', 'children'), Input('main-tabs', 'value'))
def render_tab(tab):

    # ═══════════════════════════════════════════════════════════════════════
    # OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════
    if tab == 'overview':
        return html.Div([
            html.Div([
                html.H1('Category Overview', style={'fontSize': '26px', 'fontWeight': '700',
                                                     'color': WHITE, 'margin': '0'}),
                html.P('Chips category performance · FY 2018–2019',
                       style={'color': MUTED, 'fontSize': '13px', 'margin': '4px 0 0 0'}),
            ], style={'marginBottom': '28px'}),

            # KPI Row
            html.Div([
                kpi_card('Total Revenue', f'${TOTAL_SALES:,.0f}', 'Chip category FY2018-19', ORANGE),
                kpi_card('Unique Customers', f'{TOTAL_CUSTS:,}', 'Loyalty card holders', TEAL),
                kpi_card('Transactions', f'{TOTAL_TXN:,}', 'Across all stores', '#A78BFA'),
                kpi_card('Avg Price / Unit', f'${AVG_PRICE:.2f}', 'Per chip packet', GREEN),
            ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'marginBottom': '24px'}),

            # Charts row
            html.Div([
                card([
                    dcc.Graph(figure=fig_monthly_sales(), config={'displayModeBar': False},
                              style={'height': '300px'})
                ], style={'flex': '2', 'minWidth': '300px'}),
                card([
                    dcc.Graph(figure=fig_pack_dist(), config={'displayModeBar': False},
                              style={'height': '300px'})
                ], style={'flex': '1', 'minWidth': '260px'}),
            ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}),
        ])

    # ═══════════════════════════════════════════════════════════════════════
    # SEGMENTS
    # ═══════════════════════════════════════════════════════════════════════
    elif tab == 'segments':

        lifestage_opts = [{'label': l.title(), 'value': l} for l in sorted(df['LIFESTAGE'].unique())]
        metric_opts = [
            {'label': 'Total Revenue',          'value': 'TOTAL_SALES'},
            {'label': 'Unique Customers',        'value': 'NUM_CUSTOMERS'},
            {'label': 'Avg Units / Customer',    'value': 'AVG_UNITS'},
            {'label': 'Avg Price / Unit ($)',     'value': 'AVG_PRICE'},
        ]

        return html.Div([
            html.Div([
                html.H1('Customer Segments', style={'fontSize': '26px', 'fontWeight': '700',
                                                     'color': WHITE, 'margin': '0'}),
                html.P('21 segments across 7 life stages × 3 spending tiers',
                       style={'color': MUTED, 'fontSize': '13px', 'margin': '4px 0 0 0'}),
            ], style={'marginBottom': '28px'}),

            # Controls
            card([
                html.Div([
                    html.Div([
                        html.Label('Metric', style={'color': MUTED, 'fontSize': '11px',
                                                     'letterSpacing': '1px', 'fontWeight': '600',
                                                     'textTransform': 'uppercase', 'marginBottom': '8px',
                                                     'display': 'block'}),
                        dcc.Dropdown(
                            id='seg-metric',
                            options=metric_opts,
                            value='TOTAL_SALES',
                            clearable=False,
                            style={'background': SURFACE2},
                        ),
                    ], style={'flex': '1', 'minWidth': '200px'}),

                    html.Div([
                        html.Label('Spending Tier', style={'color': MUTED, 'fontSize': '11px',
                                                            'letterSpacing': '1px', 'fontWeight': '600',
                                                            'textTransform': 'uppercase', 'marginBottom': '8px',
                                                            'display': 'block'}),
                        dcc.Checklist(
                            id='seg-tier',
                            options=[{'label': ' ' + t, 'value': t} for t in ['Budget', 'Mainstream', 'Premium']],
                            value=['Budget', 'Mainstream', 'Premium'],
                            inline=True,
                            inputStyle={'marginRight': '4px'},
                            labelStyle={'color': WHITE, 'marginRight': '20px', 'fontSize': '13px'},
                        ),
                    ], style={'flex': '1', 'minWidth': '200px'}),
                ], style={'display': 'flex', 'gap': '32px', 'flexWrap': 'wrap', 'alignItems': 'flex-end'}),
            ], style={'marginBottom': '16px'}),

            # Segment chart
            card([dcc.Graph(id='seg-chart', config={'displayModeBar': False}, style={'height': '380px'})]),
        ])

    # ═══════════════════════════════════════════════════════════════════════
    # BRAND & AFFINITY
    # ═══════════════════════════════════════════════════════════════════════
    elif tab == 'affinity':

        seg_opts = [
            {'label': f"{row.LIFESTAGE.title()} — {row.PREMIUM_CUSTOMER}",
             'value': f"{row.LIFESTAGE}|{row.PREMIUM_CUSTOMER}"}
            for _, row in seg.sort_values('TOTAL_SALES', ascending=False).iterrows()
        ]

        return html.Div([
            html.Div([
                html.H1('Brand & Pack Affinity', style={'fontSize': '26px', 'fontWeight': '700',
                                                         'color': WHITE, 'margin': '0'}),
                html.P('How each segment over- or under-indexes vs the overall population',
                       style={'color': MUTED, 'fontSize': '13px', 'margin': '4px 0 0 0'}),
            ], style={'marginBottom': '28px'}),

            # Segment selector
            card([
                html.Label('Select Segment', style={'color': MUTED, 'fontSize': '11px',
                                                     'letterSpacing': '1px', 'fontWeight': '600',
                                                     'textTransform': 'uppercase', 'marginBottom': '8px',
                                                     'display': 'block'}),
                dcc.Dropdown(
                    id='aff-segment',
                    options=seg_opts,
                    value='YOUNG SINGLES/COUPLES|Mainstream',
                    clearable=False,
                    style={'background': SURFACE2, 'maxWidth': '420px'},
                ),
            ], style={'marginBottom': '16px'}),

            # Affinity charts
            html.Div([
                card([dcc.Graph(id='aff-brand', config={'displayModeBar': False}, style={'height': '360px'})],
                     style={'flex': '1', 'minWidth': '280px'}),
                card([dcc.Graph(id='aff-pack',  config={'displayModeBar': False}, style={'height': '360px'})],
                     style={'flex': '1', 'minWidth': '280px'}),
            ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'marginBottom': '16px'}),

            # Overall brand sales
            card([dcc.Graph(figure=fig_brand_sales(), config={'displayModeBar': False},
                            style={'height': '340px'})]),
        ])

    # ═══════════════════════════════════════════════════════════════════════
    # TRIAL STORES
    # ═══════════════════════════════════════════════════════════════════════
    elif tab == 'trial':

        return html.Div([
            html.Div([
                html.H1('Trial Store Analysis', style={'fontSize': '26px', 'fontWeight': '700',
                                                        'color': WHITE, 'margin': '0'}),
                html.P('New chip aisle layout uplift test · Feb – Apr 2019',
                       style={'color': MUTED, 'fontSize': '13px', 'margin': '4px 0 0 0'}),
            ], style={'marginBottom': '28px'}),

            # Store selector + metric selector
            card([
                html.Div([
                    html.Div([
                        html.Label('Trial Store', style={'color': MUTED, 'fontSize': '11px',
                                                          'letterSpacing': '1px', 'fontWeight': '600',
                                                          'textTransform': 'uppercase', 'marginBottom': '8px',
                                                          'display': 'block'}),
                        dcc.RadioItems(
                            id='trial-store',
                            options=[{'label': f'  Store {s}', 'value': s} for s in [77, 86, 88]],
                            value=77,
                            inline=True,
                            inputStyle={'marginRight': '4px'},
                            labelStyle={'color': WHITE, 'marginRight': '24px', 'fontSize': '13px'},
                        ),
                    ]),
                    html.Div([
                        html.Label('Metric', style={'color': MUTED, 'fontSize': '11px',
                                                     'letterSpacing': '1px', 'fontWeight': '600',
                                                     'textTransform': 'uppercase', 'marginBottom': '8px',
                                                     'display': 'block'}),
                        dcc.RadioItems(
                            id='trial-metric',
                            options=[
                                {'label': '  Total Sales',    'value': 'SALES'},
                                {'label': '  Customers',      'value': 'CUSTS'},
                            ],
                            value='SALES',
                            inline=True,
                            inputStyle={'marginRight': '4px'},
                            labelStyle={'color': WHITE, 'marginRight': '24px', 'fontSize': '13px'},
                        ),
                    ]),
                ], style={'display': 'flex', 'gap': '48px', 'flexWrap': 'wrap'}),
            ], style={'marginBottom': '16px'}),

            # Trial chart
            card([
                dcc.Graph(id='trial-chart', config={'displayModeBar': False}, style={'height': '360px'})
            ], style={'marginBottom': '16px'}),

            # Significance table
            card([html.Div(id='trial-sig-table')]),
        ])


# ── SEGMENT CHART CALLBACK ────────────────────────────────────────────────────
@app.callback(
    Output('seg-chart', 'figure'),
    Input('seg-metric', 'value'),
    Input('seg-tier', 'value'),
)
def update_seg(metric, tiers):
    filtered = seg[seg['PREMIUM_CUSTOMER'].isin(tiers)]
    pivot = filtered.pivot(index='LIFESTAGE', columns='PREMIUM_CUSTOMER', values=metric).fillna(0)

    labels = {
        'TOTAL_SALES'   : ('Total Revenue ($)', '${:,.0f}'),
        'NUM_CUSTOMERS' : ('Unique Customers',  '{:,.0f}'),
        'AVG_UNITS'     : ('Avg Units / Customer', '{:.1f}'),
        'AVG_PRICE'     : ('Avg Price / Unit ($)', '${:.2f}'),
    }
    ylabel, fmt = labels[metric]
    tier_colors = {'Budget': TEAL, 'Mainstream': ORANGE, 'Premium': '#A78BFA'}

    fig = go.Figure()
    for tier in ['Budget', 'Mainstream', 'Premium']:
        if tier in pivot.columns:
            fig.add_trace(go.Bar(
                name=tier,
                x=[l.title() for l in pivot.index],
                y=pivot[tier],
                marker_color=tier_colors[tier],
                opacity=0.9,
                hovertemplate='<b>%{x}</b><br>' + tier + '<br>%{y:,.1f}<extra></extra>',
            ))

    layout = deepcopy(PLOTLY_LAYOUT)
    layout['barmode'] = 'group'
    layout['title'] = dict(text=ylabel + ' by Segment', font=dict(size=14, color=WHITE), x=0)
    layout['yaxis']['title'] = ylabel
    if 'SALES' in metric or 'PRICE' in metric:
        layout['yaxis']['tickprefix'] = '$'
        layout['yaxis']['tickformat'] = ',.0f'
    fig.update_layout(**layout)
    return fig


# ── AFFINITY CALLBACKS ────────────────────────────────────────────────────────
def compute_affinity(target_df, full_df, col):
    target_cards = set(target_df['LYLTY_CARD_NBR'].unique())
    target_share = len(target_df) / len(full_df)
    rows = []
    for val, grp in full_df.groupby(col):
        val_target = grp[grp['LYLTY_CARD_NBR'].isin(target_cards)]
        affinity = (len(val_target) / len(grp)) / target_share if target_share > 0 else 0
        rows.append({'label': str(val), 'affinity': round(affinity, 3)})
    return pd.DataFrame(rows).sort_values('affinity', ascending=False)

@app.callback(
    Output('aff-brand', 'figure'),
    Output('aff-pack',  'figure'),
    Input('aff-segment', 'value'),
)
def update_affinity(seg_val):
    lifestage, tier = seg_val.split('|')
    target = df[(df['LIFESTAGE'] == lifestage) & (df['PREMIUM_CUSTOMER'] == tier)]

    # Brand affinity
    brand_aff = compute_affinity(target, df, 'BRAND').head(12)
    brand_colors = [ORANGE if v > 1 else TEAL for v in brand_aff['affinity']]
    fig_b = go.Figure(go.Bar(
        y=brand_aff['label'],
        x=brand_aff['affinity'],
        orientation='h',
        marker_color=brand_colors,
        hovertemplate='<b>%{y}</b><br>Affinity: %{x:.2f}×<extra></extra>',
    ))
    fig_b.add_vline(x=1.0, line_dash='dash', line_color=MUTED, line_width=1.5,
                    annotation_text='Baseline', annotation_font_color=MUTED,
                    annotation_position='top right')
    layout_b = deepcopy(PLOTLY_LAYOUT)
    layout_b['title'] = dict(text='Brand Affinity Score', font=dict(size=14, color=WHITE), x=0)
    layout_b['yaxis']['categoryorder'] = 'total ascending'
    layout_b['xaxis']['title'] = 'Affinity (1.0 = population average)'
    layout_b['xaxis']['tickprefix'] = ''
    layout_b['xaxis']['tickformat'] = '.2f'
    layout_b['yaxis']['tickprefix'] = ''
    fig_b.update_layout(**layout_b)

    # Pack size affinity
    pack_aff = compute_affinity(target, df, 'PACK_SIZE')
    pack_aff['label'] = pack_aff['label'].apply(lambda x: str(int(float(x))) + 'g')
    pack_colors = [ORANGE if v > 1 else TEAL for v in pack_aff['affinity']]
    fig_p = go.Figure(go.Bar(
        x=pack_aff['label'],
        y=pack_aff['affinity'],
        marker_color=pack_colors,
        hovertemplate='<b>%{x}</b><br>Affinity: %{y:.2f}×<extra></extra>',
    ))
    fig_p.add_hline(y=1.0, line_dash='dash', line_color=MUTED, line_width=1.5)
    layout_p = deepcopy(PLOTLY_LAYOUT)
    layout_p['title'] = dict(text='Pack Size Affinity Score', font=dict(size=14, color=WHITE), x=0)
    layout_p['yaxis']['title'] = 'Affinity (1.0 = population average)'
    layout_p['yaxis']['tickprefix'] = ''
    layout_p['yaxis']['tickformat'] = '.2f'
    layout_p['xaxis']['tickprefix'] = ''
    fig_p.update_layout(**layout_p)

    return fig_b, fig_p


# ── TRIAL CHART CALLBACK ──────────────────────────────────────────────────────
@app.callback(
    Output('trial-chart', 'figure'),
    Output('trial-sig-table', 'children'),
    Input('trial-store', 'value'),
    Input('trial-metric', 'value'),
)
def update_trial(trial_store, metric):
    ctrl_store = TRIAL_CTRL[trial_store]

    trial_data = store_monthly[store_monthly['STORE_NBR'] == trial_store][['YEARMONTH', metric]].copy()
    ctrl_data  = store_monthly[store_monthly['STORE_NBR'] == ctrl_store][['YEARMONTH', metric]].copy()

    # Scale control to match trial pre-trial baseline
    trial_pre = trial_data[trial_data['YEARMONTH'] < TRIAL_START][metric].sum()
    ctrl_pre  = ctrl_data[ctrl_data['YEARMONTH'] < TRIAL_START][metric].sum()
    scale     = trial_pre / ctrl_pre if ctrl_pre > 0 else 1.0

    ctrl_data['scaled'] = ctrl_data[metric] * scale

    # Pct diff and std dev
    merged = trial_data.merge(ctrl_data[['YEARMONTH', 'scaled']], on='YEARMONTH')
    merged['pct_diff'] = (merged[metric] - merged['scaled']).abs() / merged['scaled']
    std_dev = merged[merged['YEARMONTH'] < TRIAL_START]['pct_diff'].std()

    DOF        = 7
    t_critical = stats.t.ppf(0.95, df=DOF)

    # Trial months significance
    trial_months_df = merged[
        (merged['YEARMONTH'] >= TRIAL_START) & (merged['YEARMONTH'] <= TRIAL_END)
    ].copy()
    trial_months_df['t_value']    = trial_months_df['pct_diff'] / std_dev
    trial_months_df['significant'] = trial_months_df['t_value'] > t_critical

    # ── Plot ──────────────────────────────────────────────────────────────────
    # Convert YEARMONTH to readable label
    def ym_to_label(ym):
        y, m = divmod(int(ym), 100)
        return f"{y}-{m:02d}"

    trial_data['label'] = trial_data['YEARMONTH'].apply(ym_to_label)
    ctrl_data['label']  = ctrl_data['YEARMONTH'].apply(ym_to_label)

    ci_upper = ctrl_data['scaled'] * (1 + std_dev * 2)
    ci_lower = ctrl_data['scaled'] * (1 - std_dev * 2)

    fig = go.Figure()

    # CI band
    fig.add_trace(go.Scatter(
        x=ctrl_data['label'].tolist() + ctrl_data['label'].tolist()[::-1],
        y=ci_upper.tolist() + ci_lower.tolist()[::-1],
        fill='toself',
        fillcolor='rgba(56,189,248,0.07)',
        line=dict(color='rgba(0,0,0,0)'),
        name='95% CI',
        showlegend=True,
        hoverinfo='skip',
    ))

    # Control
    fig.add_trace(go.Scatter(
        x=ctrl_data['label'],
        y=ctrl_data['scaled'],
        line=dict(color=TEAL, width=2, dash='dot'),
        mode='lines',
        name=f'Control Store {ctrl_store} (scaled)',
        hovertemplate='<b>%{x}</b><br>Control: %{y:,.1f}<extra></extra>',
    ))

    # Trial
    fig.add_trace(go.Scatter(
        x=trial_data['label'],
        y=trial_data[metric],
        line=dict(color=ORANGE, width=2.5),
        mode='lines+markers',
        marker=dict(size=7, color=ORANGE),
        name=f'Trial Store {trial_store}',
        hovertemplate='<b>%{x}</b><br>Trial: %{y:,.1f}<extra></extra>',
    ))

    # Trial period shading
    trial_labels = [ym_to_label(ym) for ym in [TRIAL_START, TRIAL_END]]
    fig.add_vrect(
        x0=trial_labels[0], x1=trial_labels[1],
        fillcolor='rgba(242,140,40,0.06)',
        layer='below', line_width=0,
        annotation_text='Trial Period',
        annotation_position='top left',
        annotation_font=dict(color=ORANGE, size=11),
    )

    metric_label = 'Total Sales ($)' if metric == 'SALES' else 'Unique Customers'
    layout = deepcopy(PLOTLY_LAYOUT)
    layout['title'] = dict(
        text=f'{metric_label} — Store {trial_store} vs Control Store {ctrl_store}',
        font=dict(size=14, color=WHITE), x=0
    )
    layout['yaxis']['title'] = metric_label
    layout['xaxis']['title'] = 'Month'
    if metric == 'SALES':
        layout['yaxis']['tickprefix'] = '$'
        layout['yaxis']['tickformat'] = ',.0f'
    fig.update_layout(**layout)

    # ── Significance Table ────────────────────────────────────────────────────
    month_names = {201902: 'February 2019', 201903: 'March 2019', 201904: 'April 2019'}

    table_rows = []
    for _, row in trial_months_df.iterrows():
        sig = row['significant']
        table_rows.append(html.Tr([
            html.Td(month_names.get(int(row['YEARMONTH']), str(int(row['YEARMONTH']))),
                    style={'color': WHITE, 'padding': '10px 16px', 'fontSize': '13px'}),
            html.Td(f"{row['pct_diff']*100:.1f}%",
                    style={'color': MUTED, 'padding': '10px 16px', 'fontSize': '13px', 'textAlign': 'center'}),
            html.Td(f"{row['t_value']:.3f}",
                    style={'color': MUTED, 'padding': '10px 16px', 'fontSize': '13px', 'textAlign': 'center'}),
            html.Td(f"{t_critical:.3f}",
                    style={'color': MUTED, 'padding': '10px 16px', 'fontSize': '13px', 'textAlign': 'center'}),
            html.Td(
                html.Span('✅  Significant' if sig else '❌  Not significant',
                          style={'color': GREEN if sig else RED, 'fontWeight': '600', 'fontSize': '13px'}),
                style={'padding': '10px 16px', 'textAlign': 'center'}
            ),
        ], style={'borderBottom': '1px solid #1E2A3A'}))

    sig_table = html.Div([
        html.P('Significance Results', style={'color': MUTED, 'fontSize': '11px', 'letterSpacing': '1.5px',
                                              'textTransform': 'uppercase', 'fontWeight': '600',
                                              'margin': '0 0 16px 0'}),
        html.Table([
            html.Thead(html.Tr([
                html.Th('Month',        style={'color': MUTED, 'padding': '8px 16px', 'fontSize': '11px',
                                               'textTransform': 'uppercase', 'letterSpacing': '1px',
                                               'textAlign': 'left', 'fontWeight': '600'}),
                html.Th('% Difference', style={'color': MUTED, 'padding': '8px 16px', 'fontSize': '11px',
                                               'textTransform': 'uppercase', 'letterSpacing': '1px',
                                               'textAlign': 'center', 'fontWeight': '600'}),
                html.Th('T-Value',      style={'color': MUTED, 'padding': '8px 16px', 'fontSize': '11px',
                                               'textTransform': 'uppercase', 'letterSpacing': '1px',
                                               'textAlign': 'center', 'fontWeight': '600'}),
                html.Th('T-Critical',   style={'color': MUTED, 'padding': '8px 16px', 'fontSize': '11px',
                                               'textTransform': 'uppercase', 'letterSpacing': '1px',
                                               'textAlign': 'center', 'fontWeight': '600'}),
                html.Th('Result',       style={'color': MUTED, 'padding': '8px 16px', 'fontSize': '11px',
                                               'textTransform': 'uppercase', 'letterSpacing': '1px',
                                               'textAlign': 'center', 'fontWeight': '600'}),
            ], style={'borderBottom': f'2px solid {ORANGE}'})),
            html.Tbody(table_rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse'}),
    ])

    return fig, sig_table


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=8050)

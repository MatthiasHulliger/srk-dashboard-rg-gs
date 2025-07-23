import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

#####################################################################
# CONFIGURATION
#####################################################################

# Page config for wider layout
st.set_page_config(
    page_title="SRK Prognose Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Fixed parameters for MVP
DISCOUNT_RATE = 0.03  # 3% annual discount rate
N_SIMULATIONS = 750  # Increased from 500 for better accuracy

# Empirical parameters for GS (National)
EMPIRICAL_DONORS_MEAN = 3.5
EMPIRICAL_DONORS_STD = 0.75
EMPIRICAL_DONATION_MEAN = 261.48  # Annual donation
EMPIRICAL_DONATION_STD = 320.87
EMPIRICAL_RETENTION = {
    1: (83.0, 0.7),      # Year 1: 83.0% retention, 0.7% std dev
    2: (81.9, 0.7),      # Year 2: 81.9% y-o-y
    3: (85.3, 0.7)       # Year 3+: 85.3% y-o-y stable
}
EPSILON = 0.0001

# Modern color palette
COLORS = {
    'primary': '#E53935',      # Modern red
    'secondary': '#00ACC1',    # Modern cyan
    'success': '#43A047',      # Modern green
    'warning': '#FB8C00',      # Modern orange
    'dark': '#37474F',         # Modern dark gray
    'light': '#ECEFF1',        # Light gray
}

#####################################################################
# MODERN CSS STYLING WITH IMPROVED WIDTH CONTROL
#####################################################################

st.markdown("""
<style>
    /* Main container - expanded to 80% for better use of screen space */
    .block-container {
        max-width: 80%;
        margin: auto;
    }
    
    /* Campaign parameter card styling */
    .campaign-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 2px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .campaign-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        border-color: #E53935;
    }
    
    .campaign-header {
        background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        font-weight: 600;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Fix input field styling */
    .stNumberInput > div {
        max-width: 200px;
    }
    
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E0E0E0;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #E53935;
        box-shadow: 0 0 0 3px rgba(229, 57, 53, 0.1);
    }
    
    /* Modern card design */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.8);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #E53935 0%, #FF5252 100%);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #607D8B;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-sublabel {
        color: #90A4AE;
        font-size: 0.8rem;
        margin-top: 0.3rem;
    }
    
    .metric-explanation {
        color: #546E7A;
        font-size: 0.85rem;
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 1px solid #E0E0E0;
        line-height: 1.5;
    }
    
    /* Custom styling for success boxes (summary boxes) */
    .stAlert[data-baseweb="notification"] {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 4px solid #43A047;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(67, 160, 71, 0.1);
    }
    
    /* Insight boxes */
    .insight-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 4px solid #43A047;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-left-color: #FB8C00;
    }
    
    .danger-card {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left-color: #E53935;
    }
    
    .insight-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Header styling */
    h1 {
        color: #E53935;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Metric grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    /* Progress message */
    .calculation-progress {
        text-align: center;
        color: #666;
        font-style: italic;
        margin: 1rem 0;
    }
    
    /* Help tooltips */
    .help-text {
        color: #666;
        font-size: 0.85rem;
        font-style: italic;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

#####################################################################
# SESSION STATE & HEADER
#####################################################################

if "page" not in st.session_state:
    st.session_state.page = "home"
if "params" not in st.session_state:
    st.session_state.params = {}
if "campaigns" not in st.session_state:
    st.session_state.campaigns = []

def display_header():
    """Creates header with logo"""
    st.markdown(
        """
        <div class="header-container">
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("https://i.ibb.co/twVx8gyf/SRK-Logo-HQ-Crop.jpg", width=333)
        except:
            pass  # Logo not found

    st.markdown(
        """
        <div style="text-align: center; margin: 1rem 0;">
            <h1 style="font-size: 2.2rem; margin: 0;">SRK Prognose Tool: Standaktionen</h1>
            <p style="color: #666; font-size: 1rem; margin-top: 0.5rem;">
                Finanzielle Prognosen für Fundraising-Kampagnen - einfach und verständlich
            </p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )

display_header()

#####################################################################
# NAVIGATION
#####################################################################
if st.session_state.page == "home":
    st.write("### 📊 Analyseart auswählen")
    st.write("Wählen Sie die passende Analyse für Ihre Fundraising-Planung:")
    
    cols = st.columns(3)
    buttons = [
        ("🏷️ Einzelaktion", "single", "Analysieren Sie eine einzelne Fundraising-Kampagne"),
        ("📅 Mehrjährig", "multi", "Planen Sie mehrere Kampagnen über verschiedene Jahre"),
        ("📊 Szenarien", "compare", "Vergleichen Sie zwei verschiedene Strategien"),
    ]
    for col, (label, page, description) in zip(cols, buttons):
        with col:
            st.markdown(f"<p style='text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>{description}</p>", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()

#####################################################################
# PARAMETER INPUTS WITH IMPROVED STYLING
#####################################################################
if st.session_state.page != "home":
    st.write("---")
    st.write("### ⚙️ Parameter Eingabe")

    # A) EINZELAKTION
    if st.session_state.page == "single":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📅 Kampagnenumfang")
            booth_days = st.number_input(
                "Dialogertage pro Kampagne",
                min_value=10.0,
                max_value=5000.0,
                value=1000.0,
                step=25.0,
                key="s_days",
                help="Anzahl der Tage, an denen das Fundraising-Team im Einsatz ist"
            )
            
            st.markdown("##### 💰 Finanzielle Parameter")
            annual_donation = st.number_input(
                "Jährlicher Spendenbetrag (CHF)",
                min_value=10.0,
                max_value=1000.0,
                value=261.48,
                step=5.0,
                key="s_donate",
                help="Durchschnittlicher Betrag, den ein Spender pro Jahr spendet"
            )
            
            booth_cost = st.number_input(
                "Kosten pro Tag (CHF)",
                min_value=500.0,
                max_value=2000.0,
                value=830.0,
                step=10.0,
                key="s_cost",
                help="Gesamtkosten pro Einsatztag (Personal, Material, etc.)"
            )
            
        with col2:
            st.markdown("##### 👥 Spenderverhalten")
            use_empirical_retention = st.toggle(
                "Empirische Verbleibsquoten verwenden",
                value=True,
                key="s_retain_toggle",
                help="Verwendet real gemessene Verbleibsquoten aus bestehenden Kampagnen"
            )
            
            if use_empirical_retention:
                st.info("""📊 **Empirische Verbleibsquoten** (GS National):
                       - Jahr 1: 83.0% der Spender bleiben aktiv
                       - Jahr 2: 81.9% der verbleibenden Spender
                       - Jahr 3+: 85.3% (stabil)""")
                retention_rate = 83.0
            else:
                retention_rate = st.slider(
                    "Verbleibsquote (%)",
                    50.0,
                    100.0,
                    83.0,
                    key="s_retain",
                    help="Prozentsatz der Spender, die im Folgejahr weiter spenden"
                )
            
            donors_per_day = st.number_input(
                "Ø Spender/Tag",
                min_value=1.0,
                max_value=10.0,
                value=3.5,
                step=0.1,
                key="s_donors",
                help="Durchschnittliche Anzahl neuer Spender pro Einsatztag"
            )
            
            # Show estimated investment
            investment = booth_days * booth_cost
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Geschätzte Gesamtinvestition</div>
                <div class="metric-value">CHF {investment:,.0f}</div>
                <div class="metric-sublabel">{int(booth_days)} Tage × CHF {booth_cost}</div>
                <div class="metric-explanation">
                    Dies ist der Gesamtbetrag, den Sie für diese Kampagne investieren müssen.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.session_state.params = {
            "type": "single",
            "booth_days": booth_days,
            "annual_donation": annual_donation,
            "retention_rate": retention_rate,
            "donors_per_day": donors_per_day,
            "booth_cost": booth_cost,
        }

    # B) MEHRJÄHRIGE KAMPAGNE - IMPROVED LAYOUT
    elif st.session_state.page == "multi":
        st.markdown("##### 📅 Kampagnenplanung")
        num_campaigns = st.number_input(
            "Anzahl der geplanten Kampagnen", 
            min_value=1, 
            max_value=10, 
            value=3, 
            key="m_num",
            help="Wie viele separate Kampagnen möchten Sie über die Jahre planen?"
        )
        
        campaigns = []
        for i in range(int(num_campaigns)):
            # Create a visually distinct card for each campaign
            st.markdown(f"""
            <div class="campaign-card">
                <div class="campaign-header">
                    📌 Kampagne {i+1}
                </div>
            """, unsafe_allow_html=True)
            
            cc1, cc2, cc3 = st.columns(3)
            
            with cc1:
                st.markdown("**📅 Zeitplanung**")
                start_year = st.number_input("Startjahr", 
                    min_value=0.0, max_value=10.0, value=float(i), step=1.0, key=f"m_start_{i}",
                    help="In welchem Jahr startet diese Kampagne? (0 = dieses Jahr)")
                days = st.number_input("Dialogertage", 
                    min_value=10.0, max_value=5000.0, value=1000.0, step=25.0, key=f"m_days_{i}",
                    help="Anzahl der Einsatztage für diese Kampagne")
                
                # Investment preview for this campaign
                booth_cost = st.session_state.get(f"m_cost_{i}", 830.0)
                campaign_investment = days * booth_cost
                st.markdown(f"<p class='help-text'>💰 Investment: CHF {campaign_investment:,.0f}</p>", unsafe_allow_html=True)
            
            with cc2:
                st.markdown("**👥 Spendererwartung**")
                use_empirical_donors = st.toggle("Empirische Spenderdaten", value=True, 
                    key=f"m_donors_toggle_{i}",
                    help="Verwendet durchschnittliche Werte aus realen Kampagnen")
                
                if use_empirical_donors:
                    donors_per_day = EMPIRICAL_DONORS_MEAN
                    annual_donation = EMPIRICAL_DONATION_MEAN
                    st.info("📊 Empirische Werte:\n• Ø 3.5 Spender/Tag\n• CHF 261.48/Jahr")
                else:
                    donors_per_day = st.number_input("Ø Spender/Tag", 
                        min_value=1.0, max_value=10.0, value=3.5, step=0.1, key=f"m_donors_{i}")
                    annual_donation = st.number_input("Spendenbetrag (CHF/Jahr)", 
                        min_value=10.0, max_value=1000.0, value=261.48, step=5.0, key=f"m_donate_{i}")
            
            with cc3:
                st.markdown("**💸 Kosten & Verbleib**")
                use_empirical_retention = st.toggle("Empirische Verbleibsquoten", value=True, 
                    key=f"m_retain_toggle_{i}",
                    help="Verwendet real gemessene Verbleibsquoten")
                
                if use_empirical_retention:
                    retention_rate = 83.0
                    st.info("📊 Jahr 1: 83.0%\nJahr 2: 81.9%\nJahr 3+: 85.3%")
                else:
                    retention_rate = st.slider("Verbleibsquote (%)", 
                        50.0, 100.0, 83.0, key=f"m_retain_{i}")
                
                booth_cost = st.number_input("Kosten/Tag (CHF)", 
                    min_value=500.0, max_value=2000.0, value=830.0, step=10.0, key=f"m_cost_{i}",
                    help="Tageskosten für Personal, Material etc.")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
            campaigns.append({
                "start_year": start_year,
                "booth_days": days,
                "annual_donation": annual_donation,
                "retention_rate": retention_rate,
                "donors_per_day": donors_per_day,
                "booth_cost_per_day": booth_cost,
            })
        
        st.session_state.campaigns = campaigns
        
        # Show total investment summary
        total_investment = sum(c["booth_days"] * c["booth_cost_per_day"] for c in campaigns)
        total_days = sum(c["booth_days"] for c in campaigns)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Gesamtinvestition aller Kampagnen</div>
            <div class="metric-value">CHF {total_investment:,.0f}</div>
            <div class="metric-sublabel">{len(campaigns)} Kampagnen mit insgesamt {int(total_days)} Einsatztagen</div>
            <div class="metric-explanation">
                Dies ist die Summe aller Investitionen über alle geplanten Kampagnen.
                Die Kampagnen starten in verschiedenen Jahren, was die Liquiditätsbelastung verteilt.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # C) SZENARIEN VERGLEICH
    elif st.session_state.page == "compare":
        st.markdown("##### ⏱️ Vergleichszeitraum")
        duration = st.slider(
            "Anzahl Jahre für den Vergleich", 
            min_value=3.0, 
            max_value=15.0, 
            value=10.0, 
            key="c_duration",
            help="Über wie viele Jahre sollen die Szenarien verglichen werden?"
        )
        
        c1, c2 = st.columns(2)
        scenarios = {}
        for col, sc_num in zip([c1, c2], [1, 2]):
            with col:
                st.markdown(f"""
                <div class="campaign-card">
                    <div class="campaign-header" style="background: {'#E53935' if sc_num == 1 else '#00ACC1'};">
                        📊 Szenario {sc_num}
                    </div>
                """, unsafe_allow_html=True)
                
                use_empirical_retention = st.toggle(f"Empirische Verbleibsquoten", value=True, key=f"c_retain_toggle_{sc_num}")
                
                booth_days = st.number_input(f"Dialogertage/Jahr", 
                                           min_value=10.0, max_value=5000.0, 
                                           value=1000.0, step=25.0, key=f"c_days_{sc_num}",
                                           help="Jährliche Anzahl der Einsatztage")
                annual_donation = st.number_input(f"Spendenbetrag/Person (CHF)", 
                                                min_value=10.0, max_value=1000.0, 
                                                value=261.48, step=5.0, key=f"c_donate_{sc_num}",
                                                help="Durchschnittlicher Jahresbetrag pro Spender")
                
                if use_empirical_retention:
                    st.info("""📊 Empirische Verbleibsquoten:
                           • Jahr 1: 83.0%
                           • Jahr 2: 81.9%
                           • Jahr 3+: 85.3%""")
                    retention_rate = 83.0
                else:
                    retention_rate = st.slider(f"Verbleibsquote (%)", 
                                             50.0, 100.0, 83.0, key=f"c_retain_{sc_num}")
                
                donors_per_day = st.number_input(f"Ø Spender/Tag", 
                                               min_value=1.0, max_value=10.0, 
                                               value=3.5, step=0.1, key=f"c_donors_{sc_num}",
                                               help="Erwartete neue Spender pro Einsatztag")
                booth_cost = st.number_input(f"Kosten pro Tag (CHF)", 
                                           min_value=500.0, max_value=2000.0, 
                                           value=830.0, step=10.0, key=f"c_cost_{sc_num}",
                                           help="Tageskosten für Personal und Material")
                
                # Show scenario summary
                yearly_investment = booth_days * booth_cost
                expected_donors = booth_days * donors_per_day
                st.markdown(f"""
                <p class='help-text'>
                💰 Jährliche Investition: CHF {yearly_investment:,.0f}<br>
                👥 Erwartete neue Spender/Jahr: {expected_donors:,.0f}
                </p>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                scenarios[f"scenario{sc_num}"] = {
                    "booth_days": booth_days,
                    "annual_donation": annual_donation,
                    "retention_rate": retention_rate,
                    "donors_per_day": donors_per_day,
                    "booth_cost": booth_cost,
                }
        st.session_state.params = {
            "duration": duration,
            "scenario1": scenarios["scenario1"],
            "scenario2": scenarios["scenario2"],
        }

#####################################################################
# FIXED CALCULATION FUNCTIONS WITH MORE REALISTIC ASSUMPTIONS
#####################################################################

def calculate_npv(cash_flows, discount_rate=DISCOUNT_RATE):
    """Calculate Net Present Value of cash flows"""
    years = np.arange(len(cash_flows))
    discount_factors = (1 + discount_rate) ** (-years)
    return np.sum(cash_flows * discount_factors)

def calculate_payback_period(cumulative_discounted, cumulative_undiscounted):
    """Calculate both simple and discounted payback periods"""
    simple_payback = next((i for i, x in enumerate(cumulative_undiscounted) if x > 0), None)
    disc_payback = next((i for i, x in enumerate(cumulative_discounted) if x > 0), None)
    return simple_payback, disc_payback

def calculate_roi_metrics(total_revenue, total_investment, npv):
    """Calculate various ROI metrics"""
    simple_roi = ((total_revenue - total_investment) / total_investment) * 100 if total_investment > 0 else 0
    npv_roi = (npv / total_investment) * 100 if total_investment > 0 else 0
    revenue_multiple = total_revenue / total_investment if total_investment > 0 else 0
    return simple_roi, npv_roi, revenue_multiple

def calculate_metrics(booth_days, retention_rate, donors_per_day, booth_cost, annual_donation, n_simulations=N_SIMULATIONS):
    """
    Calculate campaign metrics with empirical parameters
    """
    # Determine if using empirical values
    using_empirical_donors = abs(donors_per_day - EMPIRICAL_DONORS_MEAN) < EPSILON
    using_empirical_donation = abs(annual_donation - EMPIRICAL_DONATION_MEAN) < EPSILON
    using_empirical_retention = abs(retention_rate - EMPIRICAL_RETENTION[1][0]) < EPSILON
    
    actual_donors = EMPIRICAL_DONORS_MEAN if using_empirical_donors else donors_per_day
    actual_donation = EMPIRICAL_DONATION_MEAN if using_empirical_donation else annual_donation
    
    booth_days_int = int(booth_days)
    total_investment = float(booth_days) * float(booth_cost)
    
    # Storage for simulation results
    all_npvs = []
    all_cumulative_discounted = []
    all_cumulative_undiscounted = []
    all_donors = []
    all_revenue = []
    
    for _ in range(n_simulations):
        # Sample initial donors
        daily_donors = np.random.normal(actual_donors, EMPIRICAL_DONORS_STD, booth_days_int)
        daily_donors = np.maximum(daily_donors, 0)
        initial_donors = int(np.sum(daily_donors))
        
        # Initialize arrays for 11 years (0-10)
        year_donors = np.zeros(11)
        year_revenue = np.zeros(11)
        cash_flows = np.zeros(11)
        
        # Year 0: Investment AND limited donations
        cash_flows[0] = -total_investment
        year_donors[0] = initial_donors
        
        # Only 2-3 months of donations in year 0 due to processing delay
        months_of_donation_year0 = np.random.uniform(2.0, 3.0) / 12.0
        donation_sample = np.random.normal(actual_donation, EMPIRICAL_DONATION_STD)
        donation_sample = max(donation_sample, 50)
        year_revenue[0] = initial_donors * donation_sample * months_of_donation_year0
        cash_flows[0] += year_revenue[0]
        
        # Subsequent years with retention
        curr_donors = initial_donors
        for year in range(1, 11):
            # Apply retention
            if using_empirical_retention:
                if year == 1:
                    ret_mean, ret_std = EMPIRICAL_RETENTION[1]
                elif year == 2:
                    ret_mean, ret_std = EMPIRICAL_RETENTION[2]
                else:
                    ret_mean, ret_std = EMPIRICAL_RETENTION[3]
            else:
                ret_mean = retention_rate
                ret_std = EMPIRICAL_RETENTION[1][1]
            
            retention_decimal = np.random.normal(ret_mean / 100, ret_std / 100)
            retention_decimal = min(1, max(0, retention_decimal))
            
            curr_donors = int(curr_donors * retention_decimal)
            year_donors[year] = curr_donors
            
            # Full year donations
            donation_sample = np.random.normal(actual_donation, EMPIRICAL_DONATION_STD)
            donation_sample = max(donation_sample, 50)
            year_revenue[year] = curr_donors * donation_sample
            cash_flows[year] = year_revenue[year]
        
        # Calculate NPV
        npv = calculate_npv(cash_flows)
        all_npvs.append(npv)
        
        # Calculate cumulative cash flows
        cumulative_undiscounted = np.cumsum(cash_flows)
        
        # Calculate discounted cumulative
        discounted_cash_flows = cash_flows * ((1 + DISCOUNT_RATE) ** (-np.arange(11)))
        cumulative_discounted = np.cumsum(discounted_cash_flows)
        
        all_cumulative_discounted.append(cumulative_discounted)
        all_cumulative_undiscounted.append(cumulative_undiscounted)
        all_donors.append(year_donors)
        all_revenue.append(year_revenue)
    
    # Calculate statistics
    results_array = np.array(all_cumulative_discounted)
    donors_array = np.array(all_donors)
    revenue_array = np.array(all_revenue)
    
    mean_cum_disc = np.mean(results_array, axis=0)
    mean_cum_undisc = np.mean(all_cumulative_undiscounted, axis=0)
    lower = np.percentile(results_array, 10, axis=0)
    upper = np.percentile(results_array, 90, axis=0)
    mean_don = np.mean(donors_array, axis=0)
    mean_rev = np.mean(revenue_array, axis=0)
    
    return mean_don, mean_rev, total_investment, mean_cum_disc, lower, upper, mean_cum_undisc, np.mean(all_npvs)

def calculate_multi_year_metrics(campaigns, n_simulations=N_SIMULATIONS):
    """
    Multi-campaign Monte Carlo simulation
    """
    if not campaigns:
        return {
            "mean_cumulative": np.zeros(10),
            "lower_ci": np.zeros(10),
            "upper_ci": np.zeros(10),
            "campaign_contributions": [],
            "yearly_donors": np.zeros(10),
            "yearly_revenue": np.zeros(10),
            "mean_npv": 0,
            "total_investment": 0
        }

    # Determine the max simulation duration
    max_year = int(max(float(c["start_year"]) for c in campaigns) + 10)
    
    all_results = []
    all_npvs = []
    campaign_contributions = []

    for _ in range(n_simulations):
        yearly_donors = np.zeros(max_year + 1)
        yearly_revenue = np.zeros(max_year + 1)
        yearly_cash_flows = np.zeros(max_year + 1)
        sim_campaign_metrics = []

        for camp in campaigns:
            camp_start_year = int(float(camp["start_year"]))
            booth_days_int = int(float(camp["booth_days"]))
            investment = float(camp["booth_days"]) * float(camp["booth_cost_per_day"])
            
            # Investment in start year
            yearly_cash_flows[camp_start_year] -= investment
            
            # Determine if using empirical data
            using_empirical_donors = abs(float(camp["donors_per_day"]) - EMPIRICAL_DONORS_MEAN) < EPSILON
            using_empirical_donation = abs(float(camp["annual_donation"]) - EMPIRICAL_DONATION_MEAN) < EPSILON
            using_empirical_retention = abs(float(camp["retention_rate"]) - EMPIRICAL_RETENTION[1][0]) < EPSILON
            
            actual_donors = EMPIRICAL_DONORS_MEAN if using_empirical_donors else float(camp["donors_per_day"])
            actual_donation = EMPIRICAL_DONATION_MEAN if using_empirical_donation else float(camp["annual_donation"])

            # Simulate daily donor acquisition
            daily_donors = np.random.normal(actual_donors, EMPIRICAL_DONORS_STD, booth_days_int)
            daily_donors = np.maximum(daily_donors, 0)
            initial_donors = int(np.sum(daily_donors))

            camp_donors = np.zeros(max_year + 1)
            camp_revenue = np.zeros(max_year + 1)
            
            # Year 0 (acquisition year) - only 2-3 months of donations
            camp_donors[camp_start_year] = initial_donors
            months_of_donation = np.random.uniform(2.0, 3.0) / 12.0
            donation_sample = np.random.normal(actual_donation, EMPIRICAL_DONATION_STD)
            first_year_revenue = initial_donors * max(donation_sample, 50) * months_of_donation
            camp_revenue[camp_start_year] = first_year_revenue
            yearly_revenue[camp_start_year] += first_year_revenue
            yearly_cash_flows[camp_start_year] += first_year_revenue

            # Subsequent years
            curr_donors = initial_donors
            for yr in range(camp_start_year + 1, min(camp_start_year + 11, max_year + 1)):
                year_since_start = yr - camp_start_year
                
                # Retention rate logic
                if using_empirical_retention:
                    if year_since_start == 1:
                        ret_mean, ret_std = EMPIRICAL_RETENTION[1]
                    elif year_since_start == 2:
                        ret_mean, ret_std = EMPIRICAL_RETENTION[2]
                    else:
                        ret_mean, ret_std = EMPIRICAL_RETENTION[3]
                else:
                    ret_mean = float(camp["retention_rate"])
                    ret_std = EMPIRICAL_RETENTION[1][1]

                retention_decimal = np.random.normal(ret_mean / 100, ret_std / 100)
                retention_decimal = min(1, max(0, retention_decimal))
                
                curr_donors = int(curr_donors * retention_decimal)
                if curr_donors < 1:
                    break

                camp_donors[yr] = curr_donors
                donation_sample = np.random.normal(actual_donation, EMPIRICAL_DONATION_STD)
                revenue = curr_donors * max(donation_sample, 50)
                camp_revenue[yr] = revenue
                
                yearly_donors[yr] += curr_donors
                yearly_revenue[yr] += revenue
                yearly_cash_flows[yr] += revenue

            sim_campaign_metrics.append({
                "donors": camp_donors,
                "revenue": camp_revenue,
                "investment": investment,
            })

        # Calculate NPV
        npv = calculate_npv(yearly_cash_flows)
        all_npvs.append(npv)
        
        # Calculate cumulative
        cumulative_cash_flows = np.cumsum(yearly_cash_flows)
        discounted_cash_flows = yearly_cash_flows * ((1 + DISCOUNT_RATE) ** (-np.arange(len(yearly_cash_flows))))
        cumulative_discounted = np.cumsum(discounted_cash_flows)
        
        all_results.append(cumulative_discounted)
        campaign_contributions.append(sim_campaign_metrics)

    # Compute final statistics
    results_array = np.array(all_results)
    mean_cumulative = np.mean(results_array, axis=0)
    lower_ci = np.percentile(results_array, 10, axis=0)
    upper_ci = np.percentile(results_array, 90, axis=0)

    # Average campaign contributions
    avg_campaign_contrib = []
    for i in range(len(campaigns)):
        donors_across_sims = np.array([sim[i]["donors"] for sim in campaign_contributions])
        revenue_across_sims = np.array([sim[i]["revenue"] for sim in campaign_contributions])
        avg_campaign_contrib.append({
            "donors": np.mean(donors_across_sims, axis=0),
            "revenue": np.mean(revenue_across_sims, axis=0),
            "investment": campaign_contributions[0][i]["investment"]
        })

    # Compute yearly totals
    all_yearly_donors = []
    all_yearly_revenue = []
    for sim_contrib in campaign_contributions:
        combined_donors = np.sum([m["donors"] for m in sim_contrib], axis=0)
        combined_revenue = np.sum([m["revenue"] for m in sim_contrib], axis=0)
        all_yearly_donors.append(combined_donors)
        all_yearly_revenue.append(combined_revenue)
    
    total_investment = sum(float(c["booth_days"]) * float(c["booth_cost_per_day"]) for c in campaigns)

    return {
        "mean_cumulative": mean_cumulative,
        "lower_ci": lower_ci,
        "upper_ci": upper_ci,
        "campaign_contributions": avg_campaign_contrib,
        "yearly_donors": np.mean(all_yearly_donors, axis=0),
        "yearly_revenue": np.mean(all_yearly_revenue, axis=0),
        "mean_npv": np.mean(all_npvs),
        "total_investment": total_investment
    }

def create_multi_year_visualization(results, campaigns):
    """
    Creates comprehensive visualization of multi-year campaign results
    """
    years = np.arange(len(results["mean_cumulative"]))

    # 1) Cumulative Net Figure
    cumulative_fig = go.Figure()

    # Add confidence band
    cumulative_fig.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([results["upper_ci"], results["lower_ci"][::-1]]),
        fill="toself",
        fillcolor="rgba(244, 36, 52, 0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        name="80% Konfidenzintervall",
        showlegend=True
    ))

    # Add mean total line
    cumulative_fig.add_trace(go.Scatter(
        x=years,
        y=results["mean_cumulative"],
        mode="lines+markers",
        name="Erwarteter Nettoertrag (diskontiert)",
        line=dict(color="#F42434", width=3),
        marker=dict(size=8)
    ))

    # Add investment line
    cumulative_fig.add_hline(
        y=-results["total_investment"],
        line_dash="dot",
        line_color="#666666",
        annotation_text=f"Gesamtinvestition: CHF {results['total_investment']:,.0f}",
        annotation_position="right"
    )

    # Add break-even line
    cumulative_fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Break-Even",
        annotation_position="left"
    )

    # Add individual campaign contributions
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
    for idx, contrib in enumerate(results["campaign_contributions"]):
        camp_net = np.cumsum(contrib["revenue"]) - contrib["investment"]
        cumulative_fig.add_trace(go.Scatter(
            x=years,
            y=camp_net,
            mode="lines",
            name=f"Kampagne {idx+1}",
            line=dict(color=colors[idx % len(colors)], dash="dot"),
            opacity=0.7
        ))

    cumulative_fig.update_layout(
        title="Kumulierter Nettoertrag pro Jahr<br><sub>Mit 3% jährlicher Diskontierung</sub>",
        xaxis_title="Jahre",
        yaxis_title="CHF",
        template="plotly_white",
        height=450,
        hovermode='x unified'
    )

    # 2) Donors Figure
    donors_fig = go.Figure()
    donors_fig.add_trace(go.Scatter(
        x=years,
        y=results["yearly_donors"],
        mode="lines+markers",
        name="Gesamt SpenderInnen",
        line=dict(color="#F42434", width=3),
        fill='tozeroy',
        fillcolor='rgba(244,36,52,0.1)'
    ))
    
    # Add individual campaigns
    for idx, c in enumerate(results["campaign_contributions"]):
        donors_fig.add_trace(go.Scatter(
            x=years,
            y=c["donors"],
            mode="lines",
            name=f"Kampagne {idx+1}",
            line=dict(color=colors[idx % len(colors)], dash="dot"),
            opacity=0.7
        ))
    
    donors_fig.update_layout(
        title="SpenderInnenentwicklung",
        xaxis_title="Jahre",
        yaxis_title="Anzahl SpenderInnen",
        template="plotly_white",
        height=350
    )

    # 3) Revenue Figure
    revenue_fig = go.Figure()
    revenue_fig.add_trace(go.Bar(
        x=years,
        y=results["yearly_revenue"],
        name="Gesamt Ertrag",
        marker_color="#F42434",
        text=[f"CHF {int(v):,}" if v > 1000 else "" for v in results["yearly_revenue"]],
        textposition="outside"
    ))
    
    revenue_fig.update_layout(
        title="Jährlicher Spendenertrag",
        xaxis_title="Jahre",
        yaxis_title="CHF",
        template="plotly_white",
        height=350
    )

    return cumulative_fig, donors_fig, revenue_fig

def create_marketing_insights(results, params):
    """Generate insights for marketing professionals"""
    insights = []
    
    # Break-even insight
    break_even = next((i for i, x in enumerate(results[3]) if x > 0), 10)
    
    if break_even < 3:
        insights.append({
            "type": "success",
            "icon": "✅",
            "title": "Schnelle Amortisation",
            "text": f"Die Investition amortisiert sich nach nur {break_even:.1f} Jahren - ein exzellentes Ergebnis!"
        })
    elif break_even < 5:
        insights.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "Mittlere Amortisationszeit",
            "text": f"Amortisation nach {break_even:.1f} Jahren - eine solide Investition mit Geduld."
        })
    else:
        insights.append({
            "type": "danger",
            "icon": "🔴",
            "title": "Lange Amortisationszeit",
            "text": f"Über {break_even:.1f} Jahre bis zur Amortisation - sorgfältige Überlegung empfohlen."
        })
    
    # NPV insight
    npv = results[7] if len(results) > 7 else results[3][-1]
    if npv > results[2] * 0.5:
        insights.append({
            "type": "success",
            "icon": "💰",
            "title": "Hohe Rentabilität",
            "text": f"Kapitalwert von CHF {npv:,.0f} zeigt ausgezeichnete Rendite."
        })
    
    # Success probability
    success_prob = np.mean([x > 0 for x in results[3]]) * 100
    if success_prob > 80:
        insights.append({
            "type": "success",
            "icon": "🎯",
            "title": "Niedriges Risiko",
            "text": f"{success_prob:.0f}% Erfolgswahrscheinlichkeit - sehr sicheres Investment."
        })
    
    return insights

def create_simple_summary(investment, npv, total_revenue, break_even, roi):
    """Create a simple, understandable summary for non-technical users"""
    # Calculate net profit
    net_profit = total_revenue - investment
    
    # Create a styled container using Streamlit's success message
    with st.container():
        st.success(f"""
💡 **Einfache Zusammenfassung Ihrer Investition**

Mit einer Anfangsinvestition von **CHF {investment:,.0f}** können Sie über 10 Jahre insgesamt **CHF {total_revenue:,.0f}** an Spendeneinnahmen generieren.

Das bedeutet einen Nettogewinn von **CHF {net_profit:,.0f}** (unter Berücksichtigung des Zeitwerts des Geldes: **CHF {npv:,.0f}**).

Ihre Investition amortisiert sich nach **{break_even:.1f} Jahren** und erzielt eine Gesamtrendite von **{roi:.0f}%**.

*Anders ausgedrückt: Für jeden investierten Franken erhalten Sie {total_revenue/investment:.2f} Franken zurück.*
""")
    
    return None  # Return None since we're rendering directly

#####################################################################
# 5) DISPLAY THE RESULTS FOR EACH PAGE
#####################################################################
if st.session_state.page != "home":
    st.write("---")
    st.write("## 📊 Analyseergebnisse")

    # A) EINZELNE STANDAKTION
    if st.session_state.page == "single":
        p = st.session_state.params
        
        # Add calculation progress indicator
        calculation_message = st.empty()
        calculation_message.markdown('<div class="calculation-progress">🔄 Berechne realistische Prognose mit 750 Simulationen... (ca. 20 Sekunden)</div>', unsafe_allow_html=True)
        
        donors, revenue, inv, cum_disc, lower, upper, cum_undisc, npv = calculate_metrics(
            p["booth_days"],
            p["retention_rate"],
            p["donors_per_day"],
            p["booth_cost"],
            p["annual_donation"]
        )
        
        calculation_message.empty()

        # Compute KPIs
        break_even = next((i for i, x in enumerate(cum_disc) if x > 0), 10)
        roi = (npv / inv) * 100 if inv > 0 else 0
        total_revenue = np.sum(revenue)
        revenue_multiple = total_revenue / inv if inv > 0 else 0

        # Display simple summary first
        create_simple_summary(inv, npv, total_revenue, break_even, roi)

        # Generate insights
        results_tuple = (donors, revenue, inv, cum_disc, lower, upper, cum_undisc, npv)
        insights = create_marketing_insights(results_tuple, p)
        
        # Display insights
        insight_cols = st.columns(len(insights))
        for col, insight in zip(insight_cols, insights):
            with col:
                st.markdown(f"""
                <div class="insight-card {insight['type']}-card">
                    <div class="insight-title">
                        <span style="font-size: 1.2rem;">{insight['icon']}</span>
                        {insight['title']}
                    </div>
                    <div>{insight['text']}</div>
                </div>
                """, unsafe_allow_html=True)

        # KPI Cards with explanations
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        kpi_data = [
            ("Amortisation (diskontiert)", 
             f"{break_even:.1f} Jahre", 
             "Zeitwert berücksichtigt",
             "Ab diesem Zeitpunkt haben Sie Ihre komplette Investition wieder eingespielt und beginnen Gewinn zu machen."),
            ("Kapitalwert (NPV)", 
             f"CHF {npv:,.0f}", 
             "Barwert nach 10 Jahren",
             "Der heutige Wert aller zukünftigen Einnahmen minus Ihrer Investition. Ein positiver Wert bedeutet: Die Investition lohnt sich!"),
            ("ROI", 
             f"{roi:.0f}%", 
             "Return on Investment",
             f"Ihre Gesamtrendite: Pro 100 CHF Investition erhalten Sie {roi:.0f} CHF zusätzlich zurück."),
            ("Umsatzmultiplikator", 
             f"{revenue_multiple:.1f}x", 
             "Einnahmen/Investition",
             f"Sie generieren das {revenue_multiple:.1f}-fache Ihrer Investition an Spendeneinnahmen.")
        ]
        
        cols = st.columns(len(kpi_data))
        for col, (label, value, sublabel, explanation) in zip(cols, kpi_data):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sublabel">{sublabel}</div>
                    <div class="metric-explanation">{explanation}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Plot: cumulative net with confidence
        years = np.arange(0, 11)
        fig_cum = go.Figure()
        
        # Add investment line
        fig_cum.add_trace(go.Scatter(
            x=years,
            y=[-inv] * len(years),
            mode="lines",
            name="Investition",
            line=dict(color="#666666", width=2, dash="dot"),
        ))
        
        # Add confidence band
        fig_cum.add_trace(go.Scatter(
            x=np.concatenate([years, years[::-1]]),
            y=np.concatenate([upper, lower[::-1]]),
            fill="toself",
            fillcolor="rgba(244,36,52,0.1)",
            line=dict(color="rgba(255,255,255,0)"),
            name="80% Konfidenzbereich",
        ))
        
        # Add mean discounted line
        fig_cum.add_trace(go.Scatter(
            x=years,
            y=cum_disc,
            mode="lines+markers",
            name="Erwarteter Nettoertrag (diskontiert)",
            line=dict(color="#F42434", width=3),
            marker=dict(size=8)
        ))
        
        # Add undiscounted line for comparison
        fig_cum.add_trace(go.Scatter(
            x=years,
            y=cum_undisc,
            mode="lines",
            name="Nettoertrag (nominal)",
            line=dict(color="#F42434", width=2, dash="dash"),
            opacity=0.5
        ))
        
        # Add break-even line
        fig_cum.add_hline(y=0, line_dash="solid", line_color="green", line_width=1,
                         annotation_text="Break-Even", annotation_position="left")
        
        fig_cum.update_layout(
            title="Kumulierter Nettoertrag über 10 Jahre<br><sub>Mit 3% jährlicher Diskontierung</sub>",
            xaxis_title="Jahre nach Kampagnenstart",
            yaxis_title="CHF",
            template="plotly_white",
            height=450,
            hovermode='x unified'
        )
        st.plotly_chart(fig_cum, use_container_width=True)

        # Explanation box
        with st.expander("💡 Was bedeuten diese Begriffe?"):
            st.markdown("""
            **Diskontierung:** Berücksichtigt, dass CHF 1'000 heute mehr wert sind als CHF 1'000 in der Zukunft
            (wegen Inflation und entgangenen Zinsen).
            
            **Nettoertrag:** Ihre Spendeneinnahmen minus Ihre Investition.
            
            **80% Konfidenzbereich:** In 8 von 10 Fällen wird Ihr tatsächliches Ergebnis in diesem grauen Bereich liegen.
            
            **Break-Even:** Der Zeitpunkt, ab dem Sie Gewinn machen.
            
            Die **rote durchgezogene Linie** zeigt das wahrscheinlichste Ergebnis unter Berücksichtigung des Zeitwerts.
            Die **gestrichelte Linie** zeigt die nominalen Werte ohne Zeitwertberücksichtigung.
            """)

        # Donors + Revenue side by side
        c1, c2 = st.columns(2)
        with c1:
            fig_d = go.Figure()
            fig_d.add_trace(go.Scatter(
                x=years,
                y=donors,
                mode="lines+markers",
                name="Aktive SpenderInnen",
                line=dict(color="#F42434", width=2),
                fill='tozeroy',
                fillcolor='rgba(244,36,52,0.1)',
                marker=dict(size=6)
            ))
            fig_d.update_layout(
                title="Aktive SpenderInnen pro Jahr",
                xaxis_title="Jahre",
                yaxis_title="SpenderInnen",
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_d, use_container_width=True)
            
        with c2:
            # Create annotations for small values
            text_values = []
            for i, v in enumerate(revenue):
                if v > 10000:  # Only show for significant values
                    text_values.append(f"CHF {int(v/1000)}k")
                else:
                    text_values.append("")
            
            fig_r = go.Figure()
            fig_r.add_trace(go.Bar(
                x=years,
                y=revenue,
                name="Spendeneinnahmen",
                marker_color="#F42434",
                text=text_values,
                textposition="outside"
            ))
            
            # Highlight year 0 with different color
            colors = ['#FFCDD2'] + ['#F42434'] * 10
            fig_r.update_traces(marker_color=colors)
            
            fig_r.update_layout(
                title="Jährliche Spendeneinnahmen<br><sub>Jahr 0: nur 2-3 Monate Spenden</sub>",
                xaxis_title="Jahre",
                yaxis_title="CHF",
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_r, use_container_width=True)

        # Detailed data table
        with st.expander("📋 Detaillierte Jahresübersicht"):
            df = pd.DataFrame({
                "Jahr": years.astype(int),
                "SpenderInnen": donors.astype(int),
                "Spendeneinnahmen": revenue,
                "Kumuliert (nominal)": cum_undisc,
                "Kumuliert (diskontiert)": cum_disc,
                "Differenz": cum_disc - cum_undisc
            })
            
            # Apply formatting and color gradient
            styled_df = df.style.format({
                "Spendeneinnahmen": "CHF {:,.0f}",
                "Kumuliert (nominal)": "CHF {:,.0f}",
                "Kumuliert (diskontiert)": "CHF {:,.0f}",
                "Differenz": "CHF {:,.0f}"
            })
            
            # Add background gradient for cumulative discounted
            styled_df = styled_df.background_gradient(
                subset=['Kumuliert (diskontiert)'], 
                cmap='RdYlGn', 
                vmin=-inv, 
                vmax=max(cum_disc)
            )
            
            # Add background gradient for revenue
            styled_df = styled_df.background_gradient(
                subset=['Spendeneinnahmen'], 
                cmap='Blues', 
                vmin=0, 
                vmax=max(revenue)
            )
            
            st.dataframe(styled_df, use_container_width=True)

    # B) MEHRJÄHRIGE KAMPAGNE
    elif st.session_state.page == "multi":
        calculation_message = st.empty()
        calculation_message.markdown('<div class="calculation-progress">🔄 Berechne Mehrjahresprognose mit 750 Simulationen... (ca. 25 Sekunden)</div>', unsafe_allow_html=True)
        
        results = calculate_multi_year_metrics(st.session_state.campaigns)
        
        calculation_message.empty()
        
        cum = results["mean_cumulative"]
        lower = results["lower_ci"]
        upper = results["upper_ci"]
        total_invest = results["total_investment"]
        npv = results["mean_npv"]

        # Break-even, ROI
        break_even = next((i for i, x in enumerate(cum) if x > 0), len(cum) - 1)
        roi = (npv / total_invest) * 100 if total_invest else 0
        total_revenue = sum(results["yearly_revenue"])

        # Display simple summary first
        create_simple_summary(total_invest, npv, total_revenue, break_even, roi)

        # Marketing insights
        insights = []
        if break_even < 4:
            insights.append({
                "type": "success",
                "icon": "✅",
                "title": "Schnelle Amortisation",
                "text": f"Die Gesamtinvestition amortisiert sich nach {break_even:.1f} Jahren."
            })
        else:
            insights.append({
                "type": "warning", 
                "icon": "⚠️",
                "title": "Mittlere Amortisationszeit",
                "text": f"Amortisation nach {break_even:.1f} Jahren - langfristige Perspektive wichtig."
            })
        
        if npv > total_invest * 0.5:
            insights.append({
                "type": "success",
                "icon": "💰",
                "title": "Hohe Rentabilität",
                "text": f"Kapitalwert von CHF {npv:,.0f} zeigt sehr gute Rendite."
            })
        
        # Display insights
        insight_cols = st.columns(len(insights))
        for col, insight in zip(insight_cols, insights):
            with col:
                st.markdown(f"""
                <div class="insight-card {insight['type']}-card">
                    <div class="insight-title">
                        {insight['icon']} {insight['title']}
                    </div>
                    <div>{insight['text']}</div>
                </div>
                """, unsafe_allow_html=True)

        # KPI Cards with explanations
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        kpi_data = [
            ("Amortisation", 
             f"{break_even:.1f} Jahre", 
             "Diskontiert",
             "Nach dieser Zeit haben alle Kampagnen zusammen ihre Kosten wieder eingespielt."),
            ("Kapitalwert (NPV)", 
             f"CHF {npv:,.0f}", 
             "Nach 10 Jahren",
             "Der Gesamtwert aller Kampagnen in heutigen Franken."),
            ("ROI", 
             f"{roi:.0f}%", 
             "Return on Investment",
             f"Die Gesamtrendite über alle Kampagnen."),
            ("Gesamtinvestition", 
             f"CHF {total_invest:,.0f}", 
             f"{len(st.session_state.campaigns)} Kampagnen",
             "Die Summe aller Kampagneninvestitionen über die Jahre verteilt.")
        ]
        
        cols = st.columns(len(kpi_data))
        for col, (label, value, sublabel, explanation) in zip(cols, kpi_data):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sublabel">{sublabel}</div>
                    <div class="metric-explanation">{explanation}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Plots
        cumulative_fig, donors_fig, revenue_fig = create_multi_year_visualization(results, st.session_state.campaigns)
        st.plotly_chart(cumulative_fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(donors_fig, use_container_width=True)
        with c2:
            st.plotly_chart(revenue_fig, use_container_width=True)

        # Detailed breakdown
        with st.expander("📋 Kampagnenübersicht"):
            camp_df = pd.DataFrame([
                {
                    "Kampagne": f"Kampagne {i+1}",
                    "Startjahr": int(c["start_year"]),
                    "Dialogertage": int(c["booth_days"]),
                    "Investition": c["booth_days"] * c["booth_cost_per_day"],
                    "Ø Spender/Tag": c["donors_per_day"],
                    "Jahresspende": c["annual_donation"],
                    "Verbleibsquote": c["retention_rate"]
                }
                for i, c in enumerate(st.session_state.campaigns)
            ])
            
            # Apply formatting and color coding
            styled_camp_df = camp_df.style.format({
                "Investition": "CHF {:,.0f}",
                "Ø Spender/Tag": "{:.2f}",
                "Jahresspende": "CHF {:.2f}",
                "Verbleibsquote": "{:.1f}%"
            })
            
            # Add background gradient for investment
            styled_camp_df = styled_camp_df.background_gradient(
                subset=['Investition'], 
                cmap='Reds', 
                vmin=0, 
                vmax=camp_df['Investition'].max()
            )
            
            st.dataframe(styled_camp_df, use_container_width=True)
            
            # Add yearly breakdown
            st.write("##### Jährliche Übersicht")
            yearly_df = pd.DataFrame({
                "Jahr": np.arange(len(results["yearly_donors"])),
                "Aktive SpenderInnen": results["yearly_donors"].astype(int),
                "Spendeneinnahmen": results["yearly_revenue"],
                "Kumuliert (diskontiert)": results["mean_cumulative"]
            })
            
            # Only show rows with activity
            yearly_df = yearly_df[yearly_df['Spendeneinnahmen'] > 0]
            
            styled_yearly_df = yearly_df.style.format({
                "Spendeneinnahmen": "CHF {:,.0f}",
                "Kumuliert (diskontiert)": "CHF {:,.0f}"
            })
            
            # Add gradients
            styled_yearly_df = styled_yearly_df.background_gradient(
                subset=['Kumuliert (diskontiert)'], 
                cmap='RdYlGn', 
                vmin=-total_invest, 
                vmax=yearly_df['Kumuliert (diskontiert)'].max()
            )
            
            st.dataframe(styled_yearly_df, use_container_width=True)

    # C) SZENARIENVERGLEICH
    elif st.session_state.page == "compare":
        par = st.session_state.params
        duration = par["duration"]
        sc1 = par["scenario1"]
        sc2 = par["scenario2"]

        # Build repeated campaigns
        campaigns1 = []
        campaigns2 = []
        for year in range(int(duration)):
            campaigns1.append({
                "start_year": year,
                "booth_days": sc1["booth_days"],
                "annual_donation": sc1["annual_donation"],
                "retention_rate": sc1["retention_rate"],
                "donors_per_day": sc1["donors_per_day"],
                "booth_cost_per_day": sc1["booth_cost"],
            })
            campaigns2.append({
                "start_year": year,
                "booth_days": sc2["booth_days"],
                "annual_donation": sc2["annual_donation"],
                "retention_rate": sc2["retention_rate"],
                "donors_per_day": sc2["donors_per_day"],
                "booth_cost_per_day": sc2["booth_cost"],
            })

        calculation_message = st.empty()
        calculation_message.markdown('<div class="calculation-progress">🔄 Vergleiche Szenarien mit 750 Simulationen... (ca. 35 Sekunden)</div>', unsafe_allow_html=True)
        
        results1 = calculate_multi_year_metrics(campaigns1)
        results2 = calculate_multi_year_metrics(campaigns2)
        
        calculation_message.empty()

        net1 = results1["mean_npv"]
        net2 = results2["mean_npv"]
        inv1 = results1["total_investment"]
        inv2 = results2["total_investment"]
        break1 = next((i for i, x in enumerate(results1["mean_cumulative"]) if x > 0), duration)
        break2 = next((i for i, x in enumerate(results2["mean_cumulative"]) if x > 0), duration)
        roi1 = (net1 / inv1) * 100 if inv1 > 0 else 0
        roi2 = (net2 / inv2) * 100 if inv2 > 0 else 0
        
        # Calculate total revenues
        total_rev1 = sum(results1["yearly_revenue"])
        total_rev2 = sum(results2["yearly_revenue"])

        # Winner determination
        if net1 > net2 * 1.1:
            winner_text = "🏆 Szenario 1 ist deutlich profitabler"
            winner_color = "#E53935"
            winner_num = 1
        elif net2 > net1 * 1.1:
            winner_text = "🏆 Szenario 2 ist deutlich profitabler"
            winner_color = "#00ACC1"
            winner_num = 2
        else:
            winner_text = "⚖️ Beide Szenarien sind ähnlich profitabel"
            winner_color = "#43A047"
            winner_num = 0

        st.markdown(f"""
        <div style="background: {winner_color}22; border: 2px solid {winner_color}; 
                    border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 1.5rem;">
            <h3 style="margin: 0; color: {winner_color};">{winner_text}</h3>
        </div>
        """, unsafe_allow_html=True)

        # Create simple comparison summary
        st.success(f"""
💡 **Vergleich in einfachen Worten**

**Szenario 1:** Mit CHF {inv1:,.0f} Investition generieren Sie CHF {total_rev1:,.0f} (Gewinn: CHF {net1:,.0f}, ROI: {roi1:.0f}%)

**Szenario 2:** Mit CHF {inv2:,.0f} Investition generieren Sie CHF {total_rev2:,.0f} (Gewinn: CHF {net2:,.0f}, ROI: {roi2:.0f}%)

**Empfehlung:** {f"Szenario {winner_num}" if winner_num > 0 else "Beide Szenarien"} bietet die bessere Rendite. Der Unterschied beträgt CHF {abs(net1-net2):,.0f} zu Ihren Gunsten.
""")

        # KPI Cards for compare
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        # Scenario 1
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #E53935;">
            <div class="metric-label">Szenario 1</div>
            <div style="margin-top: 0.5rem;">
                <strong>Amortisation:</strong> {break1:.1f} Jahre<br>
                <strong>NPV:</strong> CHF {net1:,.0f}<br>
                <strong>ROI:</strong> {roi1:.0f}%<br>
                <strong>Investition:</strong> CHF {inv1:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Differenz
        diff_break = break2 - break1
        diff_npv = net2 - net1
        diff_roi = roi2 - roi1
        diff_inv = inv2 - inv1
        
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #888888;">
            <div class="metric-label">Differenz (S2 - S1)</div>
            <div style="margin-top: 0.5rem;">
                <strong>Amortisation:</strong> {'+' if diff_break > 0 else ''}{diff_break:.1f} Jahre<br>
                <strong>NPV:</strong> {'+' if diff_npv > 0 else ''}CHF {diff_npv:,.0f}<br>
                <strong>ROI:</strong> {'+' if diff_roi > 0 else ''}{diff_roi:.1f}%<br>
                <strong>Investition:</strong> {'+' if diff_inv > 0 else ''}CHF {diff_inv:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Scenario 2
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00ACC1;">
            <div class="metric-label">Szenario 2</div>
            <div style="margin-top: 0.5rem;">
                <strong>Amortisation:</strong> {break2:.1f} Jahre<br>
                <strong>NPV:</strong> CHF {net2:,.0f}<br>
                <strong>ROI:</strong> {roi2:.0f}%<br>
                <strong>Investition:</strong> CHF {inv2:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Comparison visualization
        years1 = np.arange(len(results1["mean_cumulative"]))
        years2 = np.arange(len(results2["mean_cumulative"]))
        years = np.arange(min(len(years1), len(years2)))
        
        # Combined comparison chart
        fig_compare = go.Figure()
        
        # Add confidence bands
        fig_compare.add_trace(go.Scatter(
            x=np.concatenate([years, years[::-1]]),
            y=np.concatenate([results1["upper_ci"][:len(years)], results1["lower_ci"][:len(years)][::-1]]),
            fill="toself",
            fillcolor="rgba(229, 57, 53, 0.1)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig_compare.add_trace(go.Scatter(
            x=np.concatenate([years, years[::-1]]),
            y=np.concatenate([results2["upper_ci"][:len(years)], results2["lower_ci"][:len(years)][::-1]]),
            fill="toself",
            fillcolor="rgba(0, 172, 193, 0.1)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add main lines
        fig_compare.add_trace(go.Scatter(
            x=years,
            y=results1["mean_cumulative"][:len(years)],
            mode='lines+markers',
            name='Szenario 1',
            line=dict(color='#E53935', width=3),
            marker=dict(size=8)
        ))
        
        fig_compare.add_trace(go.Scatter(
            x=years,
            y=results2["mean_cumulative"][:len(years)],
            mode='lines+markers',
            name='Szenario 2',
            line=dict(color='#00ACC1', width=3),
            marker=dict(size=8)
        ))
        
        # Add break-even line
        fig_compare.add_hline(y=0, line_dash="dash", line_color="gray",
                            annotation_text="Break-Even", annotation_position="left")
        
        fig_compare.update_layout(
            title="Szenarienvergleich: Kumulierter Nettoertrag<br><sub>Mit 3% jährlicher Diskontierung</sub>",
            xaxis_title="Jahre",
            yaxis_title="CHF (diskontiert)",
            template="plotly_white",
            height=450,
            hovermode='x unified'
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        # Side-by-side scenario details
        c1, c2 = st.columns(2)
        
        with c1:
            # Scenario 1 details
            st.markdown("### 📊 Szenario 1 Details")
            fig_s1 = go.Figure()
            fig_s1.add_trace(go.Scatter(
                x=years1,
                y=results1["mean_cumulative"],
                mode="lines+markers",
                name="Nettoertrag",
                line=dict(color="#E53935", width=2),
                fill='tonexty',
                fillcolor='rgba(229, 57, 53, 0.1)'
            ))
            fig_s1.add_trace(go.Scatter(
                x=years1,
                y=[-inv1] * len(years1),
                mode="lines",
                name="Investition",
                line=dict(color="#666666", width=1, dash="dot")
            ))
            fig_s1.update_layout(
                title="Szenario 1: Nettoertrag",
                xaxis_title="Jahre",
                yaxis_title="CHF",
                template="plotly_white",
                height=300
            )
            st.plotly_chart(fig_s1, use_container_width=True)
        
        with c2:
            # Scenario 2 details
            st.markdown("### 📊 Szenario 2 Details")
            fig_s2 = go.Figure()
            fig_s2.add_trace(go.Scatter(
                x=years2,
                y=results2["mean_cumulative"],
                mode="lines+markers",
                name="Nettoertrag",
                line=dict(color="#00ACC1", width=2),
                fill='tonexty',
                fillcolor='rgba(0, 172, 193, 0.1)'
            ))
            fig_s2.add_trace(go.Scatter(
                x=years2,
                y=[-inv2] * len(years2),
                mode="lines",
                name="Investition",
                line=dict(color="#666666", width=1, dash="dot")
            ))
            fig_s2.update_layout(
                title="Szenario 2: Nettoertrag",
                xaxis_title="Jahre",
                yaxis_title="CHF",
                template="plotly_white",
                height=300
            )
            st.plotly_chart(fig_s2, use_container_width=True)

        # Donor and revenue comparison
        col1, col2 = st.columns(2)
        
        with col1:
            # Donors comparison
            fig_d = go.Figure()
            fig_d.add_trace(go.Scatter(
                x=years,
                y=results1["yearly_donors"][:len(years)],
                mode="lines",
                name="SpenderInnen (S1)",
                line=dict(color="#E53935", width=2)
            ))
            fig_d.add_trace(go.Scatter(
                x=years,
                y=results2["yearly_donors"][:len(years)],
                mode="lines",
                name="SpenderInnen (S2)",
                line=dict(color="#00ACC1", width=2)
            ))
            fig_d.update_layout(
                title="Aktive SpenderInnen im Vergleich",
                xaxis_title="Jahre",
                yaxis_title="Anzahl SpenderInnen",
                template="plotly_white",
                height=300
            )
            st.plotly_chart(fig_d, use_container_width=True)
        
        with col2:
            # Revenue comparison
            fig_r = go.Figure()
            fig_r.add_trace(go.Bar(
                x=years,
                y=results1["yearly_revenue"][:len(years)],
                name="Ertrag (S1)",
                marker_color="#E53935",
                opacity=0.7
            ))
            fig_r.add_trace(go.Bar(
                x=years,
                y=results2["yearly_revenue"][:len(years)],
                name="Ertrag (S2)",
                marker_color="#00ACC1",
                opacity=0.7
            ))
            fig_r.update_layout(
                title="Jährliche Spendeneinnahmen im Vergleich",
                xaxis_title="Jahre",
                yaxis_title="CHF",
                template="plotly_white",
                height=300,
                barmode="group"
            )
            st.plotly_chart(fig_r, use_container_width=True)

        # Management summary
        with st.expander("📋 Entscheidungshilfe für Management"):
            st.markdown(f"""
            **Zusammenfassung der Analyse:**
            
            - **Schnellere Amortisation:** Szenario {1 if break1 < break2 else 2} amortisiert sich {abs(break1 - break2):.1f} Jahre schneller
            - **Höherer Kapitalwert:** Szenario {1 if net1 > net2 else 2} generiert CHF {abs(net1 - net2):,.0f} mehr Wert
            - **Bessere Rendite:** Szenario {1 if roi1 > roi2 else 2} hat {abs(roi1 - roi2):.0f}% höheren ROI
            
            **Empfehlung basierend auf Ihrer Situation:**
            
            🎯 **Bei knapper Liquidität:** Wählen Sie Szenario {1 if inv1 < inv2 else 2} (CHF {min(inv1, inv2):,.0f} Investition)
            
            💰 **Bei Fokus auf Rendite:** Wählen Sie Szenario {1 if net1 > net2 else 2} (CHF {max(net1, net2):,.0f} NPV)
            
            ⏱️ **Bei Zeitdruck:** Wählen Sie Szenario {1 if break1 < break2 else 2} ({min(break1, break2):.1f} Jahre Amortisation)
            """)
            
            # Add comparison table
            st.write("##### Detaillierter Vergleich")
            comparison_df = pd.DataFrame({
                "Metrik": ["Gesamtinvestition", "Kapitalwert (NPV)", "ROI", "Amortisation", "Gesamteinnahmen"],
                "Szenario 1": [
                    f"CHF {inv1:,.0f}",
                    f"CHF {net1:,.0f}",
                    f"{roi1:.0f}%",
                    f"{break1:.1f} Jahre",
                    f"CHF {total_rev1:,.0f}"
                ],
                "Szenario 2": [
                    f"CHF {inv2:,.0f}",
                    f"CHF {net2:,.0f}",
                    f"{roi2:.0f}%",
                    f"{break2:.1f} Jahre",
                    f"CHF {total_rev2:,.0f}"
                ],
                "Differenz": [
                    f"CHF {inv2-inv1:+,.0f}",
                    f"CHF {net2-net1:+,.0f}",
                    f"{roi2-roi1:+.0f}%",
                    f"{break2-break1:+.1f} Jahre",
                    f"CHF {total_rev2-total_rev1:+,.0f}"
                ]
            })
            
            # Style the comparison table
            def highlight_better(val):
                if isinstance(val, str) and val.startswith('+'):
                    return 'background-color: #C8E6C9'
                elif isinstance(val, str) and val.startswith('-'):
                    return 'background-color: #FFCDD2'
                return ''
            
            styled_comparison = comparison_df.style.applymap(highlight_better, subset=['Differenz'])
            st.dataframe(styled_comparison, use_container_width=True)

#####################################################################
# 6) NAVIGATION BACK TO HOME
#####################################################################
if st.session_state.page != "home":
    st.write("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🏠 Zurück zur Startseite", key="return_home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

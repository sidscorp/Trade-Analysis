import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import polars as pl
import s3fs

# Initialize the s3fs filesystem
fs = s3fs.S3FileSystem(anon=True)

from data_utils import load_trade_data, compute_metrics
from ai_utils import (
    generate_stakeholder_definition_prompt,
    generate_comprehensive_prompt,
    generate_targeted_followup_prompt,
    generate_disruption_prompt,
    run_llm_chain,
    get_response
)

from charts import (
    create_trade_trends_chart,
    create_top_suppliers_chart,
    create_trade_balance_chart,
    create_supply_chain_map,
    create_concentration_chart,
    create_metric_gauges
)

if os.path.exists(".env"):
    load_dotenv()  # Load from .env file in development
api_key = os.getenv('GOOGLE_API_KEY')  # get from environment in production
if api_key:
    genai.configure(api_key=api_key)

# Constants
bar_color = "#6c757d"
import_color = "#1f77b4"
export_color = "#ff7f0e"

# App configuration
st.set_page_config(page_title="Supply Chain Analysis", layout="wide", page_icon="🌐")

# Custom CSS
custom_css = """
<style>
.reportview-container .main .block-container {
    max-width: 95%;
    padding: 3rem;
}
h1, h2, h3, h4, h5, h6 {
    color: #2E86C1;
    font-weight: bold;
    margin-bottom: 0.8rem;
}
.stMetric {
    background-color: #EBF5FB;
    padding: 1.2rem;
    border-radius: 0.7rem;
    border: 1px solid #AED6F1;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease-in-out;
}
.stMetric:hover {
    transform: translateY(-3px);
}
.metric-label {
    font-size: 1.2rem;
    font-weight: 600;
    color: #34495E;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-size: 1.8rem;
    color: #1A5276;
}
.metric-delta {
    font-size: 1.1rem;
    color: #145A32;
}
.metric-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 160px;
}
.stButton>button {
    color: #fff;
    background-color: #2980B9;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.4rem;
    cursor: pointer;
    font-size: 1.1rem;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
    transition: background-color: 0.3s ease;
}
.stButton>button:hover {
    background-color: #1C648F;
}
.st-container {
    border: 1px solid #D4E6F1;
    border-radius: 0.6rem;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    background-color: #FBFCFC;
}
.stSelectbox>label, .stTextInput>label {
    font-weight: 500;
    color: #34495E;
}
.stSelectbox>div>div>div>input, .stTextInput>div>div>input {
    border: 1px solid #BDC3C7;
    border-radius: 0.4rem;
    padding: 0.4rem;
    font-size: 1rem;
}
.streamlit-expanderHeader {
    font-weight: 600;
    color: #2E86C1;
    border-bottom: 1px solid #AED6F1;
    padding-bottom: 0.6rem;
    margin-bottom: 0.7rem;
}
.stAlert {
    background-color: #E8F8F5;
    border-left: 5px solid #52BE80;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
}
.figure-insight {
    background-color: #F8F9FA;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
    border-left: 3px solid #2E86C1;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

def display_insight(title, content):
    """Display an insight with a title and content in a styled div"""
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="figure-insight">{content}</div>', unsafe_allow_html=True)

@st.cache_resource
def get_data(url1, url2):
    with fs.open(url1, mode='rb') as f:
        df1 = pl.scan_parquet(f)
    with fs.open(url2, mode='rb') as f:
        df2 = pl.read_parquet(f)
    return df1, df2

def main():
    """Main function containing the Streamlit app logic"""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("""
        ## 🌐 Supply Chain Intelligence Platform
        
        Welcome to your window into the global trade network! This interactive dashboard transforms complex trade data 
        into clear, actionable insights—whether you're a business leader, policy maker, or researcher. 
        
        Easily visualize where products come from, identify potential supply chain risks, and discover 
        alternative sourcing options before disruptions occur. Our analysis helps you:
        
        * **Identify vulnerabilities** in your supply chain network
        * **Assess concentration risks** from over-reliance on specific suppliers
        * **Simulate disruption scenarios** to test supply chain resilience
        * **Generate stakeholder-specific insights** tailored to your role
        """)

    with col2:
        st.markdown("""
        ### Data Sources
        
        This platform is powered by the **BACI Database** (Base pour l'Analyse du Commerce International), 
        a gold-standard trade dataset meticulously developed by CEPII research center. BACI harmonizes UN Comtrade 
        reports to create consistent bilateral trade flows, resolving common reporting discrepancies.
        
        * **Time Range:** 2018-2023
        * **Coverage:** 200+ countries and territories
        * **Resolution:** Country-to-country trade flows
        * **Products:** 5,000+ categories using HS codes
        """)

    # Replace the previous info box with a more visually distinctive element
    st.markdown("""
    <div style="background-color:#F0F7FF; padding:15px; border-radius:10px; border-left:5px solid #2E86C1; margin-bottom:20px">
    <h4 style="color:#2E86C1; margin-top:0">How to Use This Dashboard</h4>
    <p>1. Enter your <b>stakeholder role</b> (e.g., manufacturer, regulator, distributor)</p>
    <p>2. Search for a <b>product category</b> using common terms (e.g., "semiconductors", "steel", "medical devices")</p>
    <p>3. Click <b>Analyze</b> to generate visualizations and AI-powered insights specific to your context</p>
    <p>4. Explore the <b>Disruption Simulation</b> to test how your supply chain might respond to losing key suppliers</p>
    </div>
    """, unsafe_allow_html=True)
    # Load data
    full_parquet_path = "sidd-public-data/Processed Data/data_2014_2023.parquet"
    product_parquet_path = "sidd-public-data/Processed Data/products.parquet"
    trade_data, product_list = get_data(full_parquet_path, product_parquet_path)

    # show just one of the items in product_list
    
    
    # --- Input Form with Submit Button ---
    with st.form("data_selection_form"):
        st.subheader("⚙️ Data Selection")
        raw_stakeholder = st.text_input("Enter stakeholder role (e.g., manufacturers, federal government, etc.)", value="")
        stakeholder = raw_stakeholder if raw_stakeholder else "generic stakeholder"
        product_search_term = st.text_input("Search Product (e.g., steel)", key="product_search")
        submitted = st.form_submit_button("Analyze")

    if not submitted:
        st.write("Please submit the form to run the analysis.")
        return

    if not product_search_term:
        st.info("Please enter a product search term.")
        return
    st.write("Searching for products matching:", product_search_term)
    # --- Filter products based on the search term ---
    filtered_products = product_list.filter(
        pl.col("product_name").str.to_lowercase().str.contains(product_search_term.lower())
    )

    if filtered_products.is_empty():
        st.warning("No products found matching your search term.")
        return

    # --- Get ALL matching product codes ---
    product_codes = filtered_products["product_code"].to_list()

    # Time range settings
    current_year = 2023
    start_year = current_year - 5  # Past 5 Years
    end_year = current_year

    # --- Filter the trade data using the collected product codes ---
    df = trade_data.filter(
        (pl.col("product_code").is_in(product_codes)) & (pl.col("year").is_between(start_year, end_year))
    ).collect()

    if df.is_empty():
        st.error("No trade data available for the selected products and time period.")
        return

    # Calculate metrics and prepare data for visualization
    yearly_exports = (df.filter(pl.col("exporter") == "USA")
        .group_by("year")
        .agg(pl.col("value_1000usd").sum().alias("total_value"))
        .sort("year")
        .to_pandas())

    yearly_imports = (df.filter(pl.col("importer") == "USA")
        .group_by("year")
        .agg(pl.col("value_1000usd").sum().alias("total_value"))
        .sort("year")
        .to_pandas())

    yearly_trade = pd.merge(yearly_imports, yearly_exports, on="year", suffixes=("_imports", "_exports"), how="outer")
    yearly_trade["trade_balance"] = yearly_trade["total_value_exports"].fillna(0) - yearly_trade["total_value_imports"].fillna(0)

    top_us_suppliers = (df.filter(pl.col("importer") == "USA")
        .group_by("exporter")
        .agg(pl.col("value_1000usd").sum().alias("total_value"))
        .sort("total_value", descending=True)
        .head(10)
        .to_pandas())

    metrics = compute_metrics(df)
    
    # Initialize containers for LLM results
    analysis_json = None
    stakeholder_definition = {}
    
    # Run AI analysis if API key is available
    if api_key:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-002")
        
        # Define stakeholder context
        with st.spinner("Defining stakeholder context..."):
            stakeholder_prompt = generate_stakeholder_definition_prompt(product_search_term, stakeholder)
            stakeholder_definition = run_llm_chain(model, stakeholder_prompt)
            if "error" in stakeholder_definition:
                st.error("Stakeholder definition failed. Using generic analysis.")
                stakeholder_definition = {}

        # Display stakeholder context
        with st.container():
            st.subheader("Stakeholder Context")
            if stakeholder_definition:
                st.markdown(f"**Role:** {stakeholder_definition.get('role_description', 'N/A')}")
                st.markdown(f"**Key Interests:** {stakeholder_definition.get('key_interests', 'N/A')}")
                st.markdown(f"**Critical Uses of products related to '{product_search_term}':** {stakeholder_definition.get('critical_uses', 'N/A')}")
                st.markdown(f"**Supply Chain Vulnerabilities:** {stakeholder_definition.get('supply_chain_vulnerabilities', 'N/A')}")
                st.markdown(f"**Supply Chain Concerns:** {stakeholder_definition.get('supply_chain_concerns','N/A')}")
            else:
                st.markdown("No stakeholder context available.")
        
        # Generate comprehensive analysis
        with st.spinner("Generating comprehensive analysis..."):
            prompt = generate_comprehensive_prompt(metrics, product_search_term, "Past 5 Years", yearly_imports, yearly_exports, yearly_trade, top_us_suppliers, stakeholder_definition)
            try:
                response_text = get_response(model, prompt)
                analysis_json = json.loads(response_text)
            except (json.JSONDecodeError, Exception) as e:
                st.error(f"Error generating or parsing analysis: {e}")
                analysis_json = {  # Fallback
                    "trends_analysis": {"title": "Import/Export Trends", "content": "Analysis unavailable."},
                    "exporters_analysis": {"title": "Top Exporters", "content": "Analysis unavailable."},
                    "trade_balance_analysis": {"title": "Trade Balance", "content": "Analysis unavailable."},
                    "metrics_analysis": {"title": "Fragility Metrics", "content": "Analysis unavailable."}
                }
        
        # Generate targeted follow-up
        with st.spinner("Generating targeted follow-up..."):
            followup_prompt = generate_targeted_followup_prompt(analysis_json, stakeholder_definition)
            followup_json = run_llm_chain(model, followup_prompt)
            if "error" in followup_json:
                st.error("Targeted follow-up failed.")
                followup_json = {}
        
# Display market overview
    with st.container():
        st.subheader("📈 Market Overview")
        if analysis_json and 'trends_analysis' in analysis_json:
            display_insight(analysis_json['trends_analysis']['title'], analysis_json['trends_analysis']['content'])

        # Improved Trade trends chart
        fig_trends = create_trade_trends_chart(yearly_imports, yearly_exports, product_search_term)
        st.plotly_chart(fig_trends, use_container_width=True)

        # Two-column layout for exporters and trade balance
        col1, col2 = st.columns(2)
        with col1:
            if analysis_json and 'exporters_analysis' in analysis_json:
                display_insight(analysis_json['exporters_analysis']['title'], analysis_json['exporters_analysis']['content'])

            # Improved top suppliers chart
            fig_us = create_top_suppliers_chart(top_us_suppliers, product_search_term)
            st.plotly_chart(fig_us, use_container_width=True)

        with col2:
            if analysis_json and 'trade_balance_analysis' in analysis_json:
                display_insight(analysis_json['trade_balance_analysis']['title'], analysis_json['trade_balance_analysis']['content'])

            # Improved trade balance chart
            fig_trade_balance = create_trade_balance_chart(yearly_trade, product_search_term)
            st.plotly_chart(fig_trade_balance, use_container_width=True)

    # Display supply chain map
    with st.container():
        st.subheader("🌎 Geographic Supply Chain Analysis")
        # New supply chain map
        fig_map = create_supply_chain_map(top_us_suppliers, product_search_term)
        st.plotly_chart(fig_map, use_container_width=True)
        
    # Display supply chain metrics with improved gauges
    with st.container():
        st.subheader("⚖️ Supply Chain Fragility Metrics")
        
        # Create gauge charts
        risk_fig, diversity_fig, sub_fig = create_metric_gauges(metrics, product_search_term)
        
        # Display gauges in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(risk_fig, use_container_width=True)
        with col2:
            st.plotly_chart(diversity_fig, use_container_width=True)
        with col3:
            st.plotly_chart(sub_fig, use_container_width=True)

        if analysis_json and 'metrics_analysis' in analysis_json:
            display_insight(analysis_json['metrics_analysis']['title'], analysis_json['metrics_analysis']['content'])
if __name__ == "__main__":
    import polars as pl  # Import here to avoid circular imports
    main()
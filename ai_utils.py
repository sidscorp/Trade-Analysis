import json
import streamlit as st

def generate_stakeholder_definition_prompt(product_search_term, stakeholder):
    """Generate prompt to define stakeholder roles and concerns"""
    return f"""
    Define the role, interests, and potential concerns of a '{stakeholder}' in the context of the supply chain for products related to '{product_search_term}'. Return ONLY a JSON object.

    {{
        "role_description": "A concise description of the stakeholder's role.",
        "key_interests": "Stakeholder's primary interests related to the supply chain (e.g., cost, reliability, resilience, regulatory compliance).",
        "critical_uses": "Specific, critical ways the stakeholder uses products related to '{product_search_term}' in their operations (e.g., for medical devices: surgical instruments, implants, diagnostic equipment). Be very specific.",
        "supply_chain_vulnerabilities": "Specific vulnerabilities related to the supply chain of '{product_search_term}' that could directly impact the stakeholder, considering the 'critical_uses' (e.g., material shortages impacting implant production, quality inconsistencies affecting sterilization, regulatory changes affecting material sourcing).",
        "supply_chain_concerns": "List of concerns this stakeholder may have regarding supply chain disruptions or changes (e.g., maintaining quality control, reaching sustainability goals, adapting to new manufacturing, avoiding price volatility)."
    }}
    """

def generate_targeted_followup_prompt(initial_analysis_json, stakeholder_definition_json):
    """Generate prompt for targeted follow-up questions and next steps"""
    return f"""
    Given the initial supply chain analysis and stakeholder definition, identify key issues, formulate specific, *prioritized* questions (most important first), and suggest next steps. Return ONLY a JSON object.

    Initial Analysis:
    ```json
    {initial_analysis_json}
    ```

    Stakeholder Definition:
    ```json
    {stakeholder_definition_json}
    ```

    Desired JSON Output:
    {{
        "key_issues": [
            "Summary of key vulnerability/opportunity 1 (most important).",
            "Summary of key vulnerability/opportunity 2.",
            "Summary of key vulnerability/opportunity 3."
        ],
        "specific_questions": [
            "A specific, data-answerable question about issue 1.  Start with 'So what does this mean for...?' and relate it directly to the stakeholder's critical uses and vulnerabilities.",
            "A specific, data-answerable question about issue 2. Start with 'So what...?'",
            "A specific question about issue 3. Start with 'So what...?'"
        ],
        "next_steps": [
            "Concrete action to address issue 1.",
            "Concrete action to address issue 2.",
            "Concrete action to address issue 3."
        ]
    }}
    """

def generate_disruption_prompt(metrics, disrupted_metrics, supplier_to_remove, product_search_term, top_supplier_value, top_supplier_share, stakeholder_definition):
    """Generate prompt for disruption analysis"""
    risk_change = disrupted_metrics['risk_score'] - metrics['risk_score']
    concentration_change = disrupted_metrics['top_3_concentration'] - metrics['top_3_concentration']

    return f"""
    Analyze the supply chain disruption and its impact *specifically on the defined stakeholder*. Return ONLY a JSON object.
    Stakeholder Definition:
    ```json
    {stakeholder_definition}
    ```

    Desired JSON Structure:
    {{
        "title": "Disruption Analysis: Impact of Removing {supplier_to_remove} on {stakeholder_definition.get('role_description', 'the stakeholder')}",
        "content": "Two paragraphs (6+ sentences each). Focus on the *stakeholder-specific* impacts, considering their 'critical_uses' and 'vulnerabilities'.",
        "risk_assessment": "One paragraph (3-4 sentences) analyzing risk score change *for the stakeholder*.",
        "concentration_assessment": "One paragraph (3-4 sentences) analyzing supplier concentration changes *for the stakeholder*.",
        "resilience_assessment": "One paragraph (3-4 sentences) on resilience, with *stakeholder-specific* mitigation suggestions."
    }}

    DISRUPTION DATA:
    - Product: Products related to {product_search_term}
    - Supplier Removed: {supplier_to_remove} (${top_supplier_value:.1f}K, {top_supplier_share:.1f}% share)

    BASE METRICS (BEFORE):
    - Risk Score: {metrics['risk_score']:.0f}/100
    - Diversity Score: {metrics['diversity_score']:.0f}/100
    - Substitutability: {metrics['substitutability']:.0f}/100
    - Top Supplier Share: {metrics['top_supplier_share']:.1f}%
    - Top 3 Concentration: {metrics['top_3_concentration']:.1f}%
    - Supplier Count: {metrics['num_suppliers']}
    - US Market Share: {metrics['us_market_share']:.1f}%
    - Trade Balance: ${metrics['trade_balance']:.1f}K

    DISRUPTED METRICS (AFTER):
    - Risk Score: {disrupted_metrics['risk_score']:.0f}/100 ({risk_change:+.1f})
    - Diversity Score: {disrupted_metrics['diversity_score']:.0f}/100 ({disrupted_metrics['diversity_score'] - metrics['diversity_score']:+.1f})
    - Substitutability: {disrupted_metrics['substitutability']:.0f}/100 ({disrupted_metrics['substitutability'] - metrics['substitutability']:+.1f})
    - Top Supplier Share: {disrupted_metrics['top_supplier_share']:.1f}% ({disrupted_metrics['top_supplier_share'] - metrics['top_supplier_share']:+.1f}%)
    - Top 3 Concentration: {disrupted_metrics['top_3_concentration']:.1f}% ({concentration_change:+.1f}%)
    - Supplier Count: {disrupted_metrics['num_suppliers']} ({disrupted_metrics['num_suppliers'] - metrics['num_suppliers']:+d})
    - US Market Share: {disrupted_metrics['us_supplier_count']:.1f}% ({disrupted_metrics['us_supplier_count'] - metrics['us_market_share']:+.1f}%)
    - Trade Balance: ${disrupted_metrics['trade_balance']:.1f}K ({disrupted_metrics['trade_balance'] - metrics['trade_balance']:+.1f}K)
    """

def run_llm_chain(model, prompt):
    """Process prompt with LLM and return JSON result"""
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(response_text)
    except (json.JSONDecodeError, Exception) as e:
        st.error(f"LLM Error: {type(e).__name__} - {e}")
        return {"error": "Failed to generate or parse LLM response."}

def get_response(model, prompt):
    """Get raw text response from LLM and clean it"""
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    return response_text


@st.cache_data
def generate_comprehensive_prompt(metrics, product_search_term, time_range, yearly_imports, yearly_exports, yearly_trade, top_us_suppliers, stakeholder_definition):
    """Generate a prompt for comprehensive supply chain analysis"""
    risk_level = "Low" if metrics['risk_score'] >= 80 else "Moderate" if metrics['risk_score'] >= 60 else "High"
    total_imports = yearly_imports['total_value'].sum()
    total_exports = yearly_exports['total_value'].sum()
    max_import_year = yearly_imports.loc[yearly_imports['total_value'].idxmax()]['year'] if not yearly_imports.empty else "N/A"
    max_import_value = yearly_imports['total_value'].max() if not yearly_imports.empty else 0

    top_exporter = top_us_suppliers.iloc[0]['exporter'] if not top_us_suppliers.empty else "N/A"
    top_value = top_us_suppliers.iloc[0]['total_value'] if not top_us_suppliers.empty else 0
    top_3_share = (top_us_suppliers.head(3)['total_value'].sum() / top_us_suppliers['total_value'].sum() * 100) if not top_us_suppliers.empty else 0

    min_year = yearly_trade['trade_balance'].idxmin() if not yearly_trade.empty else "N/A"
    min_value = yearly_trade.loc[min_year, 'trade_balance'] if not yearly_trade.empty and min_year != "N/A" else 0
    avg_balance = yearly_trade['trade_balance'].mean() if not yearly_trade.empty else 0
    latest_year_trend = "improving" if not yearly_trade.empty and len(yearly_trade) > 1 and yearly_trade['trade_balance'].iloc[-1] > yearly_trade['trade_balance'].iloc[-2] else "worsening"

    system_instruction = f"""
    You are a seasoned supply chain risk consultant. Analyze the data and provide insights *directly relevant* to the defined stakeholder, {stakeholder_definition.get('role_description', 'the stakeholder')}.  Consider industry-specific factors.

    Stakeholder Definition:
    ```json
    {stakeholder_definition}
    ```

    Your analysis MUST connect the data to the stakeholder's 'critical_uses' and 'supply_chain_vulnerabilities' as defined above.
    """

    return f"""
    {system_instruction}

    Analyze supply chain data and return *ONLY* a JSON object:

    ```json
    {{
        "trends_analysis": {{
            "title": "Import/Export Trends Analysis",
            "content": "Two paragraphs (6+ sentences each) analyzing trends.  *Directly* connect the data to the stakeholder's critical uses and vulnerabilities. Quantify the impact whenever possible."
        }},
        "exporters_analysis": {{
            "title": "Top Exporters Analysis",
            "content": "Two paragraphs (6+ sentences each) analyzing top exporters.  *Directly* connect to stakeholder concerns. Quantify risks."
        }},
        "trade_balance_analysis": {{
            "title": "Trade Balance Analysis",
            "content": "Two paragraphs (6+ sentences each). Connect trade balance trends to stakeholder's interests (e.g., cost, profitability). Quantify."
        }},
        "metrics_analysis": {{
            "title": "Supply Chain Fragility Metrics Analysis",
            "content": "Two paragraphs (6+ sentences). Analyze metrics and provide *actionable recommendations*, specifically for the stakeholder, considering their defined vulnerabilities. Quantify."
        }}
    }}
    ```

    DATA FOR ANALYSIS:

    1.  PRODUCT INFORMATION:
        -   Product: Products related to {product_search_term}
        -   Time Period: {time_range}

    2.  TRADE TRENDS:
        -   Total US Imports: ${total_imports:.1f}K
        -   Total US Exports: ${total_exports:.1f}K
        -   Peak Import Year: {max_import_year} (${max_import_value:.1f}K)
        -   Trade Balance: ${total_imports - total_exports:.1f}K
        -   Years Covered: {yearly_imports['year'].min() if not yearly_imports.empty else 'N/A'} to {yearly_imports['year'].max() if not yearly_imports.empty else 'N/A'}

    3.  TOP EXPORTERS TO US:
        -   Leading Exporter: {top_exporter} (${top_value:.1f}K)
        -   Top 3 Exporters: {top_3_share:.1f}% of total imports
        -   Total Suppliers: {metrics['num_suppliers']}

    4.  TRADE BALANCE METRICS:
        -   Average Balance: ${avg_balance:.1f}K
        -   Largest Deficit Year: {min_year} (${min_value:.1f}K)
        -   Recent Trend: {latest_year_trend}

    5.  SUPPLY CHAIN METRICS:
        -   Risk Score: {metrics['risk_score']:.0f}/100 ({risk_level} Risk)
        -   Top Supplier Share: {metrics['top_supplier_share']:.1f}%
        -   Top 3 Concentration: {metrics['top_3_concentration']:.1f}%
        -   Supplier Count: {metrics['num_suppliers']} suppliers from {metrics['global_supplier_count']} global options
        -   Diversity Score: {metrics['diversity_score']:.1f}/100
        -   Substitutability: {metrics['substitutability']:.1f}/100
        -   Top Export Countries: {', '.join(metrics['top_exporters'][:3])}
        -   Top Import Countries: {', '.join(metrics['top_importers'][:3])}
        -   US Market Share: {metrics['us_market_share']:.1f}%
        -   YoY Growth Rate: {metrics['yoy_growth']:.1f}%
    """
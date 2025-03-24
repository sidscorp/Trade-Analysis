# Supply Chain Intelligence Platform

## Overview

The Supply Chain Intelligence Platform is an interactive dashboard that transforms complex global trade data into actionable insights. It helps businesses, policy makers, and researchers visualize supply chains, identify vulnerabilities, assess concentration risks, and simulate disruption scenarios.

## Features

* **Interactive Visualizations** : Explore trade flows, supplier concentrations, and geographic distributions
* **Risk Assessment** : Measure supply chain risk, diversity, and substitutability metrics
* **Stakeholder-Specific Analysis** : Tailor insights to different roles (manufacturers, regulators, etc.)
* **Disruption Simulation** : Test the resilience of supply chains by removing key suppliers
* **AI-Powered Insights** : Get contextual analysis generated via large language models

## Data Source

This platform uses the BACI Database (Base pour l'Analyse du Commerce International) developed by CEPII research center, which harmonizes UN Comtrade reports to create consistent bilateral trade flows.

* **Time Range** : 2018-2023
* **Coverage** : 200+ countries and territories
* **Resolution** : Country-to-country trade flows
* **Products** : 5,000+ categories using HS codes

## Installation

### Prerequisites

* Python 3.8+
* pip

### Dependencies

```bash
pip install streamlit plotly pandas polars numpy google-generativeai python-dotenv s3fs
```

### Configuration

1. Create a `.env` file in the project root
2. Add your Google API key: `GOOGLE_API_KEY=your_api_key_here`

### Data Setup

1. Download the BACI dataset from [CEPII&#39;s website](https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS92_V202501.zip)
2. Extract the contents to a folder named `Data/BACI_Full` in your project directory
3. Run the data preparation script:

```bash
python generate_input_data.py
```

4. This will create processed data files in the `Processed Data` directory

 **Note** : The current version of the app uses pre-processed data from an S3 bucket. The steps above are only needed if you want to process the raw data yourself.

## Usage

1. Run the application:

```bash
streamlit run main.py
```

2. Enter your stakeholder role (e.g., manufacturer, regulator, distributor)
3. Search for a product category using common terms (e.g., "semiconductors", "steel")
4. Click "Analyze" to generate visualizations and insights
5. Explore the Disruption Simulation to test supply chain resilience

## Project Structure

* `main.py`: The main Streamlit application
* `ai_utils.py`: Functions for generating prompts and handling AI responses
* `charts.py`: Visualization functions using Plotly
* `data_utils.py`: Data processing and metric calculation functions
* `generate_input_data.py`: Data preparation and transformation script

## Metrics Explained

* **Risk Score** : Overall supply chain risk based on supplier concentration (higher is better)
* **Diversity Score** : Measurement of supplier variety (higher is better)
* **Substitutability** : Ease of finding alternative suppliers (higher is better)
* **Top Supplier Share** : Percentage of imports from the largest supplier
* **Top 3 Concentration** : Percentage of imports from the three largest suppliers

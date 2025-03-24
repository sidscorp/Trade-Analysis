import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go



def create_concentration_chart(top_suppliers, product_name):
    # Calculate cumulative percentage
    suppliers_df = top_suppliers.copy()
    suppliers_df = suppliers_df.sort_values('total_value', ascending=False)
    total = suppliers_df['total_value'].sum()
    suppliers_df['percentage'] = suppliers_df['total_value'] / total * 100
    suppliers_df['cumulative'] = suppliers_df['percentage'].cumsum()
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for individual percentages
    fig.add_trace(
        go.Bar(
            x=suppliers_df['exporter'],
            y=suppliers_df['percentage'],
            name='% of Total Imports',
            marker_color='rgba(58, 71, 80, 0.6)',
            opacity=0.7,
            hovertemplate='<b>%{x}</b><br>%{y:.1f}% of total imports<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Add line chart for cumulative percentage
    fig.add_trace(
        go.Scatter(
            x=suppliers_df['exporter'],
            y=suppliers_df['cumulative'],
            name='Cumulative %',
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>'
        ),
        secondary_y=True
    )
    
    # Add annotations for key thresholds
    suppliers_80 = suppliers_df[suppliers_df['cumulative'] >= 80].iloc[0]
    
    fig.add_shape(
        type="line",
        x0=suppliers_df['exporter'].iloc[0],
        x1=suppliers_80['exporter'],
        y0=80,
        y1=80,
        line=dict(color="red", width=1, dash="dash"),
        secondary_y=True
    )
    
    fig.add_annotation(
        x=suppliers_df['exporter'].iloc[0],
        y=80,
        text="80% of imports",
        textangle=0,
        xshift=-5,
        yshift=10,
        showarrow=False,
        font=dict(size=10, color="red"),
        secondary_y=True
    )
    
    # Calculate the number of suppliers that make up 80% of imports
    count_80 = suppliers_df[suppliers_df['cumulative'] <= 80].shape[0] + 1
    
    # Update layout
    fig.update_layout(
        title=f"Supply Concentration Analysis for {product_name}",
        title_font=dict(size=16),
        xaxis_title="Supplier Countries",
        yaxis_title="% of Total Imports",
        yaxis2_title="Cumulative %",
        xaxis=dict(
            showgrid=False,
            tickangle=-45,
            categoryorder='total descending'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.8)',
            ticksuffix="%"
        ),
        yaxis2=dict(
            showgrid=False,
            ticksuffix="%",
            range=[0, 105]
        ),
        plot_bgcolor='rgba(255,255,255,0.9)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=60, t=80, b=100),
        height=450,
    )
    
    # Add annotation explaining concentration
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.01,
        text=f"{count_80} suppliers represent 80% of total imports",
        showarrow=False,
        font=dict(size=12, color="#333"),
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        borderwidth=1,
        borderpad=4,
        align="left"
    )
    
    # Add source annotation
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=-0.15,
        text="Source: BACI Database (CEPII research center)",
        showarrow=False,
        font=dict(size=10, color="#666666"),
        align="left"
    )
    
    return fig



def create_supply_chain_map(top_suppliers, product_name):
    # Create a dataframe for the map
    map_data = top_suppliers.copy()
    
    # Create a choropleth map
    fig = go.Figure(data=go.Choropleth(
        locations=map_data['exporter'],  # country codes
        z=map_data['total_value'],  # values to color by
        locationmode='ISO-3',
        colorscale='Blues',
        colorbar_title='Import Value<br>($Millions)',
        colorbar=dict(
            tickprefix='$',
            ticksuffix='M',
            tickformat='.1f'
        ),
        hovertemplate='<b>%{location}</b><br>Import Value: $%{z:.1f}M<extra></extra>'
    ))
    
    # Add a trace for the USA (the importer)
    fig.add_trace(go.Choropleth(
        locations=['USA'],
        z=[1],  # value doesn't matter, just to highlight
        locationmode='ISO-3',
        colorscale=[[0, 'rgba(255,77,77,0.8)'], [1, 'rgba(255,77,77,0.8)']],
        showscale=False,
        hovertemplate='<b>United States</b><br>Primary Importer<extra></extra>'
    ))
    
    # Add arcs connecting suppliers to the USA
    for idx, row in map_data.iterrows():
        # Get coordinates (this would need a mapping of country codes to coordinates)
        # For simplicity, this example uses dummy coordinates
        # In a real implementation, you would need a proper coordinate lookup
        start_lat, start_lon = 38.8833, -77.0167  # Washington DC (USA)
        end_lat, end_lon = 0, 0  # This would come from a country coordinate lookup
        
        fig.add_trace(go.Scattergeo(
            locationmode='ISO-3',
            lon=[start_lon, end_lon],
            lat=[start_lat, end_lat],
            mode='lines',
            line=dict(width=1, color='red'),
            opacity=0.5,
            showlegend=False
        ))
    
    fig.update_layout(
        title_text=f'Global Supply Chain Map for {product_name}',
        title_font=dict(size=16),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        height=500,
    )
    
    # Add a source note
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.01,
        text="Source: BACI Database (CEPII research center)",
        showarrow=False,
        font=dict(size=10, color="#666666"),
        align="left"
    )
    
    return fig



def create_metric_gauges(metrics, product_name):
    # Create gauge charts for each metric
    risk_colors = ['#2ECC71', '#F1C40F', '#E74C3C']  # Green, Yellow, Red
    
    # Supply Chain Risk Gauge
    risk_fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=metrics['risk_score'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Supply Chain Risk Score", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': risk_colors[2]},  # High risk (red)
                {'range': [60, 80], 'color': risk_colors[1]},  # Moderate risk (yellow)
                {'range': [80, 100], 'color': risk_colors[0]},  # Low risk (green)
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': metrics['risk_score']
            }
        },
        delta={'reference': 75, 'increasing': {'color': 'green'}, 'decreasing': {'color': 'red'}}
    ))
    
    risk_status = "Low" if metrics['risk_score'] >= 80 else "Moderate" if metrics['risk_score'] >= 60 else "High"
    risk_fig.add_annotation(
        x=0.5,
        y=0.25,
        text=f"Status: {risk_status}",
        showarrow=False,
        font=dict(size=14)
    )
    
    risk_fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    # Network Diversity Gauge
    diversity_fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=metrics['diversity_score'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Network Diversity Score", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': risk_colors[2]},  # Weak (red)
                {'range': [40, 70], 'color': risk_colors[1]},  # Moderate (yellow)
                {'range': [70, 100], 'color': risk_colors[0]},  # Strong (green)
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': metrics['diversity_score']
            }
        },
        delta={'reference': 60, 'increasing': {'color': 'green'}, 'decreasing': {'color': 'red'}}
    ))
    
    diversity_status = "Strong" if metrics['diversity_score'] >= 70 else "Moderate" if metrics['diversity_score'] >= 40 else "Weak"
    diversity_fig.add_annotation(
        x=0.5,
        y=0.25,
        text=f"Status: {diversity_status}",
        showarrow=False,
        font=dict(size=14)
    )
    
    diversity_fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    # Substitutability Gauge
    sub_fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=metrics['substitutability'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Global Substitutability Score", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': risk_colors[2]},  # Weak (red)
                {'range': [40, 70], 'color': risk_colors[1]},  # Moderate (yellow)
                {'range': [70, 100], 'color': risk_colors[0]},  # Strong (green)
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': metrics['substitutability']
            }
        },
        delta={'reference': 65, 'increasing': {'color': 'green'}, 'decreasing': {'color': 'red'}}
    ))
    
    sub_status = "Strong" if metrics['substitutability'] >= 70 else "Moderate" if metrics['substitutability'] >= 40 else "Weak"
    sub_fig.add_annotation(
        x=0.5,
        y=0.25,
        text=f"Status: {sub_status}",
        showarrow=False,
        font=dict(size=14)
    )
    
    sub_fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    return risk_fig, diversity_fig, sub_fig



def create_trade_balance_chart(yearly_trade, product_name):
    # Create figure with secondary y-axis
    fig_trade_balance = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Fill in any missing years with zeroes
    yearly_trade = yearly_trade.fillna(0)
    import_color = 'rgba(31, 119, 180, 0.6)'  # Blue
    export_color = 'rgba(255, 127, 14, 0.6)'  # Orange
    # Add imports and exports lines (secondary y-axis)
    fig_trade_balance.add_trace(
        go.Scatter(
            x=yearly_trade['year'],
            y=yearly_trade['total_value_imports'],
            mode='lines',
            name='Imports',
            line=dict(color=import_color, width=1.5, dash='dot'),
            opacity=0.7
        ),
        secondary_y=True
    )
    
    fig_trade_balance.add_trace(
        go.Scatter(
            x=yearly_trade['year'],
            y=yearly_trade['total_value_exports'],
            mode='lines',
            name='Exports',
            line=dict(color=export_color, width=1.5, dash='dot'),
            opacity=0.7
        ),
        secondary_y=True
    )
    
    # Define colors based on values (red for deficit, green for surplus)
    colors = ['rgba(255,0,0,0.7)' if val < 0 else 'rgba(0,128,0,0.7)' for val in yearly_trade['trade_balance']]
    
    # Add colored area under the trade balance line
    for i in range(len(yearly_trade) - 1):
        fig_trade_balance.add_shape(
            type="rect",
            x0=yearly_trade['year'].iloc[i],
            x1=yearly_trade['year'].iloc[i+1],
            y0=0,
            y1=yearly_trade['trade_balance'].iloc[i],
            fillcolor=colors[i],
            opacity=0.3,
            layer="below",
            line_width=0,
        )
    
    # Add trade balance line (primary y-axis)
    fig_trade_balance.add_trace(
        go.Scatter(
            x=yearly_trade['year'],
            y=yearly_trade['trade_balance'],
            mode='lines+markers',
            name='Trade Balance',
            line=dict(color='black', width=2),
            marker=dict(size=8, color=colors, line=dict(width=1, color='black')),
        ),
        secondary_y=False
    )
    
    # Add zero reference line
    fig_trade_balance.add_shape(
        type="line",
        x0=min(yearly_trade['year']),
        y0=0,
        x1=max(yearly_trade['year']),
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
    )
    
    # Calculate linear trend for trade balance
    x = yearly_trade['year'].values
    y = yearly_trade['trade_balance'].values
    coeffs = np.polyfit(x, y, 1)
    trend_line = np.poly1d(coeffs)
    
    # Add trend line
    trend_x = np.linspace(min(x), max(x), 100)
    trend_y = trend_line(trend_x)
    
    fig_trade_balance.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode='lines',
            name='Trend',
            line=dict(color='rgba(0,0,0,0.5)', width=1.5, dash='dashdot'),
            showlegend=True
        ),
        secondary_y=False
    )
    
    # Annotate the trend direction
    trend_direction = "Improving" if coeffs[0] > 0 else "Worsening"
    trend_color = "green" if coeffs[0] > 0 else "red"
    
    fig_trade_balance.add_annotation(
        x=max(yearly_trade['year']),
        y=trend_line(max(yearly_trade['year'])),
        text=f"Balance {trend_direction}",
        showarrow=True,
        arrowhead=1,
        arrowsize=1,
        arrowwidth=1,
        arrowcolor=trend_color,
        font=dict(color=trend_color),
        xshift=10,
        yshift=10
    )
    
    # Format axis labels and layout
    fig_trade_balance.update_layout(
        title=f"{product_name} Trade Balance (2018-2023)",
        title_font=dict(size=16),
        xaxis_title="Year",
        yaxis_title="Trade Balance ($ Millions)",
        yaxis2_title="Import/Export Value ($ Millions)",
        xaxis=dict(
            showgrid=False,
            tickangle=-45,
            dtick=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.8)',
            tickprefix="$",
            ticksuffix="M",
            tickformat=",.1f",
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        yaxis2=dict(
            showgrid=False,
            tickprefix="$",
            ticksuffix="M",
            tickformat=",.1f"
        ),
        plot_bgcolor='rgba(255,255,255,0.9)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        margin=dict(t=80, b=80, l=80, r=80),
        height=450,
    )
    
    # Add a source note
    fig_trade_balance.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.15,
        text="Source: BACI Database (CEPII research center)",
        showarrow=False,
        font=dict(size=10, color="#666666"),
        align="left"
    )
    
    return fig_trade_balance




def create_top_suppliers_chart(top_us_suppliers, product_name):
    # Calculate total value and percentages
    total_imports = top_us_suppliers['total_value'].sum()
    top_us_suppliers = top_us_suppliers.copy()
    top_us_suppliers['percentage'] = (top_us_suppliers['total_value'] / total_imports * 100).round(1)
    
    # Sort by value descending
    top_us_suppliers = top_us_suppliers.sort_values('total_value', ascending=True)
    
    # Generate color gradient based on concentration (darker = higher concentration)
    max_pct = top_us_suppliers['percentage'].max()
    colors = [f'rgba(31, 119, 180, {0.4 + (0.6 * (pct/max_pct))})' for pct in top_us_suppliers['percentage']]
    
    # Create horizontal bar chart
    fig_us = go.Figure()
    
    fig_us.add_trace(go.Bar(
        y=top_us_suppliers['exporter'],
        x=top_us_suppliers['total_value'],
        orientation='h',
        marker_color=colors,
        text=[f"${val/1000:.1f}M ({pct}%)" for val, pct in zip(top_us_suppliers['total_value'], top_us_suppliers['percentage'])],
        textposition='outside',
        hoverinfo='text',
        hovertext=[f"{country}: ${val/1000:.1f}M<br>{pct}% of imports" 
                  for country, val, pct in zip(top_us_suppliers['exporter'], 
                                              top_us_suppliers['total_value'], 
                                              top_us_suppliers['percentage'])]
    ))
    
    # Calculate the Herfindahl-Hirschman Index (HHI) for concentration
    hhi = ((top_us_suppliers['percentage'] / 100) ** 2).sum() * 10000
    concentration_level = "High" if hhi > 2500 else "Moderate" if hhi > 1500 else "Low"
    
    # Update layout with improved styling
    fig_us.update_layout(
        title=f"Top Suppliers of {product_name} to the U.S.",
        title_font=dict(size=16),
        xaxis_title="Import Value ($ Millions)",
        yaxis_title=None,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.8)',
            tickprefix="$",
            ticksuffix="M",
            tickformat=".1f"
        ),
        yaxis=dict(
            showgrid=False,
            autorange="reversed"  # Important for horizontal bar charts
        ),
        plot_bgcolor='rgba(255,255,255,0.9)',
        height=400,
        margin=dict(l=120, r=120, t=80, b=80),
    )
    
    # Add annotation for concentration level
    fig_us.add_annotation(
        xref="paper",
        yref="paper",
        x=1,
        y=1.05,
        text=f"Supplier Concentration: {concentration_level} (HHI: {hhi:.0f})",
        showarrow=False,
        font=dict(size=12),
        align="right",
        bgcolor='rgba(240, 240, 240, 0.8)',
        bordercolor='rgba(0,0,0,0.1)',
        borderwidth=1,
        borderpad=4
    )
    
    # Add source annotation
    fig_us.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.15,
        text="Source: BACI Database (CEPII research center)",
        showarrow=False,
        font=dict(size=10, color="#666666"),
        align="left"
    )
    
    return fig_us



def create_trade_trends_chart(yearly_imports, yearly_exports, product_name):
    fig_trends = go.Figure()
    
    # Calculate mean values for reference lines
    mean_imports = yearly_imports['total_value'].mean()
    mean_exports = yearly_exports['total_value'].mean()
    import_color = 'rgba(31, 119, 180, 0.6)'  # Blue
    export_color = 'rgba(255, 127, 14, 0.6)'  # Orange
    # Add import bars
    fig_trends.add_trace(go.Bar(
        x=yearly_imports['year'], 
        y=yearly_imports['total_value'], 
        name='U.S. Imports', 
        marker_color=import_color,
        text=[f"${val/1000:.1f}M" for val in yearly_imports['total_value']],
        textposition='outside',
        width=0.4,
        offset=-0.2
    ))
    
    # Add export bars
    fig_trends.add_trace(go.Bar(
        x=yearly_exports['year'], 
        y=yearly_exports['total_value'], 
        name='U.S. Exports', 
        marker_color=export_color,
        text=[f"${val/1000:.1f}M" for val in yearly_exports['total_value']],
        textposition='outside',
        width=0.4,
        offset=0.2
    ))
    
    # Add reference lines for averages
    fig_trends.add_shape(
        type="line",
        x0=min(yearly_imports['year']),
        y0=mean_imports,
        x1=max(yearly_imports['year']),
        y1=mean_imports,
        line=dict(color=import_color, width=1, dash="dot"),
    )
    
    fig_trends.add_shape(
        type="line",
        x0=min(yearly_exports['year']),
        y0=mean_exports,
        x1=max(yearly_exports['year']),
        y1=mean_exports,
        line=dict(color=export_color, width=1, dash="dot"),
    )
    
    # Add annotations for the reference lines
    fig_trends.add_annotation(
        x=min(yearly_imports['year']),
        y=mean_imports,
        xshift=-10,
        text=f"Avg Imports: ${mean_imports/1000:.1f}M",
        showarrow=False,
        font=dict(size=10, color=import_color)
    )
    
    fig_trends.add_annotation(
        x=min(yearly_exports['year']),
        y=mean_exports,
        xshift=-10,
        yshift=20,
        text=f"Avg Exports: ${mean_exports/1000:.1f}M",
        showarrow=False,
        font=dict(size=10, color=export_color)
    )
    
    # Highlight notable year with annotation if applicable
    # (this would be dynamically determined based on data)
    max_import_year = yearly_imports.loc[yearly_imports['total_value'].idxmax(), 'year']
    max_import_value = yearly_imports['total_value'].max()
    
    fig_trends.add_annotation(
        x=max_import_year,
        y=max_import_value,
        text="Peak Imports",
        yshift=15,
        showarrow=True,
        arrowhead=1,
        arrowsize=1,
        arrowwidth=1,
        arrowcolor="#666666"
    )
    
    # Update layout with improved styling
    fig_trends.update_layout(
        title=f"{product_name} Trade Flows (2018-2023)",
        title_font=dict(size=18),
        xaxis_title="Year",
        yaxis_title="Trade Value ($ Millions)",
        xaxis=dict(
            showgrid=False,
            tickangle=-45,
            dtick=1  # Ensure all years are shown
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.8)',
            tickprefix="$",
            ticksuffix="M",
            tickformat=",.1f"
        ),
        plot_bgcolor='rgba(255,255,255,0.9)',
        barmode='group',
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        margin=dict(t=100, b=100, l=80, r=80),
        height=500,
    )
    
    # Add a source note at the bottom
    fig_trends.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=-0.15,
        text="Source: BACI Database (CEPII research center)",
        showarrow=False,
        font=dict(size=10, color="#666666"),
        align="left"
    )
    
    return fig_trends
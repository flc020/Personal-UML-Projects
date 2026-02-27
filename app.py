from datetime import datetime
from pathlib import Path
from state_choices import STATE_CHOICES

from shiny import reactive
from shiny.express import input, render, ui

from faicons import icon_svg
from shinywidgets import render_plotly

import pandas as pd
import plotly.express as px

# Read file
newListings = pd.read_csv(Path(__file__).parent / "Metro_new_listings_uc_sfrcondo_sm_month.csv")
medianListPrice = pd.read_csv(Path(__file__).parent / "Metro_mlp_uc_sfrcondo_sm_month.csv")
saleInventory = pd.read_csv(Path(__file__).parent / "Metro_invt_fs_uc_sfrcondo_sm_month.csv")


forecast_mfr = pd.read_csv(Path(__file__).parent/"National_zorf_growth_uc_mfr_sm_month.csv")
forecast_sfr = pd.read_csv(Path(__file__).parent/"National_zorf_growth_uc_sfr_sm_month.csv")

# provided by a Udemy instructor
ui.head_content(
    ui.tags.link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap",
    ),
    ui.tags.style(
        """
:root {
  --bg: #f4f1ec;
  --panel: #ffffff;
  --panel-2: #fbf8f2;
  --accent: #0f766e;
  --accent-2: #b45309;
  --text: #1f2937;
  --muted: #6b7280;
  --border: #e6dfd5;
  --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  --radius: 16px;
}

body {
  font-family: "IBM Plex Sans", system-ui, -apple-system, Segoe UI, sans-serif;
  color: var(--text);
  background: radial-gradient(1200px 600px at 10% -10%, #fff 0%, #f6f1ea 45%, #efe7dd 100%);
}

.container-fluid {
  padding: 1.5rem 2rem 2.5rem;
}

.bslib-sidebar-layout {
  gap: 1.25rem;
}

.bslib-sidebar-layout .sidebar,
.bslib-sidebar-layout > .sidebar,
.sidebar {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}

.value-box,
.value-box-compact {
  background: linear-gradient(135deg, var(--panel) 0%, var(--panel-2) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.value-box .value-box-title,
.value-box .value-box-title span {
  color: var(--muted);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-size: 0.72rem;
}

.value-box .value-box-value {
  font-size: 1.8rem;
  font-weight: 700;
}

.card,
.navset-card-underline,
.bslib-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.navset-card-underline .nav-link {
  color: var(--muted);
  font-weight: 600;
}

.navset-card-underline .nav-link.active {
  color: var(--accent);
  border-bottom: 2px solid var(--accent);
}

.form-control,
.selectize-input,
.selectize-control.single .selectize-input {
  border-radius: 12px;
  border-color: var(--border);
  box-shadow: none;
}

.selectize-input.focus,
.form-control:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.15);
}

.irs--shiny .irs-bar,
.irs--shiny .irs-single,
.irs--shiny .irs-from,
.irs--shiny .irs-to {
  background: var(--accent);
}

.irs--shiny .irs-handle {
  border: 2px solid var(--accent);
}

table.dataframe,
.table {
  color: var(--text);
}

table.dataframe th,
.table thead th {
  background: var(--panel-2);
  border-color: var(--border);
  font-weight: 600;
}

table.dataframe td,
.table td {
  border-color: var(--border);
}

@media (max-width: 768px) {
  .container-fluid {
    padding: 1rem;
  }
}
"""
    ),
)


# Helper functions
def string_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def filter_by_date(df: pd.DataFrame, date_range: tuple):
    rng = sorted(date_range)
    dates = pd.to_datetime(df["Date"], format = "%Y-%m-%d").dt.date
    return df[(dates >= rng[0]) & (dates <= rng[1])]
 
# Visual spaghetti 

#saleInventory2 = saleInventory["StateName"].fillna("United States")
#saleInventory2 = saleInventory["StateName"].drop_duplicates()
#saleInventory2 = saleInventory2.sort_values().to_list()

ui.page_opts(
    title=ui.tags.div(
        "Interactive US Housing Data Dashboard",
        style="""
            font-size: 2.2rem;
            font-weight: 700;
            color: #3D52D5;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.15);
            padding-bottom: 0.25rem;
            letter-spacing: 0.5px;
        """
    )
)



# Home Inventory % Change


#FORECAST_DATES = [
#    "2026-01-31",
#    "2026-03-31",
#   "2026-12-31",
#]

with ui.sidebar():
    ui.input_select("state", "Filter by State", choices = STATE_CHOICES)
    ui.input_slider("date_range", "Flter by Date Range", 
                min = string_to_date("2018-3-31"),
                max = string_to_date("2025-12-31"), 
                value = [string_to_date(x) for x in ["2018-3-31", "2025-12-31"]])
    ui.input_select(
    "forecast_type",
    "Forecast Type",
    choices={
    "sfr": "Single-Family (SFR)",
    "mfr": "Multi-Family (MFR)",},
    selected="sfr",)

# Current median list price

with ui.layout_column_wrap():
    with ui.value_box(showcase = icon_svg("dollar-sign")):
        "Current Median List Price"

        @render.ui 
        def price():
            date_columns = medianListPrice.columns[6:]
            states = medianListPrice.groupby("StateName").mean(numeric_only=True)
            dates = states[date_columns].reset_index()
            states = dates.melt(id_vars="StateName", var_name = "Date", value_name="Value")
            country = medianListPrice[medianListPrice["RegionType"] == "country"]
            country_dates = country[date_columns].reset_index()
            country_dates["StateName"] = "United States"
            country = country_dates.melt(
                id_vars=["StateName"], var_name="Date", value_name="Value"
            )

            res = pd.concat([states, country])
            res = res[res["Date"] != "index"]
            df = res[res["StateName"] == input.state()]
            last_value = df.iloc[-1,-1]
            return f"${last_value:,.0f}"
        

    with ui.value_box(showcase = icon_svg("house")): 
        "Home Inventory Change"

        @render.ui 
        def change():
            date_columns = medianListPrice.columns[6:]
            states = medianListPrice.groupby("StateName").mean(numeric_only=True)
            dates = states[date_columns].reset_index()
            states = dates.melt(id_vars="StateName", var_name = "Date", value_name="Value")
            country = medianListPrice[medianListPrice["RegionType"] == "country"]
            country_dates = country[date_columns].reset_index()
            country_dates["StateName"] = "United States"
            country = country_dates.melt(
                id_vars=["StateName"], var_name="Date", value_name="Value"
            )

            res = pd.concat([states, country])
            res = res[res["Date"] != "index"]
            df = res[res["StateName"] == input.state()]
            last_value = df.iloc[-1,-1]
            second_last_value = df.iloc[-2,-1]
            percent_change = ((last_value - second_last_value)/second_last_value*100)
            if percent_change > 0:
                sign = "+"
                return f"{sign}{percent_change:.2f}%"
            else:
                return f"{percent_change:.2f}%"


with ui.navset_card_underline(title = "Median List Price"):
    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):
        @render_plotly
        def list_price_plot():
            price_grouped = medianListPrice.groupby('StateName').mean(numeric_only=True)
            # take mean, not sum
            date_columns = medianListPrice.columns[6:]
            price_grouped_dates = price_grouped[date_columns].reset_index()
            price_df_viz = price_grouped_dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")

            price_df_viz = filter_by_date(price_df_viz, input.date_range())

            if input.state() == "United States":
                df = price_df_viz
            else:
                df = price_df_viz[price_df_viz["StateName"] == input.state()]

            # Visual creation
            fig = px.line(df, x="Date", y ="Value", color="StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig
    with ui.nav_panel("Table", icon = icon_svg("table")):
        @render.data_frame
        def list_price_data():
            if input.state() == "United States":
                df = medianListPrice
            else:
                df = medianListPrice[medianListPrice["StateName"] == input.state()]
            return render.DataGrid(df)




with ui.navset_card_underline(title = "For Sale Inventory"):
    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):
        @render_plotly
        def for_sale_plot():
            for_sale_grouped = saleInventory.groupby('StateName').sum(numeric_only=True)
            date_columns = saleInventory.columns[6:]
            for_sale_grouped_dates = for_sale_grouped[date_columns].reset_index()
            for_sale_df_viz = for_sale_grouped_dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")

            for_sale_df_viz = filter_by_date(for_sale_df_viz, input.date_range())
            if input.state() == "United States":
                df = for_sale_df_viz
            else:
                df = for_sale_df_viz[for_sale_df_viz["StateName"] == input.state()]

            fig = px.line(df, x="Date", y ="Value", color="StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig
    with ui.nav_panel("Table", icon = icon_svg("table")):
        @render.data_frame
        def for_sale_data():
            if input.state() == "United States":
                df = saleInventory
            else:
                df = saleInventory[saleInventory["StateName"] == input.state()]
            return render.DataGrid(df)




with ui.navset_card_underline(title = "New Listings"):
    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):
        @render_plotly
        def listings_plot():
            new_listings_grouped = newListings.groupby("StateName").sum(numeric_only=True)
            date_columns = newListings.columns[6:]
            new_listings_grouped_dates = new_listings_grouped[date_columns].reset_index()
            new_listings_df_viz = new_listings_grouped_dates.melt(id_vars=["StateName"], var_name = "Date", value_name = "Value")

            new_listings_df_viz = filter_by_date(new_listings_df_viz, input.date_range())

            if input.state() == "United States":
                df = new_listings_df_viz
            else:
                df = new_listings_df_viz[new_listings_df_viz["StateName"] == input.state()]

            fig = px.line(df, x = "Date", y = "Value", color = "StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig

    with ui.nav_panel("Table", icon = icon_svg("table")):
        @render.data_frame
        def listing_data():
            if input.state() == "United States":
                df = newListings
            else:
                df = newListings[newListings["StateName"] == input.state()]
            return render.DataGrid(df)




with ui.navset_card_underline(title="Forecast Growth (ZORF)"):
    with ui.nav_panel("Plot", icon=icon_svg("chart-line")):
        @render_plotly
        def forecast_plot():
            if input.forecast_type() == "sfr":
                forecast_df = forecast_sfr.copy()
                line_color = "#16a34a"
            else:
                forecast_df = forecast_mfr.copy()
                line_color = "#dc2626"

            date_columns = ["2026-01-31", "2026-03-31", "2026-12-31"]
            
            df_viz = forecast_df.melt(id_vars=["RegionName"], value_vars=date_columns, var_name="Date", value_name="Growth")

            df_viz["Date"] = pd.to_datetime(df_viz["Date"]).dt.date

            
            df_viz = df_viz[df_viz["RegionName"] == "United States"]

            fig = px.line( df_viz, x="Date", y="Growth", color="RegionName", markers=True, color_discrete_sequence=[line_color])
            

            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")

            return fig

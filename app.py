import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Loomulik iive maakonniti", layout="wide")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": ["39", "44", "49", "51", "57", "59", "65", "67", "70", "74", "78", "82", "84", "86", "37"]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""


@st.cache_data
def import_data():
    headers = {"Content-Type": "application/json"}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)

    response = requests.post(
        STATISTIKAAMETI_API_URL,
        json=parsed_payload,
        headers=headers
    )
    response.raise_for_status()

    text = response.content.decode("utf-8-sig")
    df = pd.read_csv(StringIO(text))

    value_column = df.columns[-1]
    df = df.rename(columns={value_column: "Loomulik iive"})

    df["Aasta"] = df["Aasta"].astype(str)
    df["Maakond"] = df["Maakond"].astype(str)
    df["Maakond"] = df["Maakond"].str.replace(" maakond", "", regex=False)

    return df


@st.cache_data
def import_geojson():
    gdf = gpd.read_file(GEOJSON_FILE)

    gdf["Maakond"] = gdf["MNIMI"].astype(str)
    gdf["Maakond"] = gdf["Maakond"].str.replace(" maakond", "", regex=False)

    return gdf


def get_data_for_year(df, year):
    return df[df["Aasta"] == year].copy()


def plot_map(gdf, year):
    fig, ax = plt.subplots(figsize=(12, 8))

    gdf.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="viridis",
        missing_kwds={
            "color": "lightgrey",
            "label": "Andmed puuduvad"
        },
        legend_kwds={"label": "Loomulik iive"}
    )

    ax.set_title(f"Loomulik iive maakonniti aastal {year}")
    ax.axis("off")
    plt.tight_layout()

    return fig


st.title("Loomulik iive maakonniti")
st.write("Vali külgribalt aasta ja kaart uueneb automaatselt.")

df = import_data()
gdf = import_geojson()

years = sorted(df["Aasta"].unique())
selected_year = st.sidebar.selectbox("Vali aasta", years, index=len(years) - 1)

year_data = get_data_for_year(df, selected_year)

merged = gdf.merge(year_data, on="Maakond", how="left")

fig = plot_map(merged, selected_year)
st.pyplot(fig)

st.subheader("Andmed")
st.dataframe(year_data)

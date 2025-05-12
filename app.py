import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.features import DivIcon
import plotly.graph_objects as go
import plotly.io as pio
from folium import IFrame
from streamlit_folium import st_folium
import zipfile
import os

st.set_page_config(page_title="Peta IKM", layout="wide")
st.title("📍 Visualisasi Klaster IKM Provinsi Jambi")

# --- Ekstrak ZIP jika belum diekstrak ---
if os.path.exists("peta_ikm_jambi_files.zip"):
    with zipfile.ZipFile("peta_ikm_jambi_files.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
else:
    st.error("❌ File ZIP tidak ditemukan.")

try:
    # Load data
    gdf = gpd.read_file("KABKOTA.shp")
    df = pd.read_csv("persentase_cluster_per_kabupaten.csv")
    df.columns = df.columns.str.upper()

    if 'KAB_KOTA' not in df.columns:
        df.rename(columns={df.columns[0]: 'KAB_KOTA'}, inplace=True)

    merged = gdf.merge(df, on='KAB_KOTA')
    merged = merged.to_crs(epsg=4326)

    # Inisialisasi Peta
    center = merged.geometry.centroid.unary_union.centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=8, tiles="CartoDB positron")

    # Judul
    title_html = '''
         <h3 align="center" style="font-size:20px; margin-top:30px; margin-bottom:5px;">
         <b>📍 Peta IKM Provinsi Jambi</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Legenda
    legend_html = '''
         <div style="position: relative; bottom: -10px; left: 10px; width: 95%; font-size:14px; text-align: left; padding-top: 10px;">
             <b>Keterangan Cluster:</b>
             <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                 <li>🔴 <b>Cluster 1</b> – Rendah</li>
                 <li>🟢 <b>Cluster 2</b> – Sedang</li>
                 <li>🔵 <b>Cluster 3</b> – Tinggi</li>
             </ul>
         </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    labels = ['Cluster 1', 'Cluster 2', 'Cluster 3']
    colors = ['#d7191c', '#1a9641', '#2b83ba']

    for _, row in merged.iterrows():
        kab = row['KAB_KOTA'].title()
        cluster_vals = row[[col for col in df.columns if col != 'KAB_KOTA']]

        tooltip_html = f"""
        <b>{kab}</b><br>
        Cluster 1: {cluster_vals[0]:.2f}%<br>
        Cluster 2: {cluster_vals[1]:.2f}%<br>
        Cluster 3: {cluster_vals[2]:.2f}%
        """

        fig = go.Figure(
            data=[go.Bar(x=labels, y=cluster_vals.values, marker_color=colors)],
            layout=go.Layout(
                title=dict(text=kab, x=0.5),
                height=250,
                margin=dict(l=10, r=10, t=40, b=10),
            )
        )
        fig.update_layout(showlegend=False)
        html_div = pio.to_html(fig, include_plotlyjs='cdn', full_html=False)
        iframe = IFrame(html_div, width=320, height=300)
        popup = folium.Popup(iframe, max_width=350)

        folium.GeoJson(
            row.geometry,
            tooltip=tooltip_html,
            popup=popup,
            style_function=lambda x: {
                'fillColor': '#f0f0f0',
                'color': 'gray',
                'weight': 1,
                'fillOpacity': 0.5,
            }
        ).add_to(m)

        # Label Kabupaten
        centroid = row.geometry.centroid
        folium.map.Marker(
            [centroid.y, centroid.x],
            icon=DivIcon(
                icon_size=(150,36),
                icon_anchor=(0,0),
                html=f'<div style="font-size:9pt; color:gray;">{kab}</div>',
            )
        ).add_to(m)

    # Tampilkan di Streamlit
    st_folium(m, width=1100, height=700)

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memproses peta: {e}")

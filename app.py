import streamlit as st
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.geometry import Point
from PIL import Image, ImageDraw, ImageFont
import io, time

ox.settings.use_cache = True
ox.settings.log_console = False

def dibujar_mapa(nombre, buffer_km=5, coords=None):
    start_total = time.time()
    
    if coords:
        lat, lon = coords
        geom = Point(float(lon), float(lat))  # shapely usa (x=lon, y=lat)
        nombre_display = f"{lat:.4f}, {lon:.4f}"
    else:
        gdf = ox.geocode_to_gdf(nombre)
        if gdf.empty:
            st.error(f"No se encontró geometría para: {nombre}")
            return None
        geom = gdf.loc[0, "geometry"]
        if geom.geom_type != 'Point':
            geom = geom.centroid
        nombre_display = nombre

    buffer_deg = buffer_km / 111  # km -> grados aprox
    area = geom.buffer(buffer_deg)

    G = ox.graph_from_polygon(area, network_type="all")
    G_proj = ox.project_graph(G)

    fig, ax = ox.plot_graph(G_proj, bgcolor='white', node_size=0,
                            edge_linewidth=0.5, edge_color='gray',
                            show=False, close=False)

    ax.text(0.5, 0.05, nombre_display, ha='center', va='center',
            transform=ax.transAxes, fontsize=12, fontweight='bold', color='black')

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)

    buf = io.BytesIO()
    plt.savefig(buf, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    buf.seek(0)

    imagen = Image.open(buf)
    ancho, alto = imagen.size
    margen = 50
    img_margen = Image.new('RGB', (ancho + 2*margen, alto + 2*margen), 'white')
    img_margen.paste(imagen, (margen, margen))

    draw = ImageDraw.Draw(img_margen)
    draw.rectangle([0,0, ancho+2*margen, alto+2*margen], outline='black', width=5)

    try:
        fuente = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except:
        fuente = ImageFont.load_default()
    draw.text((margen+10, alto+margen+10), nombre_display, font=fuente, fill='black')

    out_buf = io.BytesIO()
    img_margen.save(out_buf, format="PNG")
    out_buf.seek(0)
    return out_buf

# Interfaz Streamlit
st.title("🗺️ Generador de Mapas Estéticos")
st.write("Introduce una ciudad o coordenadas y genera tu mapa en alta calidad listo para imprimir.")

modo = st.radio("Selecciona modo:", ["Ciudad", "Coordenadas"])

if modo == "Ciudad":
    ciudad = st.text_input("Nombre de la ciudad", "Madrid, Spain")
    if st.button("Generar mapa"):
        with st.spinner("Generando mapa..."):
            img_buf = dibujar_mapa(ciudad)
            if img_buf:
                st.image(img_buf, caption=f"Mapa de {ciudad}", use_column_width=True)
                st.download_button("Descargar PNG", data=img_buf, file_name="mapa.png", mime="image/png")

else:
    lat = st.number_input("Latitud", value=40.4168)
    lon = st.number_input("Longitud", value=-3.7038)
    if st.button("Generar mapa"):
        with st.spinner("Generando mapa..."):
            img_buf = dibujar_mapa(None, coords=(lat, lon))
            if img_buf:
                st.image(img_buf, caption=f"Mapa en {lat}, {lon}", use_column_width=True)
                st.download_button("Descargar PNG", data=img_buf, file_name="mapa.png", mime="image/png")

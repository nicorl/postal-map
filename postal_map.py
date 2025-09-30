import osmnx as ox
from shapely.geometry import Point
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import sys
import time

ox.settings.use_cache = True
ox.settings.log_console = False
DEBUG = True

def log(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def dibujar_mapa(nombre, archivo_salida, buffer_km=5, coords=None):
    start_total = time.time()
    
    if coords:
        lat, lon = coords
        geom = Point(float(lon), float(lat))  # shapely usa (x=lon, y=lat)
        nombre_display = f"{lat:.4f}, {lon:.4f}"
        log(f"Usando coordenadas: {geom}")
    else:
        log(f"Geocodificando lugar: {nombre}")
        gdf = ox.geocode_to_gdf(nombre)
        if gdf.empty:
            print(f"No se encontró geometría para: {nombre}")
            return
        geom = gdf.loc[0, "geometry"]
        if geom.geom_type != 'Point':
            geom = geom.centroid
        nombre_display = nombre
        log(f"Centro geográfico: {geom}")

    # Crear buffer alrededor del punto central
    buffer_deg = buffer_km / 111  # aproximación km -> grados
    area = geom.buffer(buffer_deg)
    log(f"Buffer creado de {buffer_km} km (~{buffer_deg:.4f} grados)")

    # Descargar red de calles
    log("Descargando red de calles en el buffer...")
    start = time.time()
    G = ox.graph_from_polygon(area, network_type="all")
    G_proj = ox.project_graph(G)
    log(f"Red descargada en {time.time() - start:.2f}s")

    # Plot del mapa
    log("Generando plot del mapa...")
    fig, ax = ox.plot_graph(G_proj, bgcolor='white', node_size=0,
                            edge_linewidth=0.5, edge_color='gray', show=False, close=False)

    ax.text(0.5, 0.05, nombre_display, ha='center', va='center',
            transform=ax.transAxes, fontsize=12, fontweight='bold', color='black')

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    # Marco con PIL
    imagen = Image.open(archivo_salida)
    ancho, alto = imagen.size
    margen = 50
    img_margen = Image.new('RGB', (ancho + 2*margen, alto + 2*margen), 'white')
    img_margen.paste(imagen, (margen, margen))
    draw = ImageDraw.Draw(img_margen)
    draw.rectangle([0,0, ancho+2*margen, alto+2*margen], outline='black', width=5)
    try:
        fuente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        fuente = ImageFont.load_default()
    draw.text((margen+10, alto+margen+10), nombre_display, font=fuente, fill='black')
    img_margen.save(archivo_salida)
    log(f"Mapa generado en {time.time() - start_total:.2f}s")
    print(f"Mapa guardado en: {archivo_salida}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python postal_map.py <nombre_ciudad| -coords lat,lon> <archivo_salida>")
        sys.exit(1)

    if sys.argv[1] == "-coords":
        try:
            lat_str, lon_str = sys.argv[2].split(",")
            coords = (float(lat_str), float(lon_str))
            archivo = sys.argv[3]
        except:
            print("Error: coordenadas deben ser <latitud>,<longitud>")
            sys.exit(1)
        dibujar_mapa(None, archivo, coords=coords)
    else:
        ciudad = sys.argv[1]
        archivo = sys.argv[2]
        dibujar_mapa(ciudad, archivo)

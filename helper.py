import osmnx as ox
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import contextily as cx
from pyproj import Transformer
import random
from voxcity.generator import load_voxcity
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
from affine import Affine
from matplotlib.patches import Circle
import textwrap
from matplotlib.animation import FFMpegWriter


BIAS_COLOR = {
    "A": "red",
    "B": "blue",
    None: "gold"
}


# =========================
# Build walkable + height
# =========================
def load_walkable_graph_from_osm(polygon_latlon):
    """
    polygon_latlon: list of (lon, lat) tuples (same as VoxCity input)
    """
    # OSMnx expects (lat, lon)
    polygon = [(lat, lon) for lon, lat in polygon_latlon]

    G = ox.graph_from_polygon(
        polygon,
        network_type="walk",   # walkable streets + sidewalks
        simplify=True
    )

    return G

def build_walkable_from_osmnx(polygon_latlon):
    """
    polygon_latlon: list of (lon, lat) tuples
    """

    # Shapely Polygon expects (x, y) = (lon, lat)
    poly = Polygon(polygon_latlon)

    if not poly.is_valid:
        raise ValueError("Invalid polygon passed to OSMnx")

    G = ox.graph_from_polygon(
        poly,
        network_type="walk",
        simplify=True
    )

    G = ox.distance.add_edge_lengths(G)
    return G

def plot_city_base(ax, G):
    # ---- project graph to Web Mercator ----
    G_proj = ox.project_graph(G, to_crs="EPSG:3857")

    # ---- plot streets ----
    ox.plot_graph(
        G_proj,
        ax=ax,
        show=False,
        close=False,
        node_size=0,
        edge_color="#444444",
        edge_linewidth=1.0,
        bgcolor="none"   # IMPORTANT
    )

    # ---- add Google-like basemap ----
    cx.add_basemap(
        ax,
        source=cx.providers.Esri.WorldImagery,
        alpha=1.0
    )


    ax.set_axis_off()

def init_agents(ax):
    scat_A = ax.scatter([], [], s=120, c="red", edgecolor="black", zorder=5)
    scat_B = ax.scatter([], [], s=120, c="blue", edgecolor="black", zorder=5)
    scat_res = ax.scatter(
        [], [],
        s=40,
        c="gold",
        edgecolors="black",
        alpha=1.0,
        zorder=4
    )

    return scat_A, scat_B, scat_res

def project_latlon(lat, lon):
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3857",
        always_xy=True
    )
    x, y = transformer.transform(lon, lat)
    return x, y

def add_landmark(ax):
    x, y = project_latlon(37.787994, -122.407437)

    # marker
    ax.scatter(
        x, y,
        s=120,
        c="black",
        marker="*",
        zorder=10
    )

    # label
    ax.text(
        x, y,
        "Union Square",
        fontsize=11,
        fontweight="bold",
        ha="left",
        va="bottom",
        color="black",
        zorder=10,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=2)
    )

def load_transit_stop_nodes(G):
    """
    Returns a set of graph node IDs corresponding to transit stops.
    Robust to OSMnx geometry types.
    """

    # Get edges geometry
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

    # Convert MultiLineString → Polygon
    geom = edges.unary_union
    poly = geom.convex_hull   # 🔑 THIS IS THE FIX

    if not isinstance(poly, (Polygon, MultiPolygon)):
        raise ValueError("Failed to construct a polygon from graph edges")

    tags = {
        "public_transport": ["platform", "stop_position"],
        "highway": "bus_stop",
        "railway": ["tram_stop", "subway_entrance"]
    }

    # Query OSM features inside polygon
    gdf = ox.features_from_polygon(poly, tags=tags)

    if gdf.empty:
        print("⚠️ No transit stops found in polygon")
        return set()

    stop_nodes = set()
    
    for geom in gdf.geometry:
        if geom is None:
            continue

        if random.random() > 0.1:
            continue

        x, y = geom.centroid.x, geom.centroid.y

        try:
            node = ox.nearest_nodes(G, x, y)
            stop_nodes.add(node)
        except Exception:
            continue

    print(f"🚇 Loaded {len(stop_nodes)} transit stop nodes")
    return stop_nodes

def plot_transit_stops(ax, G_proj, transit_nodes):
    xs = [G_proj.nodes[n]["x"] for n in transit_nodes]
    ys = [G_proj.nodes[n]["y"] for n in transit_nodes]

    ax.scatter(
        xs, ys,
        s=25,
        c="purple",
        marker="s",
        alpha=0.7,
        zorder=3,
        label="Transit stop"
    )

def run_2d_sim(G_proj, sim, transit_nodes):
    fig, (ax_map, ax_wealth) = plt.subplots(
        1, 2,
        figsize=(14, 7),
        gridspec_kw={"width_ratios": [3, 2]}
    )

    wrapped = "\n".join(textwrap.wrap(sim.global_faith, 100))
    fig.suptitle(
        wrapped,
        fontsize=12,
        y=0.98,
        ha="center"
    )

    # ---- LEFT: city map ----
    plot_city_base(ax_map, G_proj)
    plot_transit_stops(ax_map, G_proj, transit_nodes)

    add_landmark(ax_map)  # Union Square
    scat_A, scat_B, scat_res = init_agents(ax_map)
    vision_circle_A = None
    vision_circle_B = None

    if sim.A.vision_radius:
        vision_circle_A = Circle(
            (0, 0),                 # placeholder center
            radius=sim.A.vision_radius,
            facecolor="red",
            edgecolor="red",
            alpha=0.15,
            linewidth=2,
            zorder=4
        )

        ax_map.add_patch(vision_circle_A)

    if sim.B.vision_radius:
        vision_circle_B = Circle(
            (0, 0),                 # placeholder center
            radius=sim.B.vision_radius,
            facecolor="blue",
            edgecolor="blue",
            alpha=0.15,
            linewidth=2,
            zorder=4
        )

        ax_map.add_patch(vision_circle_B)

    # ---- RIGHT: wealth plot ----
    ax_wealth.set_title("Wealth Over Time")
    ax_wealth.set_xlabel("Time step")
    ax_wealth.set_ylabel("Wealth")

    line_A, = ax_wealth.plot([], [], color="red", lw=2, label="Player A")
    line_B, = ax_wealth.plot([], [], color="blue", lw=2, label="Player B")

    ax_wealth.legend()
    ax_wealth.grid(alpha=0.3)

    # ---- history buffers ----
    t_hist = []
    wA_hist = []
    wB_hist = []

    # ---- animation update ----
    def update(frame):
        sim.step()

        # === map update ===
        Ax = G_proj.nodes[sim.A.node]["x"]
        Ay = G_proj.nodes[sim.A.node]["y"]
        Bx = G_proj.nodes[sim.B.node]["x"]
        By = G_proj.nodes[sim.B.node]["y"]

        # 🔴 update vision circle
        if sim.A.vision_radius:
            vision_circle_A.center = (Ax, Ay)
        if sim.B.vision_radius:
            vision_circle_B.center = (Bx, By)


        scat_A.set_offsets([[Ax, Ay]])
        scat_B.set_offsets([[Bx, By]])


        if sim.resources:
            res_xy = [
                (G_proj.nodes[r.node]["x"], G_proj.nodes[r.node]["y"])
                for r in sim.resources
            ]

            res_colors = [
                BIAS_COLOR.get(r.bias, "gold")
                for r in sim.resources
            ]

            scat_res.set_offsets(res_xy)
            scat_res.set_color(res_colors)
        else:
            scat_res.set_offsets(np.empty((0, 2)))


        # === wealth update ===
        t_hist.append(sim.t)
        wA_hist.append(sim.A.wealth)
        wB_hist.append(sim.B.wealth)

        line_A.set_data(t_hist, wA_hist)
        line_B.set_data(t_hist, wB_hist)

        ax_wealth.set_xlim(max(0, sim.t - 200), sim.t + 5)
        ymax = max(wA_hist + wB_hist) if t_hist else 10
        ax_wealth.set_ylim(0, max(10, ymax * 1.2))

        return scat_A, scat_B, scat_res, line_A, line_B, vision_circle_A, vision_circle_B

    ani = FuncAnimation(
        fig,
        update,
        interval=80,
        blit=False
    )

    writer = FFMpegWriter(
        fps=12,
        metadata=dict(artist="VoxCity Simulation"),
        bitrate=1800
    )

    ani.save(
        "simulation.mp4",
        writer=writer,
        dpi=150
    )

    plt.show()

# -------------------------
# Flood Risk
# -------------------------
def get_flood_prone_roads():
    voxcity = load_voxcity("output_sf/voxcity.pkl")
    dem = voxcity.dem.elevation
    meta = voxcity.dem.meta

    lon_min, lat_min, lon_max, lat_max = meta.bounds
    crs = meta.crs  # 'EPSG:4326'

    thresh = np.nanpercentile(dem, 15)
    flood_mask = dem <= thresh


    nrows, ncols = dem.shape

    dx = (lon_max - lon_min) / ncols
    dy = (lat_max - lat_min) / nrows

    transform = Affine(
        dx, 0, lon_min,
        0, -dy, lat_max
    )


    polys = []
    for geom, val in shapes(flood_mask.astype("uint8"), transform=transform):
        if val == 1:
            polys.append(shape(geom))

    flood_geom_dem = gpd.GeoSeries(polys).unary_union

    flood_gdf = gpd.GeoSeries([flood_geom_dem], crs="EPSG:4326")  # <-- change if DEM CRS differs
    flood_geom_3857 = flood_gdf.to_crs("EPSG:3857").iloc[0]

    return flood_geom_3857



from sim import Sim
from helper import run_2d_sim, build_walkable_from_osmnx, load_transit_stop_nodes, get_flood_prone_roads
import osmnx as ox
from faith_system import FaithSystem
from shapely.geometry import LineString, Polygon


SF_RECTANGLE_VERTICES = [
    (-122.4300, 37.7645),  # SW (SoMa / Mission edge)
    (-122.4300, 37.8100),  # NW (Fisherman's Wharf / Pier 39)
    (-122.3800, 37.8100),  # NE (East of Embarcadero)
    (-122.3800, 37.7645),  # SE (Bay Bridge side)
]


UNION_SQUARE_LATLON = (37.787994, -122.407437)  # (lat, lon)

G = build_walkable_from_osmnx(SF_RECTANGLE_VERTICES)
Gp = ox.project_graph(G, to_crs="EPSG:3857")
transit_nodes = load_transit_stop_nodes(G)


sim = Sim(Gp, transit_nodes)          # simulation stays unprojected
run_2d_sim(Gp, sim, transit_nodes)   # rendering uses projected graph

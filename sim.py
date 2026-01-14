from state import Player, Resource
from typing import Optional, Tuple, List
import numpy as np
import random
import matplotlib.pyplot as plt

import random
import networkx as nx
import math
from typing import Optional, List
from faith_system import FaithSystem





# =========================
# Config
# =========================
SF_RECTANGLE_VERTICES = [
    (-122.4230, 37.7645),  # SW
    (-122.4230, 37.7895),  # NW
    (-122.3945, 37.7895),  # NE
    (-122.3945, 37.7645),  # SE
]
MESHSIZE_M = 10  # meters/cell (coarser = faster)
TICK_INTERVAL_MS = 50
SPAWN_PROB = 0.3         # per tick
SPAWN_BIAS_RADIUS = 500 # in m
RESOURCE_VALUES = [1]
CONSUME_RADIUS_CELLS = 1   # Manhattan-ish


class Sim:
    def __init__(self, G, transit_nodes):
        self.G = G
        self.transit_nodes = set(transit_nodes)
        self.nodes = list(G.nodes)

        # cache node coordinates
        self.node_xy = {
            n: (G.nodes[n]["x"], G.nodes[n]["y"])
            for n in self.nodes
        }

        self.t = 0
        self.rid = 0
        self.resources = []

        self.A = Player("A", self.random_node())
        self.B = Player("B", self.random_node())

        self.global_faith = """Only Player A has acces to transportation and the resources that are spawn biased are also biased to player A. 
            Additionally, player B has only a limited knowledge of the resources available. It knows of resources only at a proximity to it."""

        faith = FaithSystem(
            self.global_faith
        )

        self.params = faith.run()


        print(self.params)

        
        if self.params.vision_radius:
            self.A.vision_radius = self.params.vision_radius['A']
            self.B.vision_radius = self.params.vision_radius['B']

    # -------------------------
    # Helpers
    # -------------------------
    def random_node(self):
        return random.choice(self.nodes)

    def euclidean_dist(self, n1, n2):
        x1, y1 = self.node_xy[n1]
        x2, y2 = self.node_xy[n2]
        return math.hypot(x1 - x2, y1 - y2)
    
    # -------------------------
    # Resources
    # -------------------------
    def nodes_within_radius(self, center_node, radius_m):
        cx, cy = self.node_xy[center_node]

        return [
            n for n, (x, y) in self.node_xy.items()
            if math.hypot(x - cx, y - cy) <= radius_m
        ]

    def spawn_resource(self, spawn_bias):
        if random.random() > SPAWN_PROB:
            return

        node = None
        radius_m = SPAWN_BIAS_RADIUS
        biased_player = None

        # Bias toward Player A
        if spawn_bias and spawn_bias.get("A"):
            if random.random() < spawn_bias["A"]:
                print("Spawn near A")
                candidates = self.nodes_within_radius(self.A.node, radius_m)
                if candidates:
                    node = random.choice(candidates)
                    biased_player = 'A'

        # Bias toward Player B (only if A didn't trigger)
        if node is None and spawn_bias and spawn_bias.get("B"):
            if random.random() < spawn_bias["B"]:
                candidates = self.nodes_within_radius(self.B.node, radius_m)
                if candidates:
                    node = random.choice(candidates)
                    biased_player = 'B'

        # Fallback: uniform random
        if node is None:
            node = self.random_node()

        self.resources.append(Resource(self.rid, node, 1, biased_player))
        self.rid += 1

    def nearest_resource(self, p):
        if not self.resources:
            return None, None

        best_node = None
        best_dist = float("inf")

        for r in self.resources:
            if r.bias is None or r.bias == p.name:

                d = self.euclidean_dist(p.node, r.node)

                if p.vision_radius:
                    if d > p.vision_radius: 
                        continue

                if d < best_dist:
                    best_node = r.node
                    best_dist = d

        return best_node, best_dist

    # -------------------------
    # Transit logic
    # -------------------------
    def nearest_stop(self, p, ):
        best = None
        best_dist = float("inf")

        for s in self.transit_nodes:
            d = self.euclidean_dist(p.node, s)
            if d < best_dist:
                best = s
                best_dist = d

        return best, best_dist
    
    def try_teleport(self, p, dest):
        if p.node in self.transit_nodes:
            p.node = dest
            return True
        else:
            return False
        

    def stop_closest_to_any_resource(self):
        if not self.resources:
            return None, None

        best_stop = None
        best_dist = float("inf")

        for s in self.transit_nodes:
            for r in self.resources:
                d = self.euclidean_dist(s, r.node)
                if d < best_dist:
                    best_stop = s
                    best_dist = d

        return best_stop, best_dist

    # -------------------------
    # Consumption
    # -------------------------
    def consume_if_close(self, p):
        for i, r in enumerate(self.resources):
            if r.node == p.node:
                p.wealth += r.value
                self.resources.pop(i)
                break

    # -------------------------
    # Movement
    # -------------------------
    def step_player(self, p):

        res_node, res_dist = self.nearest_resource(p)
        dest_dist = None
        stop_dist = None
        target = None
        
        if self.params.teleport_access[p.name]:
            stop_node, stop_dist = self.nearest_stop(p)
            stop_dest, dest_dist = self.stop_closest_to_any_resource()

            teleport_happened = self.try_teleport(p, stop_dest)
            
            if teleport_happened:
                target, _ = self.nearest_resource(p)

            elif stop_node and stop_dest and (res_dist > stop_dist + dest_dist):
                target = stop_node

        if not target:
            target = res_node

        if target is None:
            nbrs = list(self.G.neighbors(p.node))
            if nbrs:
                p.node = random.choice(nbrs)
            return

        try:
            path = nx.shortest_path(
                self.G,
                source=p.node,
                target=target,
                weight="length"
            )
            if len(path) > 1:
                p.node = path[1]
        except nx.NetworkXNoPath:
            pass

    # -------------------------
    # Tick
    # -------------------------
    def step(self):
        self.t += 1
        
        self.spawn_resource(self.params.spawn_bias)

        self.step_player(self.A)
        self.step_player(self.B)

        self.consume_if_close(self.A)
        self.consume_if_close(self.B)
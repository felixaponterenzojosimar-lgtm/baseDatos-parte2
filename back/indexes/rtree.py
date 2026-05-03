import struct
import math
import heapq
import os
from .base_index import Index, NotSupportedError
from ..storage import Schema, PageManager, DiskStats

_HDR = struct.Struct(">?H")    # is_leaf(bool), num_entries(uint16) — 3 bytes
_MBR = struct.Struct(">dddd")  # min_lat, min_lon, max_lat, max_lon  — 32 bytes
_CID = struct.Struct(">I")     # child page id                        — 4 bytes
_PT  = struct.Struct(">dd")    # lat, lon                             — 16 bytes

_INTERNAL_ENTRY = _MBR.size + _CID.size  # 36 bytes
PAGE_SIZE = 4096


class RTree(Index):
    def __init__(self, schema: Schema, page_manager: PageManager, stats: DiskStats,
                 lat_field: str, lon_field: str):
        super().__init__(schema, page_manager, stats)
        self.lat_field = lat_field
        self.lon_field = lon_field
        leaf_entry = _PT.size + schema.record_size
        self.max_entries = min(
            (PAGE_SIZE - _HDR.size) // _INTERNAL_ENTRY,
            (PAGE_SIZE - _HDR.size) // leaf_entry,
            50,
        )
        self._root_path = page_manager.filepath.replace(".bin", ".root")
        self.root_id = self._load_root()

    def _load_root(self):
        if not os.path.exists(self._root_path):
            return None
        with open(self._root_path, "rb") as f:
            data = f.read(4)
        if len(data) < 4:
            return None
        val = struct.unpack(">i", data)[0]
        return val if val >= 0 else None

    def _save_root(self):
        with open(self._root_path, "wb") as f:
            f.write(struct.pack(">i", self.root_id if self.root_id is not None else -1))

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add(self, record: dict) -> None:
        lat = float(record[self.lat_field])
        lon = float(record[self.lon_field])
        if self.root_id is None:
            self.root_id = self.pm.allocate_page()
            self._save_root()
            self._write_node(self.root_id, {"is_leaf": True, "entries": []})
        path, leaf_id = self._choose_leaf((lat, lon))
        leaf = self._read_node(leaf_id)
        leaf["entries"].append({"lat": lat, "lon": lon, "record": record})
        if len(leaf["entries"]) > self.max_entries:
            left, right = self._split_node(leaf)
            self._write_node(leaf_id, left)
            new_id = self.pm.allocate_page()
            self._write_node(new_id, right)
            self._adjust_tree(path, leaf_id, new_id)
        else:
            self._write_node(leaf_id, leaf)
            self._adjust_tree(path, leaf_id)

    def search(self, key: tuple) -> dict | None:
        if self.root_id is None:
            return None
        lat, lon = float(key[0]), float(key[1])
        stack = [self.root_id]
        while stack:
            node = self._read_node(stack.pop())
            if node["is_leaf"]:
                for e in node["entries"]:
                    if e["lat"] == lat and e["lon"] == lon:
                        return e["record"]
            else:
                for e in node["entries"]:
                    mbr = e["mbr"]
                    if mbr[0] <= lat <= mbr[2] and mbr[1] <= lon <= mbr[3]:
                        stack.append(e["child"])
        return None

    def range_search(self, point: tuple, radius: float) -> list[dict]:
        if self.root_id is None:
            return []
        results = []
        stack = [self.root_id]
        while stack:
            node = self._read_node(stack.pop())
            if node["is_leaf"]:
                for e in node["entries"]:
                    if self._haversine(point, (e["lat"], e["lon"])) <= radius:
                        results.append(e["record"])
            else:
                for e in node["entries"]:
                    if self._mbr_intersects_circle(e["mbr"], point, radius):
                        stack.append(e["child"])
        return results

    def knn(self, point: tuple, k: int) -> list[dict]:
        if self.root_id is None:
            return []
        records_store: list[dict] = []
        heap = [(0.0, 0, False, self.root_id)]
        cnt = 1
        results: list[dict] = []
        while heap and len(results) < k:
            dist, _, is_point, data = heapq.heappop(heap)
            if is_point:
                results.append(records_store[data])
            else:
                node = self._read_node(data)
                if node["is_leaf"]:
                    for e in node["entries"]:
                        d = self._haversine(point, (e["lat"], e["lon"]))
                        idx = len(records_store)
                        records_store.append(e["record"])
                        heapq.heappush(heap, (d, cnt, True, idx))
                        cnt += 1
                else:
                    for e in node["entries"]:
                        mbr = e["mbr"]
                        clamp_lat = max(mbr[0], min(point[0], mbr[2]))
                        clamp_lon = max(mbr[1], min(point[1], mbr[3]))
                        d = self._haversine(point, (clamp_lat, clamp_lon))
                        heapq.heappush(heap, (d, cnt, False, e["child"]))
                        cnt += 1
        return results

    def remove(self, key: tuple) -> bool:
        if self.root_id is None:
            return False
        lat, lon = float(key[0]), float(key[1])
        return self._remove_from(self.root_id, lat, lon)

    def all_points(self) -> list[dict]:
        """Retorna todos los puntos almacenados (para visualización)."""
        if self.root_id is None:
            return []
        results = []
        stack = [self.root_id]
        while stack:
            node = self._read_node(stack.pop())
            if node["is_leaf"]:
                for e in node["entries"]:
                    results.append({"lat": e["lat"], "lon": e["lon"], "record": e["record"]})
            else:
                for e in node["entries"]:
                    stack.append(e["child"])
        return results

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _haversine(self, p1: tuple, p2: tuple) -> float:
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 6371.0 * 2 * math.asin(math.sqrt(min(1.0, a)))

    def _mbr_intersects_circle(self, mbr: tuple, point: tuple, radius: float) -> bool:
        clamp_lat = max(mbr[0], min(point[0], mbr[2]))
        clamp_lon = max(mbr[1], min(point[1], mbr[3]))
        return self._haversine(point, (clamp_lat, clamp_lon)) <= radius

    def _compute_mbr(self, entries: list, is_leaf: bool) -> tuple:
        if not entries:
            return (0.0, 0.0, 0.0, 0.0)
        if is_leaf:
            lats = [e["lat"] for e in entries]
            lons = [e["lon"] for e in entries]
            return (min(lats), min(lons), max(lats), max(lons))
        return (
            min(e["mbr"][0] for e in entries),
            min(e["mbr"][1] for e in entries),
            max(e["mbr"][2] for e in entries),
            max(e["mbr"][3] for e in entries),
        )

    def _split_node(self, node: dict) -> tuple:
        entries = node["entries"]
        is_leaf = node["is_leaf"]
        mid = len(entries) // 2
        return (
            {"is_leaf": is_leaf, "entries": entries[:mid]},
            {"is_leaf": is_leaf, "entries": entries[mid:]},
        )

    def _choose_leaf(self, point: tuple) -> tuple:
        curr_id = self.root_id
        path = []
        while True:
            node = self._read_node(curr_id)
            if node["is_leaf"]:
                return path, curr_id
            best_idx, best_enl, best_area = 0, float("inf"), float("inf")
            for i, e in enumerate(node["entries"]):
                mbr = e["mbr"]
                new_mbr = (
                    min(mbr[0], point[0]), min(mbr[1], point[1]),
                    max(mbr[2], point[0]), max(mbr[3], point[1]),
                )
                old_area = (mbr[2] - mbr[0]) * (mbr[3] - mbr[1])
                new_area = (new_mbr[2] - new_mbr[0]) * (new_mbr[3] - new_mbr[1])
                enl = new_area - old_area
                if enl < best_enl or (enl == best_enl and old_area < best_area):
                    best_enl, best_area, best_idx = enl, old_area, i
            path.append((curr_id, best_idx))
            curr_id = node["entries"][best_idx]["child"]

    def _adjust_tree(self, path: list, curr_id: int, new_id: int = None) -> None:
        curr_new_id = new_id
        for parent_id, child_idx in reversed(path):
            parent = self._read_node(parent_id)
            curr_node = self._read_node(curr_id)
            parent["entries"][child_idx]["mbr"] = self._compute_mbr(
                curr_node["entries"], curr_node["is_leaf"]
            )
            if curr_new_id is not None:
                new_node = self._read_node(curr_new_id)
                parent["entries"].insert(child_idx + 1, {
                    "mbr": self._compute_mbr(new_node["entries"], new_node["is_leaf"]),
                    "child": curr_new_id,
                })
                if len(parent["entries"]) > self.max_entries:
                    left, right = self._split_node(parent)
                    self._write_node(parent_id, left)
                    split_id = self.pm.allocate_page()
                    self._write_node(split_id, right)
                    curr_id, curr_new_id = parent_id, split_id
                else:
                    self._write_node(parent_id, parent)
                    curr_new_id = None
            else:
                self._write_node(parent_id, parent)
            curr_id = parent_id
        if curr_new_id is not None:
            ln = self._read_node(curr_id)
            rn = self._read_node(curr_new_id)
            new_root_id = self.pm.allocate_page()
            self._write_node(new_root_id, {
                "is_leaf": False,
                "entries": [
                    {"mbr": self._compute_mbr(ln["entries"], ln["is_leaf"]), "child": curr_id},
                    {"mbr": self._compute_mbr(rn["entries"], rn["is_leaf"]), "child": curr_new_id},
                ],
            })
            self.root_id = new_root_id
            self._save_root()

    def _read_node(self, page_id: int) -> dict:
        raw = self.pm.read_page(page_id)
        is_leaf, n = _HDR.unpack(raw[:_HDR.size])
        offset = _HDR.size
        entries = []
        if is_leaf:
            for _ in range(n):
                lat, lon = _PT.unpack(raw[offset:offset + _PT.size])
                offset += _PT.size
                rec = self.schema.deserialize(raw[offset:offset + self.schema.record_size])
                offset += self.schema.record_size
                entries.append({"lat": lat, "lon": lon, "record": rec})
        else:
            for _ in range(n):
                mbr = _MBR.unpack(raw[offset:offset + _MBR.size])
                offset += _MBR.size
                child = _CID.unpack(raw[offset:offset + _CID.size])[0]
                offset += _CID.size
                entries.append({"mbr": mbr, "child": child})
        return {"is_leaf": is_leaf, "entries": entries}

    def _write_node(self, page_id: int, node: dict) -> None:
        entries = node["entries"]
        is_leaf = node["is_leaf"]
        data = bytearray(_HDR.pack(is_leaf, len(entries)))
        if is_leaf:
            for e in entries:
                data += _PT.pack(e["lat"], e["lon"])
                data += self.schema.serialize(e["record"])
        else:
            for e in entries:
                data += _MBR.pack(*e["mbr"])
                data += _CID.pack(e["child"])
        self.pm.write_page(page_id, bytes(data).ljust(PAGE_SIZE, b"\x00"))

    def _remove_from(self, node_id: int, lat: float, lon: float) -> bool:
        node = self._read_node(node_id)
        if node["is_leaf"]:
            for i, e in enumerate(node["entries"]):
                if e["lat"] == lat and e["lon"] == lon:
                    node["entries"].pop(i)
                    self._write_node(node_id, node)
                    return True
            return False
        for e in node["entries"]:
            mbr = e["mbr"]
            if mbr[0] <= lat <= mbr[2] and mbr[1] <= lon <= mbr[3]:
                if self._remove_from(e["child"], lat, lon):
                    child_node = self._read_node(e["child"])
                    if child_node["entries"]:
                        e["mbr"] = self._compute_mbr(child_node["entries"], child_node["is_leaf"])
                    self._write_node(node_id, node)
                    return True
        return False

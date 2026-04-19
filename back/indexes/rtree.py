from .base_index import Index, NotSupportedError
from ..storage import Schema, PageManager, DiskStats


class RTree(Index):
    """
    R-Tree espacial con clave compuesta (latitud, longitud).
    Soporta búsqueda por radio y k vecinos más cercanos (kNN).
    """

    def __init__(self, schema: Schema, page_manager: PageManager, stats: DiskStats,
                 lat_field: str, lon_field: str):
        super().__init__(schema, page_manager, stats)
        self.lat_field = lat_field  # nombre del campo latitud en el schema
        self.lon_field = lon_field  # nombre del campo longitud

    def add(self, record: dict) -> None:
        """
        Input:  record  dict con todos los campos (debe incluir lat_field y lon_field)
        Output: None
        — Insertar punto ajustando MBRs desde la hoja hasta la raíz.
        """
        pass

    def search(self, key: tuple) -> dict | None:
        """
        Input:  key  (lat, lon) exacto
        Output: dict o None
        """
        pass

    def range_search(self, point: tuple, radius: float) -> list[dict]:
        """
        Input:  point   (lat, lon)
                radius  distancia máxima en km
        Output: lista de registros dentro del círculo
        — Usa distancia haversine para comparar.
        """
        pass

    def knn(self, point: tuple, k: int) -> list[dict]:
        """
        Input:  point  (lat, lon)
                k      número de vecinos a retornar
        Output: lista de los k registros más cercanos, ordenados por distancia
        """
        pass

    def remove(self, key: tuple) -> bool:
        """
        Input:  key  (lat, lon)
        Output: True/False
        """
        pass

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _haversine(self, p1: tuple, p2: tuple) -> float:
        """
        Input:  p1, p2  tuplas (lat, lon) en grados decimales
        Output: distancia en km
        """
        pass

    def _mbr_intersects_circle(self, mbr: tuple, point: tuple, radius: float) -> bool:
        """
        Input:  mbr    (min_lat, min_lon, max_lat, max_lon)
                point  (lat, lon)
                radius en km
        Output: True si el MBR puede contener puntos dentro del radio
        """
        pass

    def _read_node(self, page_id: int) -> dict:
        """Deserializa página → nodo {type, entries: [{mbr, child_page | record}]}."""
        pass

    def _write_node(self, page_id: int, node: dict) -> None:
        """Serializa nodo → página y escribe en disco."""
        pass

    def _choose_leaf(self, point: tuple) -> int:
        """Retorna page_id de la hoja donde insertar el punto."""
        pass

    def _adjust_tree(self, path: list[int]) -> None:
        """Actualiza MBRs en el camino raíz → hoja después de inserción."""
        pass

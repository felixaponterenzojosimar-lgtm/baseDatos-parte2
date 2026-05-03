from .base_index import Index, DuplicateKeyError, NotSupportedError
from ..storage import Schema, PageManager, DiskStats
import struct

class ExtendibleHashing(Index):
    """
    Hashing extensible con directorio dinámico
    """

    BUCKET_SIZE = 4  # registros máximos por bucket antes de split
    FLAG_ACTIVE = 0x01
    FLAG_DELETED = 0x00

    def __init__(self, schema: Schema, page_manager: PageManager,
                 dir_page_manager: PageManager, stats: DiskStats):
        super().__init__(schema, page_manager, stats)
        self.dir_pm = dir_page_manager  # PageManager del directorio
        self._init_directory()
        self.record_size = schema.record_size
        self.record_with_flag_size = self.record_size + 1  # +1 byte para flag

    def _init_directory(self):
        """Inicializa el directorio si está vacío."""
        if self.dir_pm.total_pages() == 0:
            # Crear directorio inicial, 2 entradas apuntando a un bucket vacío
            global_depth = 1
            # Crear primer bucket
            bucket_page_id = self.pm.allocate_page()
            self._init_bucket_page(bucket_page_id)
            
            # Escribir directorio: [global_depth][page_id_0][page_id_1]
            dir_data = struct.pack(">I", global_depth)  # 4 bytes global_depth
            dir_data += struct.pack(">I", bucket_page_id)  # page_id para hash 0
            dir_data += struct.pack(">I", bucket_page_id)  # page_id para hash 1
            self.dir_pm.write_page(0, dir_data)
    
    
    def add(self, record: dict) -> None:
        """Inserta un registro."""
        key = record[self.schema.primary_key]
        
        # Verificar si ya existe
        if self.search(key) is not None:
            raise DuplicateKeyError(f"La clave {key} ya existe")
        
        # Leer directorio
        global_depth, page_ids = self._read_directory()
        bucket_page_id = self._find_bucket_page_id(key, global_depth, page_ids)
        
        # Leer bucket actual
        records = self._read_bucket(bucket_page_id)
        
        # Buscar slot libre o añadir al final
        found_free = False
        for i, (flag, rec) in enumerate(records):
            if flag == self.FLAG_DELETED:
                # Reusar slot eliminado
                records[i] = (self.FLAG_ACTIVE, record)
                found_free = True
                break
        
        if not found_free:
            # Añadir nuevo registro
            records.append((self.FLAG_ACTIVE, record))
        
        # Verificar si hay overflow
        if len(records) > self.BUCKET_SIZE:
            self._split_bucket(bucket_page_id, records, global_depth, page_ids)
        else:
            # Escribir bucket actualizado
            self._write_bucket(bucket_page_id, records)

    def search(self, key) -> dict | None:
        """Búsqueda exacta por clave."""
        global_depth, page_ids = self._read_directory()
        bucket_page_id = self._find_bucket_page_id(key, global_depth, page_ids)
        
        records = self._read_bucket(bucket_page_id)
        
        for flag, record in records:
            if flag == self.FLAG_ACTIVE and record[self.schema.primary_key] == key:
                return record
        return None

    def remove(self, key) -> bool:
        """Elimina el registro con esa clave."""
        global_depth, page_ids = self._read_directory()
        bucket_page_id = self._find_bucket_page_id(key, global_depth, page_ids)
        
        records = self._read_bucket(bucket_page_id)
        
        for i, (flag, record) in enumerate(records):
            if flag == self.FLAG_ACTIVE and record[self.schema.primary_key] == key:
                # Marcar como eliminado
                records[i] = (self.FLAG_DELETED, record)
                self._write_bucket(bucket_page_id, records)
                return True
        return False

    def range_search(self, begin, end) -> list[dict]:
        """No soportado en hashing extensible."""
        raise NotSupportedError("ExtendibleHashing no soporta range_search")

    def scan_all(self) -> list[dict]:
        """Retorna todos los registros activos iterando los buckets únicos."""
        _, page_ids = self._read_directory()
        results = []
        for page_id in set(page_ids):
            for flag, record in self._read_bucket(page_id):
                if flag == self.FLAG_ACTIVE:
                    results.append(record)
        return results

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------
    def _init_bucket_page(self, page_id: int):
        """Inicializa una página de bucket vacía"""
        self.pm.write_record_count(page_id, 0, b"")

    def _hash(self, key, depth: int) -> int:
        """
        Retorna los `depth` bits menos significativos del hash de key.
        """
        hash_val = hash(key) & 0x7fffffff  # entero positivo de 31 bits
        mask = (1 << depth) - 1
        return hash_val & mask

    def _read_directory(self):
        """
        Lee el directorio desde disco.
        Retorna: (global_depth, list_page_ids)
        """
        if self.dir_pm.total_pages() == 0:
            return 0, []
        
        raw = self.dir_pm.read_page(0)
        global_depth = struct.unpack(">I", raw[:4])[0]
        
        # Calcular tamaño del directorio
        num_entries = 1 << global_depth
        page_ids = []
        for i in range(num_entries):
            offset = 4 + (i * 4)
            page_id = struct.unpack(">I", raw[offset:offset+4])[0]
            page_ids.append(page_id)
        
        return global_depth, page_ids

    def _write_directory(self, global_depth: int, page_ids: list):
        """
        Escribe el directorio en disco.
        """
        dir_data = struct.pack(">I", global_depth)
        for page_id in page_ids:
            dir_data += struct.pack(">I", page_id)
        
        # Padding para llenar la página
        if len(dir_data) < PageManager.PAGE_SIZE:
            dir_data += b"\x00" * (PageManager.PAGE_SIZE - len(dir_data))
        
        self.dir_pm.write_page(0, dir_data)

    def _find_bucket_page_id(self, key, global_depth: int, page_ids: list) -> int:
        """Retorna el page_id del bucket para la clave dada."""
        hash_bits = self._hash(key, global_depth)
        return page_ids[hash_bits]

    def _read_bucket(self, page_id: int) -> list[tuple]:
        """
        Lee un bucket y retorna lista de (flag, record_dict)
        flag = 0x01 activo, 0x00 eliminado
        """
        raw = self.pm.read_page(page_id)
        count = struct.unpack(">H", raw[:2])[0]  # 2 bytes para contador
        
        records = []
        offset = 2  # después del contador
        
        for _ in range(count):
            flag = raw[offset]
            offset += 1
            record_data = raw[offset:offset + self.record_size]
            offset += self.record_size
            record = self.schema.deserialize(record_data)
            records.append((flag, record))
        
        return records

    def _write_bucket(self, page_id: int, records: list[tuple]):
        """
        Escribe un bucket en disco.
        records: lista de (flag, record_dict)
        """
        data = bytearray()
        count = len(records)
        
        for flag, record in records:
            data.append(flag)
            data.extend(self.schema.serialize(record))
        
        # Escribir la página (cabecera + data)
        full_page = struct.pack(">H", count) + bytes(data)
        full_page = full_page.ljust(PageManager.PAGE_SIZE, b"\x00")
        self.pm.write_page(page_id, full_page)
        
        
    def _split_bucket(self, bucket_page_id: int, records: list, global_depth: int, page_ids: list):
        """
        Divide el bucket y redistribuye sus registros.
        """
        local_depth = 1  # Profundidad local
        # Busqueda de todos los índices que apuntan a este bucket y los actualiza
        indices = []
        for i, pid in enumerate(page_ids):
            if pid == bucket_page_id:
                indices.append(i)
        
        import math
        num_sharing = len(indices)
        local_depth = global_depth - int(math.log2(num_sharing))
        
        # Incrementar profundidad local
        new_local_depth = local_depth + 1
        
        # Crear un nuevo bucket (nueva página)
        new_bucket_page_id = self.pm.allocate_page()
        self._init_bucket_page(new_bucket_page_id)
        
        # Redistribuir registros
        records_old = []
        records_new = []
        
        for flag, record in records:
            key = record[self.schema.primary_key]
            # Usar la nueva profundidad para decidir destino
            hash_bits = self._hash(key, new_local_depth)
            original_index = indices[0]
            mask = (1 << new_local_depth) - 1
            bit_val = hash_bits & mask
            # Comparar el bit correspondiente
            if (bit_val >> (new_local_depth - 1)) & 1:
                records_new.append((flag, record))
            else:
                records_old.append((flag, record))
        
        # Escribir ambos buckets
        self._write_bucket(bucket_page_id, records_old)
        self._write_bucket(new_bucket_page_id, records_new)
        
        # Actualizar directorio
        if new_local_depth > global_depth:
            # Duplicar directorio
            new_global_depth = global_depth + 1
            new_page_ids = []
            for pid in page_ids:
                new_page_ids.append(pid)
                new_page_ids.append(pid)
            global_depth = new_global_depth
            page_ids = new_page_ids
            
            # Actualizar los índices
            for idx in indices:
                # Determinar el valor del bit extra
                if (idx >> (global_depth - 1)) & 1:
                    page_ids[idx] = new_bucket_page_id
        
        # Escribir directorio actualizado
        self._write_directory(global_depth, page_ids)

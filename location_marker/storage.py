import json
import os
from threading import RLock
from typing import List, Dict, Optional

from mcdreforged.api.all import *

from location_marker import constants
from location_message import Position, Location


class LocationStorage:
    def __init__(self):
        self.locations: List[Location] = []
        self._name_map = {}  # type: Dict[str, Location]
        self._lock = RLock()

    def get(self, name: str) -> Optional[Location]:
        with self._lock:
            return self._name_map.get(name)

    def get_locations(self) -> List[Location]:
        with self._lock:
            return list(self.locations)

    def contains(self, name: str) -> bool:
        with self._lock:
            return name in self._name_map

    def _add(self, location: Location) -> bool:
        with self._lock:
            existed = self.get(location.name)
            if existed:
                return False
            else:
                self.locations.append(location)
                self._name_map[location.name] = location
                return True

    def add(self, location: Location) -> bool:
        ret = self._add(location)
        self.save()
        return ret

    def _remove(self, target_name: str) -> Optional[Location]:
        with self._lock:
            loc = self.get(target_name)
            if loc is not None:
                self.locations.remove(loc)
                self._name_map.pop(loc.name)
                return loc
            else:
                return None

    def remove(self, target_name: str) -> Optional[Location]:
        ret = self._remove(target_name)
        self.save()
        return ret

    def load(self, file_path: str):
        with self._lock:
            folder = os.path.dirname(file_path)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            self.locations.clear()
            needs_overwrite = False
            if not os.path.isfile(file_path):
                needs_overwrite = True
            else:
                with open(file_path, 'r', encoding='utf8') as handle:
                    data = None
                    try:
                        data = json.load(handle)
                        locations = deserialize(data, List[Location])
                    except Exception as e:
                        from location_marker.entry import server_inst
                        server_inst.logger.error(
                            'Fail to load {}: {}'.format(file_path, e))
                        server_inst.logger.error(
                            'Unknown data: {}'.format(data))
                        needs_overwrite = True
                    else:
                        for location in locations:
                            self._add(location)
            if needs_overwrite:
                self.save()

    def save(self):
        from location_marker.entry import server_inst
        with self._lock:
            file_path = os.path.join(
                server_inst.get_data_folder(), constants.STORAGE_FILE)
            with open(file_path, 'w', encoding='utf8') as file:
                json.dump(serialize(self.locations), file,
                          indent=4, ensure_ascii=False)

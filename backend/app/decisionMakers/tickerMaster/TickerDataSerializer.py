import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd


class TickerDataSerializer:
    """
    Klasa do serializacji i deserializacji danych tickera.
    Struktura: {base_path}/{ticker}/{datetime}/{mode}.json
    """

    def __init__(self, base_path: Union[str, Path] = "data"):
        """
        Args:
            base_path: Główny katalog na dane (domyślnie 'data')
        """
        self.base_path = Path(base_path)

    def _ensure_directory(self, path: Path) -> None:
        """Tworzy katalog jeśli nie istnieje"""
        path.parent.mkdir(parents=True, exist_ok=True)

    def _json_serializer(self, obj: Any) -> str:
        """Pomocnicza funkcja do serializacji obiektów nie-JSON"""
        if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
            return obj.isoformat()
        if isinstance(obj, pd.Series):
            return obj.to_dict()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _get_file_path(self, path: str, date_time: datetime, mode: str) -> Path:

        date_str = date_time.strftime("%Y%m%d_%H%M%S")
        return self.base_path / path / date_str / f"{mode}.json"

    def serialize(self, path: str, date_time: datetime,
                  mode: str, data: Dict) -> str:

        if mode not in ['structured_input', 'llm_output', 'llm_ranker']:
            raise ValueError(f"Mode must be 'structured_input' or 'llm_output' or 'llm_ranker', got {mode}")

        file_path = self._get_file_path(path, date_time, mode)
        self._ensure_directory(file_path)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=self._json_serializer)

        return str(file_path)

    def deserialize(self, path: str, date_time: datetime, mode: str) -> Dict:
        """
        Odczytuje dane z pliku.

        Args:
            ticker: Nazwa tickera
            date_time: Data i czas
            mode: 'structured_input' lub 'llm_output'

        Returns:
            Słownik z danymi
        """
        if mode not in ['structured_input', 'llm_output', 'llm_ranker']:
            raise ValueError(f"Mode must be 'structured_input' or 'llm_output' or 'llm_ranker', got {mode}")

        file_path = self._get_file_path(path, date_time, mode)

        if not file_path.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

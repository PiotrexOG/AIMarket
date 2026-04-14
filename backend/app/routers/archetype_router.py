from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.dto.archetype_dto import ArchetypeRead
from app.services.archetype_service import ArchetypeService

router = APIRouter(prefix="/archetypes", tags=["Archetypes"])
service = ArchetypeService()

@router.get("/", response_model=List[ArchetypeRead])
def list_all_archetypes():
    """Pobiera listę wszystkich dostępnych strategii (archetypów) botów."""
    return service.get_all_archetypes()

@router.get("/{archetype_key}", response_model=ArchetypeRead)
def get_archetype_details(
    archetype_key: str = Path(..., description="Klucz archetypu, np. 'degen_trader'")
):
    """Pobiera szczegółową konfigurację konkretnego archetypu."""
    archetype = service.get_archetype_by_key(archetype_key)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")
    return archetype
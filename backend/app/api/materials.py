from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.models.project import Project
from app.schemas.material import MaterialCreate, MaterialResponse

router = APIRouter(prefix="/projects/{project_id}/materials", tags=["Materials"])


def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=MaterialResponse, status_code=201)
def create_material(project_id: int, payload: MaterialCreate, db: Session = Depends(get_db)):
    get_project_or_404(project_id, db)
    material = Material(project_id=project_id, **payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("", response_model=list[MaterialResponse])
def list_materials(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(project_id, db)
    stmt = select(Material).where(Material.project_id == project_id).order_by(Material.id)
    return list(db.scalars(stmt).all())


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(project_id: int, material_id: int, db: Session = Depends(get_db)):
    get_project_or_404(project_id, db)
    material = db.get(Material, material_id)
    if material is None or material.project_id != project_id:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.delete("/{material_id}", status_code=204)
def delete_material(project_id: int, material_id: int, db: Session = Depends(get_db)):
    get_project_or_404(project_id, db)
    material = db.get(Material, material_id)
    if material is None or material.project_id != project_id:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(material)
    db.commit()

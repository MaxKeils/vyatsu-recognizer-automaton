"""API routes for configuration management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.crud import ConfigurationCRUD
from database.schemas import ConfigurationRequest, ConfigurationResponse

router = APIRouter(prefix="/configuration", tags=["configuration"])


@router.get("/", response_model=ConfigurationResponse)
def get_configuration(db: Session = Depends(get_db)):
    config = ConfigurationCRUD.get_configuration(db)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.put("/", response_model=ConfigurationResponse)
def update_configuration(
    config_data: ConfigurationRequest,
    db: Session = Depends(get_db)
):
    config = ConfigurationCRUD.create_or_update_configuration(db, config_data)
    return config
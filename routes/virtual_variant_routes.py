"""API роутер для управления виртуальными вариантами."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from database.database import get_db
from database.crud import VirtualVariantCRUD, TaskCRUD
from database.schemas import (
    VirtualVariantCreateRequest, 
    VirtualVariantUpdateRequest,
    VirtualVariantDetailResponse
)


router = APIRouter(prefix="/virtual-variants", tags=["virtual-variants"])


@router.get("/", response_model=List[VirtualVariantDetailResponse])
async def get_all_virtual_variants(
    db: Session = Depends(get_db)
) -> List[VirtualVariantDetailResponse]:
    """
    Получить список всех виртуальных вариантов с полной информацией.
    
    Args:
        db: Сессия БД
        
    Returns:
        Список виртуальных вариантов
    """
    variants = VirtualVariantCRUD.get_all_virtual_variants(db)
    return variants


@router.get("/{variant_id}", response_model=VirtualVariantDetailResponse)
async def get_virtual_variant(
    variant_id: int,
    db: Session = Depends(get_db)
) -> VirtualVariantDetailResponse:
    """
    Получить информацию о конкретном виртуальном варианте.
    
    Args:
        variant_id: ID виртуального варианта
        db: Сессия БД
        
    Returns:
        Информация о виртуальном варианте
        
    Raises:
        HTTPException: Если виртуальный вариант не найден
    """
    variant = VirtualVariantCRUD.get_virtual_variant_by_id(db, variant_id)
    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Виртуальный вариант не найден"
        )
    return variant


@router.post("/", response_model=VirtualVariantDetailResponse, status_code=201)
async def create_virtual_variant(
    request: VirtualVariantCreateRequest,
    db: Session = Depends(get_db)
) -> VirtualVariantDetailResponse:
    """
    Создать новый виртуальный вариант.
    
    Args:
        request: Данные для создания виртуального варианта
        db: Сессия БД
        
    Returns:
        Созданный виртуальный вариант
        
    Raises:
        HTTPException: Если задание не найдено или display_number уже существует
    """
    # Проверяем существование задания
    task = TaskCRUD.get_task_by_id(db, request.real_task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Задание с указанным ID не найдено"
        )
    
    # Проверяем уникальность display_number
    existing_variant = VirtualVariantCRUD.get_virtual_variant_by_display_number(
        db, request.display_number
    )
    if existing_variant:
        raise HTTPException(
            status_code=409,
            detail=f"Виртуальный вариант с номером {request.display_number} уже существует"
        )
    
    try:
        variant = VirtualVariantCRUD.create_virtual_variant(
            db=db,
            real_task_id=request.real_task_id,
            display_number=request.display_number
        )
        return variant
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ошибка при создании виртуального варианта. Возможно, номер уже занят"
        )


@router.put("/{variant_id}", response_model=VirtualVariantDetailResponse)
async def update_virtual_variant(
    variant_id: int,
    request: VirtualVariantUpdateRequest,
    db: Session = Depends(get_db)
) -> VirtualVariantDetailResponse:
    """
    Обновить виртуальный вариант.
    
    Args:
        variant_id: ID виртуального варианта
        request: Данные для обновления
        db: Сессия БД
        
    Returns:
        Обновленный виртуальный вариант
        
    Raises:
        HTTPException: Если виртуальный вариант или задание не найдено
    """
    # Проверяем существование виртуального варианта
    existing_variant = VirtualVariantCRUD.get_virtual_variant_by_id(db, variant_id)
    if not existing_variant:
        raise HTTPException(
            status_code=404,
            detail="Виртуальный вариант не найден"
        )
    
    # Если обновляется real_task_id, проверяем существование задания
    if request.real_task_id is not None:
        task = TaskCRUD.get_task_by_id(db, request.real_task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Задание с указанным ID не найдено"
            )
    
    # Если обновляется display_number, проверяем уникальность
    if request.display_number is not None:
        conflict_variant = VirtualVariantCRUD.get_virtual_variant_by_display_number(
            db, request.display_number
        )
        if conflict_variant and conflict_variant.id != variant_id:
            raise HTTPException(
                status_code=409,
                detail=f"Виртуальный вариант с номером {request.display_number} уже существует"
            )
    
    try:
        variant = VirtualVariantCRUD.update_virtual_variant(
            db=db,
            variant_id=variant_id,
            real_task_id=request.real_task_id,
            display_number=request.display_number
        )
        return variant
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ошибка при обновлении виртуального варианта"
        )


@router.delete("/{variant_id}", status_code=204)
async def delete_virtual_variant(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить виртуальный вариант.
    
    Args:
        variant_id: ID виртуального варианта
        db: Сессия БД
        
    Returns:
        Пустой ответ со статусом 204
        
    Raises:
        HTTPException: Если виртуальный вариант не найден
    """
    deleted = VirtualVariantCRUD.delete_virtual_variant(db, variant_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Виртуальный вариант не найден"
        )
    return None

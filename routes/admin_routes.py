"""API роутер для админ-панели."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from database.database import get_db
from database.crud import ConfigurationCRUD, VirtualVariantCRUD, TaskCRUD
from database.schemas import (
    AdminLoginRequest, AdminLoginResponse,
    AdminChangePasswordRequest,
    VirtualVariantCreateRequest, VirtualVariantUpdateRequest,
    VirtualVariantDetailResponse
)
from service.auth_service import AuthService


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse, status_code=200)
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
) -> AdminLoginResponse:
    """
    Вход в админ-панель по паролю из конфигурации.
    
    Args:
        request: Запрос с паролем
        db: Сессия БД
        
    Returns:
        Результат входа
        
    Raises:
        HTTPException: Если пароль неверный (401)
    """
    is_valid = ConfigurationCRUD.verify_admin_password(db, request.password)
    
    if is_valid:
        return AdminLoginResponse(
            success=True,
            message="Вход выполнен успешно"
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль"
        )


@router.post("/change-password", status_code=200)
async def change_admin_password(
    request: AdminChangePasswordRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Изменить пароль администратора.
    
    Требует старый пароль для подтверждения.
    
    Args:
        request: Запрос со старым и новым паролем
        db: Сессия БД
        
    Returns:
        Результат операции: {"success": true, "message": "Пароль успешно изменен"}
        
    Raises:
        HTTPException: Если старый пароль неверный (400)
    """
    # Проверяем старый пароль
    is_valid = ConfigurationCRUD.verify_admin_password(db, request.old_password)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Неверный старый пароль"
        )
    
    # Хешируем новый пароль и сохраняем
    new_hash = AuthService.hash_password(request.new_password)
    config = ConfigurationCRUD.update_password(db, new_hash)
    
    if not config:
        raise HTTPException(
            status_code=500,
            detail="Не удалось обновить пароль"
        )
    
    return {
        "success": True,
        "message": "Пароль успешно изменен"
    }


@router.get("/variants", response_model=List[VirtualVariantDetailResponse])
async def get_all_virtual_variants_admin(
    db: Session = Depends(get_db)
) -> List[VirtualVariantDetailResponse]:
    """
    Получить все виртуальные варианты (для админа).
    
    Возвращает детальную информацию включая ID реальных заданий.
    
    Args:
        db: Сессия БД
        
    Returns:
        Список всех виртуальных вариантов
    """
    variants = VirtualVariantCRUD.get_all_virtual_variants(db)
    return variants


@router.post("/variants", response_model=VirtualVariantDetailResponse, status_code=201)
async def create_virtual_variant(
    request: VirtualVariantCreateRequest,
    db: Session = Depends(get_db)
) -> VirtualVariantDetailResponse:
    """
    Создать новый виртуальный вариант.
    
    Args:
        request: Данные виртуального варианта
        db: Сессия БД
        
    Returns:
        Созданный виртуальный вариант
        
    Raises:
        HTTPException: Если реальное задание не найдено или display_number уже занят
    """
    # Проверяем существование реального задания
    task = TaskCRUD.get_task_by_id(db, request.real_task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Реальное задание с ID {request.real_task_id} не найдено"
        )
    
    # Проверяем уникальность display_number
    existing = VirtualVariantCRUD.get_virtual_variant_by_display_number(db, request.display_number)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Виртуальный вариант с номером {request.display_number} уже существует"
        )
    
    try:
        variant = VirtualVariantCRUD.create_virtual_variant(
            db,
            request.real_task_id,
            request.display_number
        )
        return variant
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Ошибка при создании виртуального варианта"
        )


@router.put("/variants/{variant_id}", response_model=VirtualVariantDetailResponse)
async def update_virtual_variant(
    variant_id: int,
    request: VirtualVariantUpdateRequest,
    db: Session = Depends(get_db)
) -> VirtualVariantDetailResponse:
    """
    Обновить виртуальный вариант.
    
    Args:
        variant_id: ID виртуального варианта
        request: Новые данные
        db: Сессия БД
        
    Returns:
        Обновленный виртуальный вариант
        
    Raises:
        HTTPException: Если вариант не найден или некорректные данные
    """
    # Если обновляется real_task_id, проверяем его существование
    if request.real_task_id is not None:
        task = TaskCRUD.get_task_by_id(db, request.real_task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Реальное задание с ID {request.real_task_id} не найдено"
            )
    
    # Если обновляется display_number, проверяем уникальность
    if request.display_number is not None:
        existing = VirtualVariantCRUD.get_virtual_variant_by_display_number(db, request.display_number)
        if existing and existing.id != variant_id:
            raise HTTPException(
                status_code=400,
                detail=f"Виртуальный вариант с номером {request.display_number} уже существует"
            )
    
    try:
        variant = VirtualVariantCRUD.update_virtual_variant(
            db,
            variant_id,
            request.real_task_id,
            request.display_number
        )
        
        if not variant:
            raise HTTPException(
                status_code=404,
                detail=f"Виртуальный вариант с ID {variant_id} не найден"
            )
        
        return variant
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Ошибка при обновлении виртуального варианта"
        )


@router.delete("/variants/{variant_id}", status_code=200)
async def delete_virtual_variant(
    variant_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Удалить виртуальный вариант.
    
    Args:
        variant_id: ID виртуального варианта
        db: Сессия БД
        
    Returns:
        Результат операции: {"success": true, "message": "Виртуальный вариант успешно удален"}
        
    Raises:
        HTTPException: Если вариант не найден (404)
    """
    success = VirtualVariantCRUD.delete_virtual_variant(db, variant_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Виртуальный вариант не найден"
        )
    
    return {
        "success": True,
        "message": f"Виртуальный вариант {variant_id} успешно удален"
    }

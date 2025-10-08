from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from database.database import get_db
from database.crud import UserCRUD, StudentProgressCRUD
from database.schemas import UserRequest, UserUpdateRequest, UserResponse, UserLoginResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserLoginResponse)
def create_or_get_user_by_full_name(
    user_data: UserRequest,
    db: Session = Depends(get_db)
):
    """
    Создать нового пользователя или получить существующего по ФИО.
    
    Если пользователь с таким ФИО существует, возвращает его вместе с прогрессом.
    Если указана группа, обновляет её.

    
    Args:
        user_data: Данные пользователя (full_name обязательно, group_name опционально)
        db: Сессия БД
        
    Returns:
        Пользователь (существующий или созданный) + его прогресс (если есть)
    """
    try:
        user = UserCRUD.create_or_get_user_by_full_name(db, user_data)
        
        # Получаем прогресс пользователя, если он есть
        progress = StudentProgressCRUD.get_user_progress(db, user.id)
        
        return UserLoginResponse(
            user=user,
            progress=progress if progress else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = UserCRUD.get_all_users(db)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        user = UserCRUD.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )
        return user
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Ошибка при обновлении пользователя"
        )


@router.delete("/{user_id}", status_code=200)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    return {
        "success": True,
        "message": "Пользователь успешно удален"
    }
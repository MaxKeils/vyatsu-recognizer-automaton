"""Admin routes for managing theory questions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from database.database import get_db
from database.crud import TheoryQuestionCRUD
from database.schemas import (
    TheoryQuestionCreate,
    TheoryQuestionUpdate,
    TheoryQuestionResponse
)

router = APIRouter(prefix="/admin/theory-questions", tags=["admin", "theory"])


@router.post("/", response_model=TheoryQuestionResponse, status_code=201)
def create_question(
    question_data: TheoryQuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новый теоретический вопрос с вариантами ответов.
    
    Args:
        question_data: Данные вопроса (текст, тип, варианты ответов)
        db: Сессия БД
        
    Returns:
        Созданный вопрос с вариантами ответов
    """
    try:
        question = TheoryQuestionCRUD.create_question(db, question_data)
        return question
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating theory question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании вопроса. Обратитесь к администратору."
        )


@router.get("/", response_model=List[TheoryQuestionResponse])
def get_all_questions(db: Session = Depends(get_db)):
    """
    Получить все теоретические вопросы.
    
    Возвращает вопросы с правильными ответами (только для админа).
    
    Returns:
        Список всех вопросов
    """
    try:
        questions = TheoryQuestionCRUD.get_all_questions(db)
        return questions
    except Exception as e:
        logging.error(f"Error fetching questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении вопросов. Обратитесь к администратору."
        )


@router.get("/{question_id}", response_model=TheoryQuestionResponse)
def get_question_by_id(question_id: int, db: Session = Depends(get_db)):
    """
    Получить вопрос по ID.
    
    Args:
        question_id: ID вопроса
        db: Сессия БД
        
    Returns:
        Вопрос с вариантами ответов
        
    Raises:
        HTTPException 404: Вопрос не найден
    """
    try:
        question = TheoryQuestionCRUD.get_question_by_id(db, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении вопроса. Обратитесь к администратору."
        )


@router.put("/{question_id}", response_model=TheoryQuestionResponse)
def update_question(
    question_id: int,
    question_data: TheoryQuestionUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить вопрос.
    
    Args:
        question_id: ID вопроса
        question_data: Новые данные вопроса
        db: Сессия БД
        
    Returns:
        Обновленный вопрос
        
    Raises:
        HTTPException 404: Вопрос не найден
    """
    try:
        question = TheoryQuestionCRUD.update_question(db, question_id, question_data)
        if not question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении вопроса. Обратитесь к администратору."
        )


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    """
    Удалить вопрос.
    
    Args:
        question_id: ID вопроса
        db: Сессия БД
        
    Raises:
        HTTPException 404: Вопрос не найден
    """
    try:
        success = TheoryQuestionCRUD.delete_question(db, question_id)
        if not success:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при удалении вопроса. Обратитесь к администратору."
        )

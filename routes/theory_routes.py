"""Theory test routes for students."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import random

from database.database import get_db
from database.crud import TheoryQuestionCRUD, TheoryTestSubmissionCRUD, UserCRUD
from database.schemas import (
    TheoryQuestionPublic,
    TheoryTestSubmitRequest,
    TheoryTestSubmitResponse,
    QuestionResultDetail
)

router = APIRouter(prefix="/theory", tags=["theory"])


@router.get("/questions", response_model=List[TheoryQuestionPublic])
def get_theory_questions(db: Session = Depends(get_db)):
    """
    Получить все теоретические вопросы в случайном порядке.
    
    Возвращает вопросы БЕЗ информации о правильности ответов.
    Порядок вопросов и вариантов ответов рандомизирован.
    
    Returns:
        Список всех вопросов в случайном порядке
    """
    try:
        questions = TheoryQuestionCRUD.get_all_questions(db)
        
        # Рандомизируем порядок вопросов
        random.shuffle(questions)
        
        # Рандомизируем порядок вариантов ответов для каждого вопроса
        for question in questions:
            random.shuffle(question.answer_options)
        
        return questions
    except Exception as e:
        logging.error(f"Error fetching theory questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении вопросов. Обратитесь к администратору."
        )


@router.post("/submit", response_model=TheoryTestSubmitResponse)
def submit_theory_test(
    test_data: TheoryTestSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Проверить ответы на теоретический тест.
    
    Студент может ответить ТОЛЬКО ОДИН РАЗ.
    
    Args:
        test_data: Ответы студента на все вопросы
        db: Сессия БД
        
    Returns:
        Результаты теста с детализацией по каждому вопросу
        
    Raises:
        HTTPException 400: Пользователь уже отвечал на тест
        HTTPException 404: Пользователь или вопрос не найден
    """
    try:
        # Проверяем существование пользователя
        user = UserCRUD.get_user_by_id(db, test_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем, не отвечал ли пользователь уже
        if TheoryTestSubmissionCRUD.has_user_answered(db, test_data.user_id):
            raise HTTPException(
                status_code=400,
                detail="Вы уже проходили тест. Повторное прохождение невозможно."
            )
        
        results = []
        correct_count = 0
        incorrect_count = 0
        
        # Проверяем каждый ответ
        for answer in test_data.answers:
            question = TheoryQuestionCRUD.get_question_by_id(db, answer.question_id)
            
            if not question:
                raise HTTPException(
                    status_code=404,
                    detail=f"Вопрос с ID {answer.question_id} не найден"
                )
            
            # Получаем правильные ответы
            correct_option_ids = [
                opt.id for opt in question.answer_options if opt.is_correct
            ]
            
            # Сортируем для корректного сравнения
            user_answers_sorted = sorted(answer.selected_option_ids)
            correct_answers_sorted = sorted(correct_option_ids)
            
            # Проверяем правильность ответа
            is_correct = user_answers_sorted == correct_answers_sorted
            
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
            
            # Сохраняем результат в БД
            TheoryTestSubmissionCRUD.create_submission(
                db=db,
                user_id=test_data.user_id,
                question_id=answer.question_id,
                selected_option_ids=answer.selected_option_ids,
                is_correct=is_correct,
                correct_option_ids=correct_option_ids
            )
            
            # Добавляем детали в результат
            results.append(QuestionResultDetail(
                question_id=question.id,
                question_text=question.question_text,
                question_type=question.question_type,
                is_correct=is_correct,
                selected_option_ids=answer.selected_option_ids,
                correct_option_ids=correct_option_ids
            ))
        
        total_questions = len(test_data.answers)
        score_percentage = round((correct_count / total_questions * 100) if total_questions > 0 else 0, 2)
        
        return TheoryTestSubmitResponse(
            user_id=test_data.user_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            score_percentage=score_percentage,
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error submitting theory test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при проверке теста. Обратитесь к администратору."
        )


@router.get("/results/{user_id}")
def get_user_test_results(user_id: int, db: Session = Depends(get_db)):
    """
    Получить результаты теста пользователя.
    
    Args:
        user_id: ID пользователя
        db: Сессия БД
        
    Returns:
        Статистика по тесту пользователя
        
    Raises:
        HTTPException 404: Пользователь не найден или не проходил тест
    """
    try:
        user = UserCRUD.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not TheoryTestSubmissionCRUD.has_user_answered(db, user_id):
            raise HTTPException(
                status_code=404,
                detail="Пользователь еще не проходил тест"
            )
        
        results = TheoryTestSubmissionCRUD.get_user_test_results(db, user_id)
        return {
            "user_id": user_id,
            **results
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching test results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении результатов. Обратитесь к администратору."
        )

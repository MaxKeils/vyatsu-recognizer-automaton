from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import (
    Configuration, Task, User, Submission, StudentProgress, VirtualVariant,
    TheoryQuestion, TheoryAnswerOption
)
from database.schemas import (
    ConfigurationRequest, TaskRequest, UserRequest, UserUpdateRequest, 
    SubmissionRequest, TheoryQuestionCreate, TheoryQuestionUpdate
)


class ConfigurationCRUD:
    @staticmethod
    def get_configuration(db: Session) -> Optional[Configuration]:
        return db.query(Configuration).first()
    
    @staticmethod
    def create_or_update_configuration(
        db: Session, 
        config_data: ConfigurationRequest
    ) -> Configuration:
        config = db.query(Configuration).first()
        
        if config:
            config.duration = config_data.duration
            config.difficulty_mode = config_data.difficulty_mode.value
        else:
            from service.auth_service import AuthService
            config = Configuration(
                duration=config_data.duration,
                difficulty_mode=config_data.difficulty_mode.value,
                password_hash=AuthService.generate_default_password_hash()
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def update_password(db: Session, new_password_hash: str) -> Optional[Configuration]:
        """
        Обновить пароль администратора в конфигурации.
        
        Args:
            db: Сессия БД
            new_password_hash: Новый хеш пароля
            
        Returns:
            Обновленная конфигурация или None
        """
        config = db.query(Configuration).first()
        if config:
            config.password_hash = new_password_hash
            db.commit()
            db.refresh(config)
        return config
    
    @staticmethod
    def verify_admin_password(db: Session, password: str) -> bool:
        """
        Проверить пароль администратора.
        
        Args:
            db: Сессия БД
            password: Пароль для проверки
            
        Returns:
            True если пароль верный, False иначе
        """
        from service.auth_service import AuthService
        config = db.query(Configuration).first()
        if not config or not config.password_hash:
            return False
        return AuthService.verify_password(password, config.password_hash)


class TaskCRUD:
    @staticmethod
    def get_all_tasks(db: Session) -> List[Task]:
        return db.query(Task).all()
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def create_task(db: Session, task_data: TaskRequest) -> Task:
        task = Task(
            description=task_data.description,
            task=task_data.task
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskRequest) -> Optional[Task]:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.description = task_data.description
            task.task = task_data.task
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False


class UserCRUD:

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        return db.query(User).all()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_full_name(db: Session, full_name: str) -> Optional[User]:
        return db.query(User).filter(User.full_name == full_name).first()
    
    @staticmethod
    def create_or_get_user_by_full_name(db: Session, user_data: UserRequest) -> User:
        existing_user = UserCRUD.get_user_by_full_name(db, user_data.full_name)
        
        if existing_user:
            if user_data.group_name:
                existing_user.group_name = user_data.group_name
                db.commit()
                db.refresh(existing_user)
            return existing_user
        
        user = User(
            full_name=user_data.full_name,
            group_name=user_data.group_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdateRequest) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.group_name is not None:
            user.group_name = user_data.group_name
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False


class SubmissionCRUD:

    @staticmethod
    def get_submissions_by_user_id(db: Session, user_id: int) -> List[Submission]:
        """
        Получить все submissions пользователя по секциям автоматов.
        
        ВАЖНО: Фильтрует is_test=FALSE, чтобы тесты по теории не попадали в результаты.
        """
        return db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.is_test == False
        ).all()
    
    @staticmethod
    def get_submission_by_id(db: Session, submission_id: int) -> Optional[Submission]:
        return db.query(Submission).filter(Submission.id == submission_id).first()
    
    @staticmethod
    def create_submission(db: Session, submission_data: SubmissionRequest) -> Submission:
        submission = Submission(
            task_id=submission_data.task_id,
            user_id=submission_data.user_id,
            submitted_task=submission_data.submitted_task,
            errors=None 
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    
    @staticmethod
    def create_section_submission(
        db: Session,
        task_id: int,
        user_id: int,
        progress_id: Optional[int],
        section_number: int,
        difficulty_mode: str,
        submitted_data: Dict[str, Any],
        errors_data: Dict[str, Any]
    ) -> Submission:
        """
        Создать submission для секции с полными ошибками.
        
        Args:
            db: Сессия БД
            task_id: ID задания (виртуальный вариант)
            user_id: ID пользователя
            progress_id: ID прогресса студента (может быть None)
            section_number: Номер секции (1, 2, 3)
            difficulty_mode: Режим сложности
            submitted_data: Отправленные данные секции
            errors_data: Полная информация об ошибках (с EASY_MODE)
            
        Returns:
            Созданный Submission
        """
        submission = Submission(
            task_id=task_id,
            user_id=user_id,
            progress_id=progress_id,
            section_number=section_number,
            difficulty_mode=difficulty_mode,
            submitted_task=submitted_data,
            errors=errors_data
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    
    @staticmethod
    def update_submission_errors(
        db: Session, 
        submission_id: int, 
        errors: Dict[str, Any]
    ) -> Optional[Submission]:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.errors = errors
            db.commit()
            db.refresh(submission)
        return submission
    
    @staticmethod
    def get_submission_errors(db: Session, submission_id: int) -> Optional[Dict[str, Any]]:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        return submission.errors if submission else None


class StudentProgressCRUD:
    """CRUD операции для прогресса студентов."""
    
    @staticmethod
    def get_progress(db: Session, user_id: int, task_id: int) -> Optional[StudentProgress]:
        return db.query(StudentProgress).filter(
            StudentProgress.user_id == user_id,
            StudentProgress.task_id == task_id
        ).first()
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int) -> List[StudentProgress]:
        return db.query(StudentProgress).filter(StudentProgress.user_id == user_id).all()
    
    @staticmethod
    def create_progress(
        db: Session,
        user_id: int,
        task_id: int,
        difficulty_mode: Optional[str] = None
    ) -> StudentProgress:
        progress = StudentProgress(
            user_id=user_id,
            task_id=task_id,
            current_section=1,
            difficulty_mode=difficulty_mode
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def update_section_data(
        db: Session,
        progress_id: int,
        section_number: int,
        section_data: Dict[str, Any]
    ) -> Optional[StudentProgress]:
        progress = db.query(StudentProgress).filter(StudentProgress.id == progress_id).first()
        if not progress:
            return None
        
        if section_number == 1:
            progress.section_1_data = section_data
        elif section_number == 2:
            progress.section_2_data = section_data
        elif section_number == 3:
            progress.section_3_data = section_data
        
        # Обновляем текущую секцию если она меньше
        if progress.current_section < section_number:
            progress.current_section = section_number
        
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def increment_current_section(
        db: Session, 
        progress_id: int, 
        section_number: int
    ) -> Optional[StudentProgress]:
        """
        Увеличивает current_section только если section_number > current_section.
        Это предотвращает повторное увеличение при переотправке уже пройденной секции.
        
        Args:
            db: Сессия БД
            progress_id: ID прогресса
            section_number: Номер текущей секции
            
        Returns:
            Обновленный прогресс или None
        """
        progress = db.query(StudentProgress).filter(StudentProgress.id == progress_id).first()
        if progress and section_number > progress.current_section:
            progress.current_section = section_number + 1
            db.commit()
            db.refresh(progress)
        return progress
    
    @staticmethod
    def mark_completed(db: Session, progress_id: int) -> Optional[StudentProgress]:
        progress = db.query(StudentProgress).filter(StudentProgress.id == progress_id).first()
        if progress:
            progress.is_completed = True
            db.commit()
            db.refresh(progress)
        return progress


class VirtualVariantCRUD:
    """CRUD операции для виртуальных вариантов."""
    
    @staticmethod
    def get_all_virtual_variants(db: Session) -> List[VirtualVariant]:
        return db.query(VirtualVariant).order_by(VirtualVariant.display_number).all()
    
    @staticmethod
    def get_virtual_variant_by_id(db: Session, variant_id: int) -> Optional[VirtualVariant]:
        return db.query(VirtualVariant).filter(VirtualVariant.id == variant_id).first()
    
    @staticmethod
    def get_virtual_variant_by_display_number(db: Session, display_number: int) -> Optional[VirtualVariant]:
        return db.query(VirtualVariant).filter(VirtualVariant.display_number == display_number).first()
    
    @staticmethod
    def get_task_by_virtual_variant(db: Session, display_number: int) -> Optional[Task]:
        """
        Получить реальное задание по номеру виртуального варианта.
        
        Args:
            db: Сессия БД
            display_number: Номер виртуального варианта (который видит студент)
            
        Returns:
            Task или None если виртуальный вариант не найден
        """
        virtual_variant = VirtualVariantCRUD.get_virtual_variant_by_display_number(db, display_number)
        if not virtual_variant:
            return None
        return TaskCRUD.get_task_by_id(db, virtual_variant.real_task_id)
    
    @staticmethod
    def create_virtual_variant(db: Session, real_task_id: int, display_number: int) -> VirtualVariant:
        """
        Создать виртуальный вариант.
        
        Args:
            db: Сессия БД
            real_task_id: ID реального задания
            display_number: Номер для отображения
            
        Returns:
            Созданный виртуальный вариант
            
        Raises:
            IntegrityError: Если display_number уже существует
        """
        virtual_variant = VirtualVariant(
            real_task_id=real_task_id,
            display_number=display_number
        )
        db.add(virtual_variant)
        db.commit()
        db.refresh(virtual_variant)
        return virtual_variant
    
    @staticmethod
    def update_virtual_variant(
        db: Session,
        variant_id: int,
        real_task_id: Optional[int] = None,
        display_number: Optional[int] = None
    ) -> Optional[VirtualVariant]:
        """
        Обновить виртуальный вариант.
        
        Args:
            db: Сессия БД
            variant_id: ID виртуального варианта
            real_task_id: Новый ID реального задания (опционально)
            display_number: Новый номер для отображения (опционально)
            
        Returns:
            Обновленный виртуальный вариант или None если не найден
        """
        variant = db.query(VirtualVariant).filter(VirtualVariant.id == variant_id).first()
        if not variant:
            return None
        
        if real_task_id is not None:
            variant.real_task_id = real_task_id
        
        if display_number is not None:
            variant.display_number = display_number
        
        db.commit()
        db.refresh(variant)
        return variant
    
    @staticmethod
    def delete_virtual_variant(db: Session, variant_id: int) -> bool:
        """
        Удалить виртуальный вариант.
        
        Args:
            db: Сессия БД
            variant_id: ID виртуального варианта
            
        Returns:
            True если удален, False если не найден
        """
        variant = db.query(VirtualVariant).filter(VirtualVariant.id == variant_id).first()
        if variant:
            db.delete(variant)
            db.commit()
            return True
        return False


class TheoryQuestionCRUD:
    """CRUD операции для теоретических вопросов."""
    
    @staticmethod
    def create_question(db: Session, question_data: TheoryQuestionCreate) -> TheoryQuestion:
        """
        Создать новый теоретический вопрос с вариантами ответов.
        
        Args:
            db: Сессия БД
            question_data: Данные вопроса с вариантами ответов
            
        Returns:
            Созданный вопрос
        """
        # Создаем вопрос
        db_question = TheoryQuestion(
            question_text=question_data.question_text,
            question_type=question_data.question_type
        )
        db.add(db_question)
        db.flush()  # Получаем ID вопроса
        
        # Создаем варианты ответов
        for option_data in question_data.answer_options:
            db_option = TheoryAnswerOption(
                question_id=db_question.id,
                option_text=option_data.option_text,
                is_correct=option_data.is_correct,
                option_order=option_data.option_order
            )
            db.add(db_option)
        
        db.commit()
        db.refresh(db_question)
        return db_question
    
    @staticmethod
    def get_all_questions(db: Session) -> List[TheoryQuestion]:
        """Получить все вопросы с вариантами ответов."""
        return db.query(TheoryQuestion).all()
    
    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[TheoryQuestion]:
        """Получить вопрос по ID."""
        return db.query(TheoryQuestion).filter(TheoryQuestion.id == question_id).first()
    
    @staticmethod
    def update_question(
        db: Session, 
        question_id: int, 
        question_data: TheoryQuestionUpdate
    ) -> Optional[TheoryQuestion]:
        """
        Обновить вопрос.
        
        Args:
            db: Сессия БД
            question_id: ID вопроса
            question_data: Новые данные вопроса
            
        Returns:
            Обновленный вопрос или None если не найден
        """
        question = db.query(TheoryQuestion).filter(TheoryQuestion.id == question_id).first()
        if not question:
            return None
        
        # Обновляем текст и тип вопроса
        if question_data.question_text is not None:
            question.question_text = question_data.question_text
        if question_data.question_type is not None:
            question.question_type = question_data.question_type
        
        # Если переданы новые варианты ответов - заменяем все
        if question_data.answer_options is not None:
            # Удаляем старые варианты
            db.query(TheoryAnswerOption).filter(
                TheoryAnswerOption.question_id == question_id
            ).delete()
            
            # Добавляем новые варианты
            for option_data in question_data.answer_options:
                db_option = TheoryAnswerOption(
                    question_id=question_id,
                    option_text=option_data.option_text,
                    is_correct=option_data.is_correct,
                    option_order=option_data.option_order
                )
                db.add(db_option)
        
        db.commit()
        db.refresh(question)
        return question
    
    @staticmethod
    def delete_question(db: Session, question_id: int) -> bool:
        """
        Удалить вопрос (варианты ответов удалятся автоматически через cascade).
        
        Args:
            db: Сессия БД
            question_id: ID вопроса
            
        Returns:
            True если удален, False если не найден
        """
        question = db.query(TheoryQuestion).filter(TheoryQuestion.id == question_id).first()
        if question:
            db.delete(question)
            db.commit()
            return True
        return False


class TheoryTestSubmissionCRUD:
    """
    CRUD операции для результатов тестов по теории.
    Использует таблицу submissions с is_test=TRUE.
    
    Структура данных:
    - is_test = TRUE
    - task_id = NULL (не нужен для теории)
    - submitted_task = {"question_id": N, "selected_option_ids": [1, 2, 3]}
    - errors = {"is_correct": true/false, "correct_option_ids": [1, 2]}
    """
    
    @staticmethod
    def create_submission(
        db: Session,
        user_id: int,
        question_id: int,
        selected_option_ids: List[int],
        is_correct: bool,
        correct_option_ids: List[int]
    ) -> Submission:
        """
        Создать запись о результате ответа на вопрос теории.
        
        Args:
            db: Сессия БД
            user_id: ID пользователя
            question_id: ID вопроса
            selected_option_ids: ID выбранных вариантов
            is_correct: Правильно ли ответил
            correct_option_ids: ID правильных вариантов
            
        Returns:
            Созданный submission
        """
        submission = Submission(
            user_id=user_id,
            task_id=None,  # Для теории task не нужен
            is_test=True,
            submitted_task={
                "question_id": question_id,
                "selected_option_ids": selected_option_ids
            },
            errors={
                "is_correct": is_correct,
                "correct_option_ids": correct_option_ids
            }
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    
    @staticmethod
    def get_user_test_submissions(db: Session, user_id: int) -> List[Submission]:
        """Получить все submissions пользователя по теории (is_test=TRUE)."""
        return db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.is_test == True
        ).all()
    
    @staticmethod
    def has_user_answered(db: Session, user_id: int) -> bool:
        """Проверить, отвечал ли пользователь на тест по теории."""
        count = db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.is_test == True
        ).count()
        return count > 0
    
    @staticmethod
    def get_user_test_results(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Получить результаты теста пользователя.
        
        Returns:
            Dict с total_questions, correct_answers, incorrect_answers
        """
        submissions = db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.is_test == True
        ).all()
        
        total = len(submissions)
        correct = sum(1 for s in submissions if s.errors and s.errors.get("is_correct") == True)
        incorrect = total - correct
        
        return {
            "total_questions": total,
            "correct_answers": correct,
            "incorrect_answers": incorrect,
            "score_percentage": round((correct / total * 100) if total > 0 else 0, 2)
        }
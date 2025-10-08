from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import Configuration, Task, User, Submission, StudentProgress, VirtualVariant
from database.schemas import (
    ConfigurationRequest, TaskRequest, UserRequest, UserUpdateRequest, 
    SubmissionRequest
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
        return db.query(Submission).filter(Submission.user_id == user_id).all()
    
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
        task_id: int
    ) -> StudentProgress:
        progress = StudentProgress(
            user_id=user_id,
            task_id=task_id,
            current_section=1
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
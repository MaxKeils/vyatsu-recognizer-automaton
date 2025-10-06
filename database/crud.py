"""CRUD operations for database models."""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from database.models import Configuration, Task, User, Submission, HintLevelEnum
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
            # Update existing
            config.duration = config_data.duration
            config.hint_level = config_data.hint_level.value
        else:
            # Create new
            config = Configuration(
                duration=config_data.duration,
                hint_level=config_data.hint_level.value
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return config


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
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_or_get_user_by_email(db: Session, user_data: UserRequest) -> User:
        existing_user = UserCRUD.get_user_by_email(db, user_data.email)
        
        if existing_user:
            # Update full_name if provided
            if user_data.full_name:
                existing_user.full_name = user_data.full_name
                db.commit()
                db.refresh(existing_user)
            return existing_user
        
        # Create new user
        if not user_data.full_name:
            raise ValueError("full_name is required for new user")
            
        user = User(
            full_name=user_data.full_name,
            email=user_data.email
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
        
        if user_data.email is not None:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            if existing_user:
                raise IntegrityError("Email already taken", None, None)
            user.email = user_data.email
        
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
            errors=None  # Will be populated by verification service
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
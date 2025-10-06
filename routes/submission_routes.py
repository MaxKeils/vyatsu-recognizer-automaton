"""API routes for submission management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database.database import get_db
from database.crud import SubmissionCRUD, UserCRUD, TaskCRUD
from database.schemas import (
    SubmissionRequest, SubmissionResponse, ErrorsResponse
)
from service.automaton_service import AutomatonService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("/user/{user_id}", response_model=List[SubmissionResponse])
def get_user_submissions(user_id: int, db: Session = Depends(get_db)):
    """Get all submissions by user ID."""
    # Check if user exists
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    submissions = SubmissionCRUD.get_submissions_by_user_id(db, user_id)
    return submissions


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission_by_id(submission_id: int, db: Session = Depends(get_db)):
    """Get submission by ID with full details."""
    submission = SubmissionCRUD.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get("/{submission_id}/errors", response_model=ErrorsResponse)
def get_submission_errors(submission_id: int, db: Session = Depends(get_db)):
    """Get errors for a specific submission."""
    submission = SubmissionCRUD.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return ErrorsResponse(
        submission_id=submission_id,
        errors=submission.errors
    )


@router.post("/", response_model=SubmissionResponse)
def create_submission(
    submission_data: SubmissionRequest,
    db: Session = Depends(get_db)
):
    """Create a new submission and verify it against reference automaton."""
    # Validate that user and task exist
    user = UserCRUD.get_user_by_id(db, submission_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    task = TaskCRUD.get_task_by_id(db, submission_data.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create submission
    submission = SubmissionCRUD.create_submission(db, submission_data)
    
    # Verify submission against reference automaton
    try:
        service = AutomatonService()
        
        # Convert submitted task to StudentAutomaton and reference task to ReferenceAutomaton
        from models.automaton import StudentAutomaton, ReferenceAutomaton
        
        student_automaton = StudentAutomaton(**submission_data.submitted_task)
        reference_automaton = ReferenceAutomaton(**task.task)
        
        # Verify automatons
        verification_result = service.verify_automatons(student_automaton, reference_automaton)
        
        # Update submission with errors
        errors = {
            "is_correct": verification_result.is_correct,
            "differences": verification_result.differences,
            "hints": verification_result.hints
        }
        
        submission = SubmissionCRUD.update_submission_errors(db, submission.id, errors)
        
    except Exception as e:
        # If verification fails, still save submission but mark error
        error_info = {
            "verification_error": str(e),
            "is_correct": False
        }
        submission = SubmissionCRUD.update_submission_errors(db, submission.id, error_info)
    
    return submission
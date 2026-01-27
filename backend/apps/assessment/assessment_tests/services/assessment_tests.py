from decimal import Decimal
from typing import Optional
from datetime import datetime

from django.utils import timezone
from django.db import transaction
from pydantic import BaseModel, Field, field_validator

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.test_results.models import TestResult
from apps.candidate.recruiters.models import Recruiter


# Logic Upgrade complete

class StartTestInput(BaseModel):
    """Input for starting a test."""
    test_id: int
    recruiter_id: int


class SubmitTestInput(BaseModel):
    """Input for submitting a test."""
    test_id: int
    recruiter_id: int
    answers: list[dict]
    started_at: datetime
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v):
        if not v:
            raise ValueError('Answers cannot be empty')
        for ans in v:
            if 'question_id' not in ans:
                raise ValueError('Each answer must have question_id')
            if 'answer' not in ans:
                raise ValueError('Each answer must have answer')
        return v

def start_test(input_data: StartTestInput) -> dict:
    """
    Start a test session for a recruiter.
    """
    # Verify test exists and is active
    test = AssessmentTest.objects.get(id=input_data.test_id)
    
    if not test.is_active:
        raise ValueError('This test is not currently active')
    
    # Verify recruiter exists
    recruiter = Recruiter.objects.get(id=input_data.recruiter_id)
    
    # Check retake eligibility (Dynamic from model)
    eligibility = check_retake_eligibility(test.id, recruiter.id)
    
    if not eligibility['can_retake']:
        raise ValueError(eligibility.get('message', 'Retake limit exceeded or wait period active'))
    
    # Prepare questions without correct answers
    questions_data = test.questions_data or {}
    questions = questions_data.get('questions', [])
    
    safe_questions = []
    for q in questions:
        safe_q = {
            'id': q.get('id'),
            'type': q.get('type'),
            'question': q.get('question'),
            'options': q.get('options'),
            'points': q.get('points', 1),
        }
        safe_questions.append(safe_q)
    
    return {
        'test_id': test.id,
        'test_title': test.title,
        'duration_minutes': test.duration_minutes,
        'total_questions': test.total_questions,
        'questions': safe_questions,
        'started_at': timezone.now(),
        'attempt_number': eligibility['attempts_used'] + 1,
    }


def submit_test(input_data: SubmitTestInput) -> TestResult:
    """
    Submit test answers and calculate score.
    
    Args:
        input_data: SubmitTestInput with test_id, recruiter_id, answers
        
    Returns:
        TestResult instance
        
    Raises:
        AssessmentTest.DoesNotExist: If test not found
        Recruiter.DoesNotExist: If recruiter not found
    """
    test = AssessmentTest.objects.get(id=input_data.test_id)
    recruiter = Recruiter.objects.get(id=input_data.recruiter_id)
    
    # Calculate score
    score_result = calculate_score(test, input_data.answers)
    
    # Calculate time taken
    started_at = input_data.started_at
    if started_at.tzinfo is None:
        started_at = timezone.make_aware(started_at)
    
    completed_at = timezone.now()
    time_taken = (completed_at - started_at).total_seconds() / 60
    time_taken_minutes = int(time_taken)
    
    # Determine if passed
    passing_score = test.passing_score or Decimal('60.00')
    passed = score_result['percentage_score'] >= passing_score
    
    # Create result
    with transaction.atomic():
        result = TestResult.objects.create(
            assessment_test=test,
            recruiter=recruiter,
            score=score_result['score'],
            percentage_score=score_result['percentage_score'],
            time_taken_minutes=time_taken_minutes,
            answers_data={'answers': input_data.answers},
            passed=passed,
            started_at=started_at,
        )
    
    return result


def calculate_score(test: AssessmentTest, answers: list[dict]) -> dict:
    """
    Calculate score based on answers.
    
    Supports question types:
    - multiple_choice: Exact match
    - true_false: Boolean match
    - text: Case-insensitive match (basic)
    
    Args:
        test: AssessmentTest instance
        answers: List of {question_id, answer}
        
    Returns:
        dict with score, percentage_score, correct_count, details
    """
    questions_data = test.questions_data or {}
    questions = questions_data.get('questions', [])
    
    # Build question lookup
    question_map = {q['id']: q for q in questions}
    
    # Build answer lookup
    answer_map = {a['question_id']: a['answer'] for a in answers}
    
    total_points = 0
    earned_points = 0
    correct_count = 0
    details = []
    
    for q in questions:
        q_id = q['id']
        q_type = q.get('type', 'multiple_choice')
        correct_answer = q.get('correct_answer')
        points = q.get('points', 1)
        total_points += points
        
        user_answer = answer_map.get(q_id)
        is_correct = False
        
        if user_answer is not None and correct_answer is not None:
            if q_type == 'multiple_choice':
                is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()
            elif q_type == 'true_false':
                # Handle boolean comparison
                user_bool = _to_bool(user_answer)
                correct_bool = _to_bool(correct_answer)
                is_correct = user_bool == correct_bool
            elif q_type == 'text':
                # Basic case-insensitive comparison
                is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            else:
                # Default: exact match
                is_correct = user_answer == correct_answer
        
        if is_correct:
            earned_points += points
            correct_count += 1
        
        details.append({
            'question_id': q_id,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'points_earned': points if is_correct else 0,
        })
    
    # Calculate percentage
    if total_points > 0:
        percentage = (earned_points / total_points) * 100
    else:
        percentage = 0
    
    return {
        'score': Decimal(str(earned_points)).quantize(Decimal('0.01')),
        'percentage_score': Decimal(str(percentage)).quantize(Decimal('0.01')),
        'correct_count': correct_count,
        'total_questions': len(questions),
        'total_points': total_points,
        'earned_points': earned_points,
        'details': details,
    }


def get_test_results(test_id: int, recruiter_id: int) -> list[TestResult]:
    """
    Get all test results for a specific test and recruiter.
    
    Args:
        test_id: Assessment test ID
        recruiter_id: Recruiter ID
        
    Returns:
        List of TestResult instances
    """
    return list(
        TestResult.objects
        .filter(
            assessment_test_id=test_id,
            recruiter_id=recruiter_id
        )
        .order_by('-completed_at')
    )


def check_retake_eligibility(test_id: int, recruiter_id: int) -> dict:
    """
    Check if recruiter can retake a test based on model configuration.
    """
    test = AssessmentTest.objects.get(id=test_id)
    
    results = TestResult.objects.filter(
        assessment_test_id=test_id,
        recruiter_id=recruiter_id
    ).order_by('-completed_at')
    
    attempt_count = results.count()
    latest_result = results.first()
    
    max_attempts = test.max_retakes + 1  # Original + Max Retakes
    
    can_retake = True
    message = "Available"
    next_available_date = None
    days_to_wait = 0
    
    # 1. Check max attempts
    if attempt_count >= max_attempts:
        can_retake = False
        message = f"Bạn đã đạt giới hạn tối đa {max_attempts} lần thi cho bài test này."
    
    # 2. Check wait period if there's a previous result
    elif latest_result and test.retake_wait_days > 0:
        wait_period = timezone.timedelta(days=test.retake_wait_days)
        next_available_date = latest_result.completed_at + wait_period
        
        if timezone.now() < next_available_date:
            can_retake = False
            # Calculate days remaining (round up)
            delta = next_available_date - timezone.now()
            days_remaining = delta.days + (1 if delta.seconds > 0 else 0)
            message = f"Bạn cần chờ thêm {days_remaining} ngày để có thể thi lại bài test này."
            days_to_wait = days_remaining

    return {
        'can_retake': can_retake,
        'message': message,
        'attempts_used': attempt_count,
        'attempts_remaining': max(0, max_attempts - attempt_count),
        'max_attempts': max_attempts,
        'next_available_date': next_available_date.isoformat() if next_available_date else None,
        'wait_days_remaining': days_to_wait,
    }


def _to_bool(value) -> Optional[bool]:
    """Convert various values to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'y')
    if isinstance(value, (int, float)):
        return bool(value)
    return None

"""
Test Results Service

Business logic for test results - certificates, retakes.
"""
from typing import Optional
from datetime import datetime

from django.db.models import QuerySet
from pydantic import BaseModel

from apps.assessment.test_results.models import TestResult
from apps.assessment.assessment_tests.models import AssessmentTest
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.assessment_tests.services.assessment_tests import (
    start_test,
    StartTestInput,
    check_retake_eligibility,
    MAX_RETAKE_ATTEMPTS,
)


# ============ Service Functions ============

def get_recruiter_test_results(recruiter_id: int) -> QuerySet[TestResult]:
    """
    Get all test results for a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        
    Returns:
        QuerySet of TestResult ordered by date
    """
    return (
        TestResult.objects
        .filter(recruiter_id=recruiter_id)
        .select_related('assessment_test')
        .order_by('-completed_at')
    )


def get_result_by_id(result_id: int) -> Optional[TestResult]:
    """
    Get single test result by ID.
    
    Args:
        result_id: Result ID
        
    Returns:
        TestResult or None
    """
    try:
        return (
            TestResult.objects
            .select_related('assessment_test', 'recruiter__user')
            .get(id=result_id)
        )
    except TestResult.DoesNotExist:
        return None


def get_certificate_data(result_id: int) -> Optional[dict]:
    """
    Get certificate data for a test result.
    
    Args:
        result_id: Result ID
        
    Returns:
        dict with certificate data or None
    """
    result = get_result_by_id(result_id)
    if not result:
        return None
    
    # Only passed results get certificates
    validity_status = 'valid' if result.passed else 'not_passed'
    
    return {
        'result_id': result.id,
        'recruiter_name': result.recruiter.user.full_name,
        'test_title': result.assessment_test.title,
        'test_type': result.assessment_test.test_type,
        'score': result.score,
        'percentage_score': result.percentage_score,
        'passed': result.passed,
        'completed_at': result.completed_at,
        'certificate_url': result.certificate_url,
        'validity_status': validity_status,
    }


def request_retake(result_id: int, recruiter_id: int) -> dict:
    """
    Request to retake a test based on a previous result.
    
    Args:
        result_id: Previous result ID
        recruiter_id: Recruiter ID
        
    Returns:
        dict with retake session or error
        
    Raises:
        TestResult.DoesNotExist: If result not found
        ValueError: If retake not allowed
    """
    result = get_result_by_id(result_id)
    if not result:
        raise TestResult.DoesNotExist('Result not found')
    
    # Verify ownership
    if result.recruiter_id != recruiter_id:
        raise ValueError('This result does not belong to the current user')
    
    test_id = result.assessment_test_id
    
    # Check eligibility
    eligibility = check_retake_eligibility(test_id, recruiter_id)
    
    if not eligibility['can_retake']:
        return {
            'can_retake': False,
            'session': None,
            'message': f'Maximum retake limit ({MAX_RETAKE_ATTEMPTS}) exceeded',
            'eligibility': eligibility,
        }
    
    # Start new test session
    input_data = StartTestInput(
        test_id=test_id,
        recruiter_id=recruiter_id
    )
    session = start_test(input_data)
    
    return {
        'can_retake': True,
        'session': session,
        'message': 'Retake session started',
        'eligibility': eligibility,
    }


def get_application_test_results(application_id: int) -> QuerySet[TestResult]:
    """
    Get test results for a specific application.
    
    Args:
        application_id: Application ID
        
    Returns:
        QuerySet of TestResult
    """
    return (
        TestResult.objects
        .filter(application_id=application_id)
        .select_related('assessment_test')
        .order_by('-completed_at')
    )


def get_job_required_tests(job_id: int) -> list[dict]:
    """
    Get required tests for a job.
    
    Args:
        job_id: Job ID
        
    Returns:
        List of required test info
    """
    from apps.assessment.job_assessment_requirements.models import JobAssessmentRequirement
    
    requirements = (
        JobAssessmentRequirement.objects
        .filter(job_id=job_id)
        .select_related('assessment_test')
    )
    
    result = []
    for req in requirements:
        test = req.assessment_test
        result.append({
            'test_id': test.id,
            'test_title': test.title,
            'test_type': test.test_type,
            'is_required': req.is_mandatory,
            'minimum_score': req.minimum_score,
        })
    
    return result


def check_application_test_status(application_id: int, job_id: int) -> dict:
    """
    Check if application has completed all required tests.
    
    Args:
        application_id: Application ID
        job_id: Job ID
        
    Returns:
        dict with status summary
    """
    required_tests = get_job_required_tests(job_id)
    results = get_application_test_results(application_id)
    
    # Build result map
    result_map = {}
    for r in results:
        test_id = r.assessment_test_id
        # Keep best result
        if test_id not in result_map or r.score > result_map[test_id].score:
            result_map[test_id] = r
    
    completed = []
    pending = []
    failed = []
    
    for req in required_tests:
        test_id = req['test_id']
        min_score = req['minimum_score'] or req.get('passing_score', 60)
        
        if test_id in result_map:
            result = result_map[test_id]
            if result.passed and result.percentage_score >= min_score:
                completed.append({
                    'test_id': test_id,
                    'test_title': req['test_title'],
                    'score': float(result.percentage_score),
                })
            else:
                failed.append({
                    'test_id': test_id,
                    'test_title': req['test_title'],
                    'score': float(result.percentage_score),
                    'required_score': float(min_score),
                })
        else:
            pending.append({
                'test_id': test_id,
                'test_title': req['test_title'],
                'is_required': req['is_required'],
            })
    
    all_required_passed = len([p for p in pending if True]) == 0 and len(failed) == 0
    
    return {
        'all_required_passed': all_required_passed,
        'completed': completed,
        'pending': pending,
        'failed': failed,
        'total_required': len(required_tests),
        'total_completed': len(completed),
    }

from typing import Optional
from pydantic import BaseModel
from django.db import transaction
from django.utils import timezone

from apps.recruitment.interviews.models import Interview
from apps.recruitment.applications.models import Application
from apps.email.services import EmailService


class InterviewCreateInput(BaseModel):
    """
        Pydantic input model cho tạo interview
    """
    application_id: int
    interview_type_id: int
    scheduled_at: str  # ISO format datetime
    duration_minutes: int = 60
    address_id: Optional[int] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdateInput(BaseModel):
    """
        Pydantic input model cho cập nhật interview
    """
    interview_type_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    address_id: Optional[int] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    feedback: Optional[str] = None
    result: Optional[str] = None


@transaction.atomic
def create_interview(data: InterviewCreateInput, user) -> Interview:
    """
        Tạo lịch phỏng vấn mới.
    """
    application = Application.objects.get(id=data.application_id)
    
    # Kiểm tra trạng thái đơn
    if application.status in ['rejected', 'withdrawn', 'accepted']:
        raise ValueError("Application is not in the correct state!")
    
    # Lấy số vòng phỏng vấn cuối cùng
    last_interview = Interview.objects.filter(
        application=application
    ).order_by('-round_number').first()
    
    round_number = (last_interview.round_number + 1) if last_interview else 1
    
    interview = Interview.objects.create(
        application=application,
        interview_type_id=data.interview_type_id,
        round_number=round_number,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        address_id=data.address_id,
        meeting_link=data.meeting_link if data.meeting_link else None,
        notes=data.notes if data.notes else None,
        status='scheduled',
        created_by=user
    )
    
    # Cập nhật trạng thái đơn
    if application.status != 'interview':
        application.status = 'interview'
        application.save()
    
    return interview


@transaction.atomic
def update_interview(interview: Interview, data: InterviewUpdateInput) -> Interview:
    """
        Cập nhật lịch phỏng vấn.
    """
    if interview.status == 'cancelled':
        raise ValueError("Interview is cancelled!")
    
    if data.interview_type_id is not None:
        interview.interview_type_id = data.interview_type_id
    
    if data.scheduled_at is not None:
        interview.scheduled_at = data.scheduled_at
    
    if data.duration_minutes is not None:
        interview.duration_minutes = data.duration_minutes
    
    if data.address_id is not None:
        interview.address_id = data.address_id
    
    if data.meeting_link is not None:
        interview.meeting_link = data.meeting_link if data.meeting_link else None
    
    if data.notes is not None:
        interview.notes = data.notes if data.notes else None
    
    if data.feedback is not None:
        interview.feedback = data.feedback if data.feedback else None
    
    if data.result is not None:
        interview.result = data.result
        if data.result in ['pass', 'fail']:
            interview.status = 'completed'
    
    interview.save()
    return interview


@transaction.atomic
def delete_interview(interview: Interview) -> None:
    """
        Xóa lịch phỏng vấn.
    """
    if interview.status == 'completed':
        raise ValueError("Interview is completed!")
    
    interview.delete()


@transaction.atomic
def reschedule_interview(interview: Interview, new_scheduled_at, reason: str = None) -> Interview:
    """
        Đổi lịch phỏng vấn.
    """
    if interview.status in ['completed', 'cancelled']:
        raise ValueError("Interview is completed or cancelled!")
    
    old_time = interview.scheduled_at
    interview.scheduled_at = new_scheduled_at
    interview.status = 'rescheduled'
    
    if reason:
        interview.notes = f"{interview.notes or ''}\n[Đổi lịch] {old_time} → {new_scheduled_at}: {reason}".strip()
    
    interview.save()
    return interview


@transaction.atomic
def cancel_interview(interview: Interview, reason: str = None) -> Interview:
    """
        Hủy lịch phỏng vấn.
    """
    if interview.status in ['completed', 'cancelled']:
        raise ValueError("Interview is completed or cancelled!")
    
    interview.status = 'cancelled'
    
    if reason:
        interview.notes = f"{interview.notes or ''}\n[Đã hủy] {reason}".strip()
    
    interview.save()
    return interview


@transaction.atomic
def complete_interview(interview: Interview, result: str, feedback: str = None) -> Interview:
    """
        Hoàn thành phỏng vấn với kết quả.
    """
    if interview.status in ['completed', 'cancelled']:
        raise ValueError("Phỏng vấn này đã kết thúc!")
    
    if result not in ['pass', 'fail']:
        raise ValueError("Kết quả phải là 'pass' hoặc 'fail'!")
    
    interview.status = 'completed'
    interview.result = result
    
    if feedback:
        interview.feedback = feedback
    
    interview.save()

    # Cập nhật trạng thái đơn
    application = interview.application
    has_pending_interviews = application.interviews.exclude(status__in=['completed', 'cancelled']).exists()
    
    if not has_pending_interviews:
        application.status = 'rejected' if result == 'fail' else 'review'
        application.save()

    return interview


@transaction.atomic
def add_feedback(interview: Interview, feedback: str) -> Interview:
    """
        Thêm feedback cho phỏng vấn.
    """
    interview.feedback = feedback
    interview.save()
    return interview


def send_reminder(interview: Interview, message: str = None) -> dict:
    """
        Gửi nhắc nhở (mock - sẽ tích hợp email sau).
    """
    if interview.status in ['completed', 'cancelled']:
        raise ValueError("Không thể gửi nhắc nhở cho phỏng vấn này!")
    
    applicant = interview.application.recruiter.user
    default_message = f"Nhắc nhở: Bạn có lịch phỏng vấn vào {interview.scheduled_at.strftime('%d/%m/%Y %H:%M')}"
    
    # Send Reminder Email
    EmailService.send_email(
        recipient=applicant.email,
        subject="[JobPortal] Nhắc nhở lịch phỏng vấn sắp tới",
        template_path="emails/recruitment/interview_reminder.html",
        context={
            "candidate_name": applicant.full_name,
            "job_title": interview.application.job.title,
            "company_name": interview.application.job.company.company_name,
            "interview_time": interview.scheduled_at.strftime("%H:%M ngày %d/%m/%Y"),
            "address": interview.address.full_address if interview.address else "Online",
            "meeting_link": interview.meeting_link,
            "notes": message or interview.notes,
            "recruiter_name": interview.created_by.full_name
        }
    )
    
    return {
        "status": "sent",
        "recipient": applicant.email,
        "message": message or default_message
    }

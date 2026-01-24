from typing import Optional
from pydantic import BaseModel
from django.db import transaction
from django.utils import timezone

from apps.candidate.recruiters.models import Recruiter
from apps.recruitment.jobs.models import Job
from apps.recruitment.applications.models import Application
from apps.recruitment.application_status_history.services.application_status_history import log_status_history
from apps.email.services import EmailService

class ApplicationCreateInput(BaseModel):
    """
        Pydantic input model cho tạo application
    """
    job_id: int
    cv_id: Optional[int] = None
    cover_letter: Optional[str] = None


class ApplicationUpdateInput(BaseModel):
    """
        Pydantic input model cho cập nhật application
    """
    cv_id: Optional[int] = None
    cover_letter: Optional[str] = None


@transaction.atomic
def create_application(recruiter: Recruiter, data: ApplicationCreateInput) -> Application:
    """
        Tạo đơn ứng tuyển mới.
        Raise ValueError nếu đã ứng tuyển rồi.
    """
    # Kiểm tra trùng lặp
    if Application.objects.filter(recruiter=recruiter, job_id=data.job_id).exists():
        raise ValueError("You have already applied for this job!")
    
    # Lấy job
    job = Job.objects.get(id=data.job_id)
    
    # Kiểm tra job status
    if job.status != 'published':
        raise ValueError("This job is no longer recruiting!")
    
    application = Application.objects.create(
        recruiter=recruiter,
        job=job,
        cv_id=data.cv_id,
        cover_letter=data.cover_letter,
        status='pending'
    )
    
    # Cập nhật số lượng ứng tuyển
    Job.objects.filter(id=data.job_id).update(
        application_count=job.application_count + 1
    )
    
    return application


@transaction.atomic
def update_application(application: Application, data: ApplicationUpdateInput) -> Application:
    """
        Cập nhật đơn ứng tuyển (bởi ứng viên).
        Chỉ cho cập nhật khi status = pending
    """
    if application.status not in ['pending', 'reviewing']:
        raise ValueError("You cannot update this application!")
    
    if data.cv_id is not None:
        application.cv_id = data.cv_id
    
    if data.cover_letter is not None:
        application.cover_letter = data.cover_letter if data.cover_letter else None
    
    application.save()
    return application


@transaction.atomic
def withdraw_application(application: Application) -> None:
    """
        Rút đơn ứng tuyển (bởi ứng viên).
    """
    if application.status in ['accepted', 'withdrawn']:
        raise ValueError("You cannot withdraw this application!")
    
    application.status = 'withdrawn'
    application.save()
    
    # Giảm số lượng ứng tuyển
    Job.objects.filter(id=application.job_id).update(
        application_count=application.job.application_count - 1
    )


@transaction.atomic
def change_application_status(
    application: Application, 
    status: str, 
    reviewed_by, 
    notes: str = None
) -> Application:
    """
        Đổi trạng thái đơn ứng tuyển (bởi job owner).
    """
    valid_statuses = ['reviewing', 'shortlisted', 'interview', 'offered', 'rejected', 'accepted']
    
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")
    
    if application.status == 'withdrawn':
        raise ValueError("You cannot change the status of this application!")
    
    application.status = status
    application.reviewed_by = reviewed_by
    application.reviewed_at = timezone.now()
    
    if notes:
        application.notes = notes
    
    application.save()
    
    # Send Status Update Email
    status_display = status.capitalize()
    
    EmailService.send_email(
        recipient=application.recruiter_cv.email if hasattr(application, 'recruiter_cv') and application.recruiter_cv else (application.recruiter.user.email if hasattr(application.recruiter, 'user') else None),
        subject=f"[JobPortal] Cập nhật trạng thái ứng tuyển: {application.job.title}",
        template_path="emails/recruitment/application_status.html",
        context={
            "candidate_name": application.recruiter.user.full_name,
            "job_title": application.job.title,
            "company_name": application.job.company.company_name,
            "status_class": status,
            "status_display": status_display,
            "notes": notes,
            "recruiter_name": application.job.company.user.full_name
        }
    )

    return application


@transaction.atomic
def rate_application(
    application: Application, 
    rating: int, 
    notes: str = None
) -> Application:
    """
        Đánh giá ứng viên (bởi job owner).
    """
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5!")
    
    application.rating = rating
    
    if notes:
        application.notes = notes
    
    application.save()
    return application


@transaction.atomic
def send_offer(application: Application, offer_details: str, user, salary: str = None, start_date = None) -> Application:
    """
        Gửi offer cho ứng viên (bởi job owner).
    """
    if application.status == 'withdrawn':
        raise ValueError("You cannot send an offer to this application!")
    
    if application.status == 'rejected':
        raise ValueError("You cannot send an offer to this application!")
    
    # Update status to offered
    application.status = 'offered'
    application.reviewed_by = user
    application.reviewed_at = timezone.now()
    
    # Build notes with offer details
    offer_notes = f"Offer: {offer_details}"
    if salary:
        offer_notes += f"\nSalary: {salary}"
    if start_date:
        offer_notes += f"\nStart date: {start_date}"
    
    application.notes = offer_notes
    application.save()
    
    # Send Offer Email
    EmailService.send_email(
        recipient=application.recruiter.user.email,
        subject=f"[JobPortal] Thư mời nhận việc: {application.job.title}",
        template_path="emails/recruitment/offer_letter.html",
        context={
            "candidate_name": application.recruiter.user.full_name,
            "job_title": application.job.title,
            "company_name": application.job.company.company_name,
            "header_image_url": application.job.company.banner or "",
            "salary": salary,
            "start_date": start_date,
            "offer_details": offer_details,
            "recruiter_name": user.full_name
        }
    )
    
    return application


@transaction.atomic
def applicant_withdraw(application: Application, reason: str = None) -> Application:
    """
       Ứng viên rút đơn ứng tuyển.
    """
    
    if application.status in ['accepted', 'withdrawn']:
        raise ValueError("You cannot withdraw this application!")
    
    old_status = application.status
    application.status = 'withdrawn'
    
    if reason:
        application.notes = f"Reason: {reason}"
    
    application.save()
    
    # Log history
    log_status_history(
        application,
        old_status,
        'withdrawn',
        application.recruiter.user,
        reason or "Applicant withdrew the application"
    )
    
    # Decrease job application count
    Job.objects.filter(id=application.job_id).update(
        application_count=application.job.application_count - 1
    )
    
    return application


@transaction.atomic
def bulk_action(application_ids: list, action: str, user, notes: str = None) -> dict:
    """
        Thực hiện thao tác hàng loạt trên nhiều applications.
    """

    # Get applications và validate ownership
    applications = Application.objects.filter(
        id__in=application_ids,
        job__company__user=user  # Chỉ với jobs mà user sở hữu
    ).select_related('job')
    
    if applications.count() != len(application_ids):
        raise ValueError("Some applications do not exist or you do not have permission!")
    
    processed = 0
    errors = []
    
    for app in applications:
        try:
            old_status = app.status
            
            if action == 'reject':
                app.status = 'rejected'
                app.reviewed_by = user
                app.reviewed_at = timezone.now()
                if notes:
                    app.notes = notes
                app.save()
                
            elif action == 'shortlist':
                app.status = 'shortlisted'
                app.reviewed_by = user
                app.reviewed_at = timezone.now()
                if notes:
                    app.notes = notes
                app.save()
                
            elif action == 'delete':
                app.delete()
            
            # Log history (except delete)
            if action != 'delete':
                log_status_history(
                    app,
                    old_status,
                    app.status,
                    user,
                    notes or f"Bulk {action}"
                )
            
            processed += 1
            
        except Exception as e:
            errors.append({"id": app.id, "error": str(e)})
    
    return {
        "processed": processed,
        "errors": errors
    }

from datetime import date
from ..models import AnalyticsReport
from apps.system.report_types.models import ReportType


def generate_report(
    user,
    report_type_code: str,
    period_start: date,
    period_end: date,
    company = None
) -> AnalyticsReport:
    """
        Tạo 1 bản báo cáo
    """
    
    # Kiểm tra hợp lệ
    try:
        report_type = ReportType.objects.get(type_name=report_type_code)
    except ReportType.DoesNotExist:
        # Xử lý hoặc tạo mặc định

        raise ValueError("Invalid report type")

    # Logic tính toán (Placeholder cho thực tế)
    # trong thế giới thực, chúng ta sẽ gọi một strategy dựa trên type
    metrics_data = {
        "summary": "Report generated",
        "count": 0
    }
    
    # Lưu
    report = AnalyticsReport.objects.create(
        company=company,
        report_type=report_type,
        report_period_start=period_start,
        report_period_end=period_end,
        metrics=metrics_data,
        generated_by=user
    )
    
    return report

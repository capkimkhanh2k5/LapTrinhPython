from decimal import Decimal
from typing import Optional

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter


# Region mapping for provinces
REGION_MAPPING = {
    # Northern region
    'north': [
        'ha_noi', 'hai_phong', 'quang_ninh', 'bac_ninh', 'hai_duong',
        'hung_yen', 'thai_binh', 'ha_nam', 'nam_dinh', 'ninh_binh',
        'vinh_phuc', 'bac_giang', 'phu_tho', 'thai_nguyen', 'bac_kan',
        'cao_bang', 'lang_son', 'tuyen_quang', 'ha_giang', 'lao_cai',
        'yen_bai', 'lai_chau', 'dien_bien', 'son_la', 'hoa_binh',
    ],
    # Central region
    'central': [
        'thanh_hoa', 'nghe_an', 'ha_tinh', 'quang_binh', 'quang_tri',
        'thua_thien_hue', 'da_nang', 'quang_nam', 'quang_ngai',
        'binh_dinh', 'phu_yen', 'khanh_hoa', 'ninh_thuan', 'binh_thuan',
        'kon_tum', 'gia_lai', 'dak_lak', 'dak_nong', 'lam_dong',
    ],
    # Southern region  
    'south': [
        'ho_chi_minh', 'binh_duong', 'dong_nai', 'ba_ria_vung_tau',
        'tay_ninh', 'binh_phuoc', 'long_an', 'tien_giang', 'ben_tre',
        'tra_vinh', 'vinh_long', 'dong_thap', 'an_giang', 'kien_giang',
        'can_tho', 'hau_giang', 'soc_trang', 'bac_lieu', 'ca_mau',
    ],
}


def get_province_region(province_code: Optional[str]) -> Optional[str]:
    """Get region for a province code."""
    if not province_code:
        return None
    
    province_lower = province_code.lower()
    for region, provinces in REGION_MAPPING.items():
        if province_lower in provinces:
            return region
    return None


def calculate_location_score(job: Job, recruiter: Recruiter) -> dict:
    """
    Calculate location match score between Job and Recruiter.
    
    Algorithm:
    1. If job is remote: 100 points (location doesn't matter)
    2. Compare provinces:
       - Same province: 100 points
       - Same region (North/Central/South): 70 points
       - Different region: 40 points
       - Unknown location: 50 points (neutral)
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), details
    """
    # If job is remote, location doesn't matter
    if job.is_remote:
        return {
            'score': Decimal('100.00'),
            'details': {
                'is_remote': True,
                'status': 'remote_job',
                'message': 'Remote job - location not required',
            }
        }
    
    # Get job location
    job_address = job.address
    job_province_id = None
    job_province_code = None
    
    if job_address and job_address.commune:
        job_province = job_address.commune.province
        if job_province:
            job_province_id = job_province.id
            job_province_code = job_province.code if hasattr(job_province, 'code') else None
    
    # Get recruiter location
    recruiter_address = recruiter.address
    recruiter_province_id = None
    recruiter_province_code = None
    
    if recruiter_address and recruiter_address.commune:
        recruiter_province = recruiter_address.commune.province
        if recruiter_province:
            recruiter_province_id = recruiter_province.id
            recruiter_province_code = recruiter_province.code if hasattr(recruiter_province, 'code') else None
    
    # Handle unknown locations
    if not job_province_id or not recruiter_province_id:
        return {
            'score': Decimal('50.00'),
            'details': {
                'is_remote': False,
                'job_province_id': job_province_id,
                'recruiter_province_id': recruiter_province_id,
                'status': 'unknown_location',
                'message': 'Location information incomplete',
            }
        }
    
    # Compare provinces
    if job_province_id == recruiter_province_id:
        # Same province
        score = Decimal('100.00')
        status = 'same_province'
    else:
        # Check if same region
        job_region = get_province_region(job_province_code)
        recruiter_region = get_province_region(recruiter_province_code)
        
        if job_region and recruiter_region and job_region == recruiter_region:
            score = Decimal('70.00')
            status = 'same_region'
        elif job_region and recruiter_region:
            score = Decimal('40.00')
            status = 'different_region'
        else:
            # Region unknown, use moderate score
            score = Decimal('50.00')
            status = 'region_unknown'
    
    return {
        'score': score,
        'details': {
            'is_remote': False,
            'job_province_id': job_province_id,
            'recruiter_province_id': recruiter_province_id,
            'job_region': get_province_region(job_province_code),
            'recruiter_region': get_province_region(recruiter_province_code),
            'status': status,
        }
    }

#!/usr/bin/env python
"""
Semantic Matching Accuracy Verification Script

This script tests the Gemini-based Semantic Matching logic
by running predefined test cases and checking if scores are reasonable.

Usage:
    python scripts/verify_semantic_accuracy.py

Expected Results:
    - Perfect Match: score > 80
    - Strong Mismatch: score < 40
    - Subtle Match: score 50-75
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from decimal import Decimal
from dataclasses import dataclass
from apps.assessment.ai_matching_scores.calculators.semantic_calculator import (
    get_embedding,
    cosine_similarity,
    is_semantic_enabled,
)


@dataclass
class MockJob:
    """Mock Job for testing."""
    title: str
    description: str
    requirements: str = ""
    benefits: str = ""
    level: str = "middle"
    job_type: str = "full_time"


@dataclass
class MockRecruiter:
    """Mock Recruiter for testing."""
    current_position: str
    bio: str
    years_of_experience: int = 5


# Test Cases
TEST_CASES = [
    {
        "name": "Perfect Match",
        "description": "Senior Python Developer applying to Python Backend role",
        "job": MockJob(
            title="Senior Python Backend Developer",
            description="Looking for experienced Python developer with Django, FastAPI, and PostgreSQL expertise. Must have experience with REST APIs and microservices.",
            requirements="5+ years Python, Django, PostgreSQL, Docker, CI/CD",
        ),
        "recruiter": MockRecruiter(
            current_position="Python Backend Developer",
            bio="Senior software engineer with 7 years of Python experience. Expert in Django, FastAPI, PostgreSQL. Built multiple microservices architectures. Strong in REST API design and Docker containerization.",
            years_of_experience=7,
        ),
        "expected_min": 75,
        "expected_max": 100,
    },
    {
        "name": "Strong Mismatch",
        "description": "Java Developer applying to HR Manager role",
        "job": MockJob(
            title="HR Manager",
            description="Lead HR operations, manage recruitment processes, employee relations, and talent development. Develop HR policies and ensure legal compliance.",
            requirements="5+ years HR experience, strategic planning, employee management",
        ),
        "recruiter": MockRecruiter(
            current_position="Java Developer",
            bio="Backend software developer specializing in Java Spring Boot applications. Experience with microservices, Kubernetes, and cloud deployment. Focus on enterprise software development.",
            years_of_experience=5,
        ),
        "expected_min": 50,
        "expected_max": 75,
    },
    {
        "name": "Subtle Match",
        "description": "React Developer applying to Vue Frontend role",
        "job": MockJob(
            title="Frontend Developer (Vue.js)",
            description="Build modern web applications using Vue.js and TypeScript. Component-based architecture, state management with Pinia, and responsive design.",
            requirements="3+ years Frontend, Vue.js, TypeScript, CSS",
        ),
        "recruiter": MockRecruiter(
            current_position="Frontend Developer",
            bio="Frontend engineer with 4 years React experience. Proficient in TypeScript, component architecture, Redux state management. Strong CSS and responsive design skills.",
            years_of_experience=4,
        ),
        "expected_min": 75,
        "expected_max": 95,
    },
]


def build_job_text(job: MockJob) -> str:
    """Build text representation of job."""
    parts = [
        f"Job Title: {job.title}",
        f"Description: {job.description}",
    ]
    if job.requirements:
        parts.append(f"Requirements: {job.requirements}")
    return "\n".join(parts)


def build_recruiter_text(recruiter: MockRecruiter) -> str:
    """Build text representation of recruiter."""
    parts = [
        f"Current Position: {recruiter.current_position}",
        f"Bio: {recruiter.bio}",
        f"Experience: {recruiter.years_of_experience} years",
    ]
    return "\n".join(parts)


def run_test_case(test_case: dict) -> dict:
    """Run a single test case and return results."""
    job_text = build_job_text(test_case["job"])
    recruiter_text = build_recruiter_text(test_case["recruiter"])
    
    job_embedding = get_embedding(job_text)
    recruiter_embedding = get_embedding(recruiter_text)
    
    if not job_embedding or not recruiter_embedding:
        return {
            "name": test_case["name"],
            "status": "ERROR",
            "error": "Failed to get embeddings",
            "score": None,
        }
    
    similarity = cosine_similarity(job_embedding, recruiter_embedding)
    score = max(0, min(100, similarity * 100))
    
    expected_min = test_case["expected_min"]
    expected_max = test_case["expected_max"]
    
    if expected_min <= score <= expected_max:
        status = "PASS"
    else:
        status = "FAIL"
    
    return {
        "name": test_case["name"],
        "description": test_case["description"],
        "status": status,
        "score": round(score, 2),
        "expected": f"{expected_min}-{expected_max}",
        "raw_similarity": round(similarity, 4),
    }


def main():
    """Main function to run all test cases."""
    print("=" * 60)
    print("Semantic Matching Accuracy Verification")
    print("=" * 60)
    
    # Check if Gemini is enabled
    if not is_semantic_enabled():
        print("\n⚠️  WARNING: Gemini API is not configured!")
        print("Please set GEMINI_API_KEY in environment variables.")
        print("Script will exit without running tests.\n")
        return
    
    print("\nRunning test cases...\n")
    
    results = []
    for tc in TEST_CASES:
        result = run_test_case(tc)
        results.append(result)
    
    # Print results table
    print("-" * 60)
    print(f"{'Test Case':<20} {'Score':<10} {'Expected':<15} {'Status':<10}")
    print("-" * 60)
    
    passed = 0
    failed = 0
    errors = 0
    
    for r in results:
        if r["status"] == "ERROR":
            print(f"{r['name']:<20} {'N/A':<10} {'N/A':<15} {'ERROR':<10}")
            errors += 1
        else:
            status_emoji = "✅" if r["status"] == "PASS" else "❌"
            print(f"{r['name']:<20} {r['score']:<10} {r['expected']:<15} {status_emoji} {r['status']}")
            if r["status"] == "PASS":
                passed += 1
            else:
                failed += 1
    
    print("-" * 60)
    print(f"\nSummary: {passed} passed, {failed} failed, {errors} errors")
    print(f"Total: {len(results)} test cases\n")
    
    # Detailed results
    print("\nDetailed Results:")
    for r in results:
        if r["status"] != "ERROR":
            print(f"\n  📋 {r['name']}")
            print(f"     Description: {r['description']}")
            print(f"     Score: {r['score']} (expected: {r['expected']})")
            print(f"     Raw Similarity: {r['raw_similarity']}")


if __name__ == "__main__":
    main()

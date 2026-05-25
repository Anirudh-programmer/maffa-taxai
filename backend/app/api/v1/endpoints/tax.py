"""
Tax calculator endpoints - Calculate, compare, and save tax calculations.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import os
import structlog

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User, SavedCalculation, TaxReport
from app.schemas.schemas import (
    TaxInput, TaxCalculationResult, TaxCalculationSave,
    TaxReportCreate, TaxReportResponse
)
from app.services.tax_calculator import tax_calculator
from app.services.pdf_service import pdf_processor

router = APIRouter(prefix="/tax", tags=["Tax Calculator"])
logger = structlog.get_logger()


@router.post("/calculate", response_model=TaxCalculationResult)
async def calculate_tax(
    tax_input: TaxInput,
    current_user: User = Depends(get_current_user),
):
    """
    Calculate income tax for both old and new regimes.
    Returns detailed comparison with recommendations.
    All calculations done in Python - never by the LLM.
    """
    try:
        result = tax_calculator.calculate(tax_input)
        return result
    except Exception as e:
        logger.error("Tax calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/calculate/public", response_model=TaxCalculationResult)
async def calculate_tax_public(tax_input: TaxInput):
    """
    Public tax calculation endpoint (no auth required for demo/landing page).
    """
    try:
        return tax_calculator.calculate(tax_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculations/save", status_code=201)
async def save_calculation(
    save_data: TaxCalculationSave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a tax calculation for future reference."""
    calc = SavedCalculation(
        user_id=current_user.id,
        title=save_data.title,
        financial_year=save_data.financial_year,
        input_data=save_data.input_data,
        old_regime_result=save_data.old_regime_result,
        new_regime_result=save_data.new_regime_result,
        recommended_regime=save_data.recommended_regime,
        tax_saved=save_data.tax_saved,
    )
    db.add(calc)
    await db.commit()
    await db.refresh(calc)
    return {"id": calc.id, "message": "Calculation saved successfully"}


@router.get("/calculations", response_model=List[dict])
async def list_calculations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    """List saved calculations for the current user."""
    result = await db.execute(
        select(SavedCalculation)
        .where(SavedCalculation.user_id == current_user.id)
        .order_by(desc(SavedCalculation.created_at))
        .limit(limit)
    )
    calcs = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "financial_year": c.financial_year,
            "recommended_regime": c.recommended_regime,
            "tax_saved": c.tax_saved,
            "created_at": c.created_at.isoformat(),
        }
        for c in calcs
    ]


@router.get("/calculations/{calc_id}")
async def get_calculation(
    calc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific saved calculation."""
    result = await db.execute(
        select(SavedCalculation).where(
            SavedCalculation.id == calc_id,
            SavedCalculation.user_id == current_user.id
        )
    )
    calc = result.scalar_one_or_none()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return {
        "id": calc.id,
        "title": calc.title,
        "financial_year": calc.financial_year,
        "input_data": calc.input_data,
        "old_regime_result": calc.old_regime_result,
        "new_regime_result": calc.new_regime_result,
        "recommended_regime": calc.recommended_regime,
        "tax_saved": calc.tax_saved,
        "created_at": calc.created_at.isoformat(),
    }


@router.post("/reports/generate", response_model=TaxReportResponse, status_code=201)
async def generate_tax_report(
    report_request: TaxReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a PDF tax analysis report."""
    # Get calculation data if provided
    calc_data = {}
    if report_request.calculation_id:
        result = await db.execute(
            select(SavedCalculation).where(
                SavedCalculation.id == report_request.calculation_id,
                SavedCalculation.user_id == current_user.id
            )
        )
        calc = result.scalar_one_or_none()
        if calc:
            calc_data = {
                "old_regime": calc.old_regime_result,
                "new_regime": calc.new_regime_result,
                "recommended_regime": calc.recommended_regime,
                "tax_saved": calc.tax_saved,
            }

    # Create report record
    report = TaxReport(
        user_id=current_user.id,
        title=report_request.title,
        financial_year=report_request.financial_year,
        report_data=calc_data,
        is_ready=False,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Generate PDF in background
    async def generate_pdf(report_id: str, data: dict, user_name: str):
        from app.core.database import AsyncSessionLocal
        output_dir = "./reports"
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/report_{report_id}.pdf"

        report_data = {
            **data,
            "financial_year": report_request.financial_year,
            "user_name": user_name or "User",
            "key_recommendations": [
                "Maximize Section 80C investments to ₹1.5L",
                "Consider NPS for additional ₹50,000 deduction",
                "Ensure health insurance for Section 80D benefit",
            ],
        }
        success = pdf_processor.generate_tax_report_pdf(report_data, output_path)

        async with AsyncSessionLocal() as db2:
            result = await db2.execute(select(TaxReport).where(TaxReport.id == report_id))
            r = result.scalar_one_or_none()
            if r:
                r.is_ready = success
                r.file_path = output_path if success else None
                await db2.commit()

    background_tasks.add_task(
        generate_pdf, report.id, calc_data, current_user.full_name or "User"
    )

    return TaxReportResponse.model_validate(report)


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated PDF report."""
    result = await db.execute(
        select(TaxReport).where(
            TaxReport.id == report_id,
            TaxReport.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.is_ready or not report.file_path:
        raise HTTPException(status_code=202, detail="Report is still being generated")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"taxai_report_{report.financial_year}.pdf",
    )


@router.get("/sections")
async def get_tax_sections():
    """Return information about major tax sections for quick reference."""
    return {
        "sections": [
            {"code": "80C", "name": "EPF, PPF, ELSS, LIC", "limit": 150000, "regime": "old"},
            {"code": "80CCD(1B)", "name": "NPS Additional", "limit": 50000, "regime": "both"},
            {"code": "80D", "name": "Health Insurance", "limit": 100000, "regime": "old"},
            {"code": "80E", "name": "Education Loan Interest", "limit": None, "regime": "old"},
            {"code": "80G", "name": "Donations", "limit": None, "regime": "old"},
            {"code": "80TTA", "name": "Savings Interest", "limit": 10000, "regime": "old"},
            {"code": "24(b)", "name": "Home Loan Interest", "limit": 200000, "regime": "old"},
            {"code": "10(13A)", "name": "HRA Exemption", "limit": None, "regime": "old"},
            {"code": "Standard", "name": "Standard Deduction", "limit": 75000, "regime": "new"},
        ]
    }

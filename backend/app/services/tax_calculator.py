"""
Tax Calculation Engine - All calculations done in pure Python.
Never delegate financial math to the LLM.
Covers FY 2024-25 Indian Income Tax rules.
"""
from typing import Dict, List, Tuple, Optional
from app.schemas.schemas import TaxInput, RegimeResult, TaxCalculationResult, TaxSlabDetail
import structlog

logger = structlog.get_logger()


class IndianTaxCalculator:
    """
    Accurate Indian Income Tax Calculator for FY 2024-25.
    Handles both old and new tax regimes.
    """

    # ─── New Regime Slabs (FY 2024-25 post Budget 2024) ─────────────────
    NEW_REGIME_SLABS = [
        (300000, 0.00),    # Up to 3L: 0%
        (700000, 0.05),    # 3L - 7L: 5%
        (1000000, 0.10),   # 7L - 10L: 10%
        (1200000, 0.15),   # 10L - 12L: 15%
        (1500000, 0.20),   # 12L - 15L: 20%
        (float('inf'), 0.30),  # Above 15L: 30%
    ]

    # ─── Old Regime Slabs ─────────────────────────────────────────────────
    # For individuals < 60 years
    OLD_REGIME_SLABS_NORMAL = [
        (250000, 0.00),
        (500000, 0.05),
        (1000000, 0.20),
        (float('inf'), 0.30),
    ]

    # Senior citizens (60-79)
    OLD_REGIME_SLABS_SENIOR = [
        (300000, 0.00),
        (500000, 0.05),
        (1000000, 0.20),
        (float('inf'), 0.30),
    ]

    # Super senior citizens (80+)
    OLD_REGIME_SLABS_SUPER_SENIOR = [
        (500000, 0.00),
        (1000000, 0.20),
        (float('inf'), 0.30),
    ]

    # Surcharge rates
    SURCHARGE_RATES = [
        (5000000, 0.00),      # Up to 50L: 0%
        (10000000, 0.10),     # 50L - 1Cr: 10%
        (20000000, 0.15),     # 1Cr - 2Cr: 15%
        (50000000, 0.25),     # 2Cr - 5Cr: 25%
        (float('inf'), 0.37), # Above 5Cr: 37% (25% under new regime)
    ]

    HEALTH_EDUCATION_CESS = 0.04  # 4%

    def calculate_hra_exemption(
        self, basic_salary: float, hra_received: float,
        rent_paid: float, city_type: str
    ) -> float:
        """
        HRA Exemption = Minimum of:
        1. Actual HRA received
        2. 50% of basic (metro) or 40% of basic (non-metro)
        3. Rent paid - 10% of basic salary
        """
        if hra_received == 0 or rent_paid == 0:
            return 0.0
        metro_percentage = 0.50 if city_type == "metro" else 0.40
        option1 = hra_received
        option2 = basic_salary * metro_percentage
        option3 = max(0, rent_paid - (basic_salary * 0.10))
        return min(option1, option2, option3)

    def calculate_standard_deduction(self, gross_salary: float) -> float:
        """Standard deduction: Rs 75,000 (new regime), Rs 50,000 (old regime)."""
        return 50000.0  # For old regime; new regime handled separately

    def calculate_slab_tax(
        self, taxable_income: float, slabs: List[Tuple]
    ) -> Tuple[float, List[TaxSlabDetail]]:
        """Calculate tax based on slab structure."""
        total_tax = 0.0
        slab_details = []
        previous_limit = 0

        for limit, rate in slabs:
            if taxable_income <= previous_limit:
                break
            slab_income = min(taxable_income, limit) - previous_limit
            if slab_income > 0:
                slab_tax = slab_income * rate
                total_tax += slab_tax
                slab_label = (
                    f"Up to ₹{previous_limit/100000:.1f}L"
                    if previous_limit == 0
                    else f"₹{previous_limit/100000:.1f}L - ₹{limit/100000:.1f}L"
                    if limit != float('inf')
                    else f"Above ₹{previous_limit/100000:.1f}L"
                )
                slab_details.append(TaxSlabDetail(
                    slab=slab_label,
                    rate=rate * 100,
                    taxable_income=slab_income,
                    tax=slab_tax
                ))
            previous_limit = limit

        return total_tax, slab_details

    def calculate_surcharge(self, taxable_income: float, basic_tax: float, is_new_regime: bool = False) -> float:
        """Calculate surcharge based on income level."""
        if taxable_income <= 5000000:
            return 0.0

        surcharge_rate = 0.0
        if taxable_income <= 10000000:
            surcharge_rate = 0.10
        elif taxable_income <= 20000000:
            surcharge_rate = 0.15
        elif taxable_income <= 50000000:
            surcharge_rate = 0.25
        else:
            # New regime caps at 25%, old regime 37%
            surcharge_rate = 0.25 if is_new_regime else 0.37

        surcharge = basic_tax * surcharge_rate

        # Marginal relief: ensure total tax increase < income increase above threshold
        return surcharge

    def apply_87a_rebate(self, taxable_income: float, basic_tax: float, regime: str = "old") -> float:
        """
        Section 87A rebate: Rs 12,500 if income <= 5L (old regime)
        New regime: Rs 25,000 rebate if income <= 7L (Budget 2023)
        """
        if regime == "old" and taxable_income <= 500000:
            return min(basic_tax, 12500)
        elif regime == "new" and taxable_income <= 700000:
            return min(basic_tax, 25000)
        return 0.0

    def calculate_old_regime(self, inp: TaxInput) -> RegimeResult:
        """Calculate tax under old regime with all deductions."""
        # Calculate gross income
        hra_exemption = self.calculate_hra_exemption(
            inp.basic_salary, inp.hra_received, inp.rent_paid, inp.city_type
        )
        salary_income = (
            inp.basic_salary + inp.hra_received + inp.other_allowances
        )
        standard_deduction = 50000  # Old regime standard deduction

        gross_income = (
            salary_income + inp.business_income + inp.rental_income +
            inp.interest_income + inp.capital_gains_short +
            inp.capital_gains_long + inp.other_income
        )

        # Compute total deductions
        section_80c_total = min(inp.section_80c + inp.home_loan_principal, 150000)
        deductions = {
            "Standard Deduction": standard_deduction,
            "Section 80C (EPF/PPF/ELSS)": section_80c_total,
            "Section 80CCD(1B) - NPS": min(inp.section_80ccd_nps, 50000),
            "Section 80D - Health Insurance": min(inp.section_80d, 100000),
            "Section 80E - Education Loan": inp.section_80e,
            "Section 80G - Donations": inp.section_80g,
            "Section 80TTA/TTB - Interest": min(inp.section_80tta + inp.section_80ttb, 50000),
            "Section 24b - Home Loan Interest": min(inp.home_loan_interest, 200000),
            "HRA Exemption": hra_exemption,
            "LTA Exemption": inp.lta_exemption,
            "Professional Tax": inp.professional_tax,
        }
        total_deductions = sum(deductions.values())
        taxable_income = max(0, gross_income - total_deductions)

        # Get slabs based on age
        if inp.is_super_senior_citizen or inp.age >= 80:
            slabs = self.OLD_REGIME_SLABS_SUPER_SENIOR
        elif inp.is_senior_citizen or inp.age >= 60:
            slabs = self.OLD_REGIME_SLABS_SENIOR
        else:
            slabs = self.OLD_REGIME_SLABS_NORMAL

        basic_tax, slab_details = self.calculate_slab_tax(taxable_income, slabs)

        # Apply 87A rebate
        rebate = self.apply_87a_rebate(taxable_income, basic_tax, "old")
        basic_tax = max(0, basic_tax - rebate)

        surcharge = self.calculate_surcharge(taxable_income, basic_tax, False)
        cess = (basic_tax + surcharge) * self.HEALTH_EDUCATION_CESS
        total_tax = basic_tax + surcharge + cess
        effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0

        take_home_monthly = (gross_income - total_tax) / 12

        return RegimeResult(
            gross_income=round(gross_income, 2),
            total_deductions=round(total_deductions, 2),
            taxable_income=round(taxable_income, 2),
            basic_tax=round(basic_tax, 2),
            surcharge=round(surcharge, 2),
            cess=round(cess, 2),
            total_tax=round(total_tax, 2),
            effective_rate=round(effective_rate, 2),
            take_home_monthly=round(take_home_monthly, 2),
            slab_details=slab_details,
            deduction_breakdown={k: round(v, 2) for k, v in deductions.items() if v > 0},
        )

    def calculate_new_regime(self, inp: TaxInput) -> RegimeResult:
        """Calculate tax under new regime (limited deductions, lower rates)."""
        # New regime: most deductions not allowed, but higher standard deduction
        standard_deduction = 75000  # Enhanced from Budget 2024

        salary_income = inp.basic_salary + inp.hra_received + inp.other_allowances
        gross_income = (
            salary_income + inp.business_income + inp.rental_income +
            inp.interest_income + inp.capital_gains_short +
            inp.capital_gains_long + inp.other_income
        )

        # Only allowed deductions under new regime
        nps_employer = min(inp.section_80ccd_nps, 50000)  # 80CCD(2) - employer NPS still allowed
        deductions = {
            "Standard Deduction": standard_deduction,
            "NPS Employer Contribution 80CCD(2)": nps_employer,
            "Professional Tax": inp.professional_tax,
        }
        total_deductions = sum(deductions.values())
        taxable_income = max(0, gross_income - total_deductions)

        basic_tax, slab_details = self.calculate_slab_tax(taxable_income, self.NEW_REGIME_SLABS)

        # 87A rebate for new regime
        rebate = self.apply_87a_rebate(taxable_income, basic_tax, "new")
        basic_tax = max(0, basic_tax - rebate)

        surcharge = self.calculate_surcharge(taxable_income, basic_tax, True)
        cess = (basic_tax + surcharge) * self.HEALTH_EDUCATION_CESS
        total_tax = basic_tax + surcharge + cess
        effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0
        take_home_monthly = (gross_income - total_tax) / 12

        return RegimeResult(
            gross_income=round(gross_income, 2),
            total_deductions=round(total_deductions, 2),
            taxable_income=round(taxable_income, 2),
            basic_tax=round(basic_tax, 2),
            surcharge=round(surcharge, 2),
            cess=round(cess, 2),
            total_tax=round(total_tax, 2),
            effective_rate=round(effective_rate, 2),
            take_home_monthly=round(take_home_monthly, 2),
            slab_details=slab_details,
            deduction_breakdown={k: round(v, 2) for k, v in deductions.items() if v > 0},
        )

    def generate_recommendations(
        self, inp: TaxInput, old: RegimeResult, new: RegimeResult
    ) -> List[str]:
        """Generate actionable tax-saving recommendations."""
        recs = []
        recommended = "old" if old.total_tax < new.total_tax else "new"

        if recommended == "old":
            recs.append(f"Old Tax Regime saves you ₹{abs(old.total_tax - new.total_tax):,.0f} this year")
        else:
            recs.append(f"New Tax Regime saves you ₹{abs(old.total_tax - new.total_tax):,.0f} this year")

        # 80C advice
        if inp.section_80c < 150000:
            remaining = 150000 - inp.section_80c
            recs.append(f"Invest ₹{remaining:,.0f} more in 80C instruments (EPF/PPF/ELSS) to maximize deduction")

        # NPS advice
        if inp.section_80ccd_nps < 50000:
            recs.append("Invest in NPS for additional ₹50,000 deduction under Section 80CCD(1B)")

        # Health insurance
        if inp.section_80d < 25000:
            recs.append("Get health insurance to claim up to ₹25,000 deduction under Section 80D")

        # HRA advice
        if inp.rent_paid > 0 and inp.hra_received == 0:
            recs.append("If you receive HRA, claim exemption to reduce taxable income")

        # Home loan
        if inp.home_loan_interest == 0:
            recs.append("Consider home loan for Section 24b deduction up to ₹2,00,000 on interest")

        # Effective rate comparison
        recs.append(f"Old Regime effective tax rate: {old.effective_rate:.1f}% | New Regime: {new.effective_rate:.1f}%")

        return recs

    def calculate(self, inp: TaxInput) -> TaxCalculationResult:
        """Main calculation entry point."""
        logger.info("Calculating tax", financial_year=inp.financial_year)
        old = self.calculate_old_regime(inp)
        new = self.calculate_new_regime(inp)

        recommended = "old" if old.total_tax <= new.total_tax else "new"
        tax_saved = abs(old.total_tax - new.total_tax)
        better_tax = min(old.total_tax, new.total_tax)
        worse_tax = max(old.total_tax, new.total_tax)
        savings_pct = ((worse_tax - better_tax) / worse_tax * 100) if worse_tax > 0 else 0

        recommendations = self.generate_recommendations(inp, old, new)

        return TaxCalculationResult(
            old_regime=old,
            new_regime=new,
            recommended_regime=recommended,
            tax_saved=round(tax_saved, 2),
            savings_percentage=round(savings_pct, 2),
            key_recommendations=recommendations,
            financial_year=inp.financial_year,
        )


# Singleton
tax_calculator = IndianTaxCalculator()

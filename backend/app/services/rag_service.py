"""
RAG Service - Retrieval Augmented Generation for tax knowledge.
Uses ChromaDB for vector storage and Google embeddings.
"""
import os
import asyncio
import hashlib
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class RAGService:
    """
    ChromaDB-based RAG service for tax knowledge retrieval.
    Supports document ingestion, embedding, and semantic retrieval.
    """

    def __init__(self):
        self.client = None
        self.collection = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of ChromaDB client."""
        if self._initialized:
            return

        # Configure Google Generative AI with the API key
        genai.configure(api_key=settings.GEMINI_API_KEY)

        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._initialized = True
        logger.info("ChromaDB initialized", collection=settings.CHROMA_COLLECTION_NAME)

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding using Gemini embedding model."""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            # Return zero vector as fallback — chat still works without RAG
            return [0.0] * 3072

    async def embed_query(self, text: str) -> List[float]:
        """Generate query embedding."""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as e:
            logger.error("Query embedding failed", error=str(e))
            return [0.0] * 3072

    async def ingest_document(
        self,
        text: str,
        document_id: str,
        document_type: str,
        user_id: str,
        metadata: Optional[Dict] = None,
    ) -> List[str]:
        """
        Ingest a document into ChromaDB.
        Chunks text, generates embeddings, stores with metadata.
        """
        self._initialize()
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return []

        chunk_ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "document_id": document_id,
                "document_type": document_type,
                "user_id": user_id,
                "chunk_index": i,
                "chunk_hash": chunk_hash,
                **(metadata or {}),
            })

        # Generate embeddings in batches
        for chunk in chunks:
            emb = await self.embed_text(chunk)
            embeddings.append(emb)

        # Store in ChromaDB
        self.collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Document ingested", document_id=document_id, chunks=len(chunks))
        return chunk_ids

    async def ingest_tax_knowledge(self):
        """
        Pre-populate tax knowledge base with Indian tax information.
        Called on application startup.
        """
        self._initialize()

        # Check if already seeded
        count = self.collection.count()
        if count > 50:
            logger.info("Tax knowledge already seeded", documents=count)
            return

        tax_documents = self._get_tax_knowledge_base()
        for doc in tax_documents:
            await self.ingest_document(
                text=doc["content"],
                document_id=f"knowledge_{doc['id']}",
                document_type="tax_knowledge",
                user_id="system",
                metadata={"source": doc["source"], "category": doc["category"]},
            )
        logger.info("Tax knowledge base seeded", count=len(tax_documents))

    async def retrieve_context(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        n_results: int = 3,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Retrieve relevant context for a query.
        Can filter by specific document IDs or user.
        """
        self._initialize()
        query_embedding = await self.embed_query(query)

        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}
        elif user_id:
            where_filter = {
                "$or": [
                    {"user_id": {"$eq": user_id}},
                    {"user_id": {"$eq": "system"}},
                ]
            }

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, max(1, self.collection.count())),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            if not results["documents"] or not results["documents"][0]:
                return ""

            context_parts = []
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                relevance = 1 - dist  # cosine distance to similarity
                if relevance > 0.3:  # Only include relevant chunks
                    source = meta.get("source", meta.get("document_type", "Tax Knowledge"))
                    context_parts.append(f"[Source: {source}]\n{doc}")

            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error("ChromaDB query failed", error=str(e))
            return ""

    async def delete_document(self, document_id: str):
        """Remove a document's chunks from ChromaDB."""
        self._initialize()
        try:
            results = self.collection.get(where={"document_id": {"$eq": document_id}})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info("Document deleted from ChromaDB", document_id=document_id)
        except Exception as e:
            logger.error("ChromaDB deletion failed", error=str(e))

    def _get_tax_knowledge_base(self) -> List[Dict]:
        """Returns curated Indian tax knowledge for RAG seeding."""
        return [
            {
                "id": "old_regime_2024",
                "source": "Income Tax Department - FY 2024-25",
                "category": "tax_slabs",
                "content": """Old Tax Regime Slabs for FY 2024-25:
For individuals below 60 years:
- Income up to ₹2,50,000: NIL
- Income from ₹2,50,001 to ₹5,00,000: 5%
- Income from ₹5,00,001 to ₹10,00,000: 20%
- Income above ₹10,00,000: 30%

For Senior Citizens (60-79 years):
- Income up to ₹3,00,000: NIL
- Income from ₹3,00,001 to ₹5,00,000: 5%
- Income from ₹5,00,001 to ₹10,00,000: 20%
- Income above ₹10,00,000: 30%

For Super Senior Citizens (80+ years):
- Income up to ₹5,00,000: NIL
- Income from ₹5,00,001 to ₹10,00,000: 20%
- Income above ₹10,00,000: 30%

Health and Education Cess: 4% on total tax
Surcharge: 10% on tax if income exceeds ₹50 lakhs, 15% above ₹1 crore, 25% above ₹2 crore, 37% above ₹5 crore.
Section 87A rebate: If total income is up to ₹5,00,000, rebate of ₹12,500 on tax.""",
            },
            {
                "id": "new_regime_2024",
                "source": "Budget 2024 - New Tax Regime",
                "category": "tax_slabs",
                "content": """New Tax Regime Slabs for FY 2024-25 (Budget 2024 Updated):
- Income up to ₹3,00,000: NIL
- Income from ₹3,00,001 to ₹7,00,000: 5%
- Income from ₹7,00,001 to ₹10,00,000: 10%
- Income from ₹10,00,001 to ₹12,00,000: 15%
- Income from ₹12,00,001 to ₹15,00,000: 20%
- Income above ₹15,00,000: 30%

Key Features of New Regime:
- Standard deduction: ₹75,000 (increased from ₹50,000 in Budget 2024)
- Section 87A rebate: If income is up to ₹7,00,000, full tax rebate (₹25,000)
- Employer NPS contribution deduction (Section 80CCD(2)): Still allowed
- Most other deductions (80C, 80D, HRA, LTA) are NOT available
- Health and Education Cess: 4%
- Surcharge capped at 25% under new regime

The new regime is now the DEFAULT regime from FY 2023-24 onwards.""",
            },
            {
                "id": "section_80c",
                "source": "Income Tax Act - Section 80C",
                "category": "deductions",
                "content": """Section 80C - Most Popular Tax Deduction:
Maximum limit: ₹1,50,000 per financial year (only under Old Regime)

Eligible investments and expenses:
1. Employee Provident Fund (EPF) - employee contribution
2. Public Provident Fund (PPF) - up to ₹1.5L per year
3. ELSS (Equity Linked Savings Scheme) - 3-year lock-in, market-linked returns
4. Life Insurance Premium (LIC/other insurers)
5. National Savings Certificate (NSC)
6. 5-year Fixed Deposit (Bank/Post Office)
7. Senior Citizens Savings Scheme (SCSS)
8. Sukanya Samriddhi Yojana (for girl child)
9. Home loan principal repayment
10. Tuition fees for children (max 2 children)
11. Stamp duty and registration charges for home purchase

Strategy: Maximize 80C investments first before other deductions.""",
            },
            {
                "id": "section_80d",
                "source": "Income Tax Act - Section 80D",
                "category": "deductions",
                "content": """Section 80D - Health Insurance Premium Deduction:
Only under Old Tax Regime.

Limits:
- Self, spouse, children: Up to ₹25,000 (₹50,000 if self/spouse is senior citizen)
- Parents (non-senior): Additional ₹25,000
- Parents (senior citizens 60+): Additional ₹50,000
- Maximum total: ₹1,00,000 per year

Also includes: Preventive health check-up costs up to ₹5,000 (within the above limit)

Who should claim: Anyone paying health insurance premiums for self or family.""",
            },
            {
                "id": "hra_exemption",
                "source": "Income Tax Act - Section 10(13A)",
                "category": "exemptions",
                "content": """HRA (House Rent Allowance) Exemption:
Only available under Old Tax Regime.

HRA Exemption = Minimum of:
1. Actual HRA received from employer
2. 50% of basic salary (Metro cities: Delhi, Mumbai, Kolkata, Chennai) OR 40% (Non-metro)
3. Rent paid - 10% of basic salary

Metro cities for HRA: Delhi, Mumbai, Kolkata, Chennai

Required documents: Rent receipts, rental agreement, landlord PAN (if rent > ₹1 lakh/year)

Note: If paying rent but not receiving HRA, you can claim deduction under Section 80GG (up to ₹5,000/month or 25% of total income).""",
            },
            {
                "id": "nps_sections",
                "source": "Income Tax Act - NPS Deductions",
                "category": "deductions",
                "content": """National Pension System (NPS) Tax Benefits:

Section 80CCD(1): Employee/Self contribution
- Within ₹1.5L limit of Section 80C
- Up to 10% of basic salary + DA

Section 80CCD(1B): Additional deduction
- EXTRA ₹50,000 over and above 80C limit
- Available in BOTH old and new regimes
- Total additional benefit: ₹50,000 × your tax rate

Section 80CCD(2): Employer NPS contribution
- Available in BOTH old AND new regimes
- Up to 10% of basic salary (private sector) or 14% (government employees)
- NO upper monetary limit
- One of the best tax-saving tools for salaried employees

NPS Investment strategy: Use 80CCD(1B) to save ₹50,000 extra deduction.""",
            },
            {
                "id": "home_loan_deductions",
                "source": "Income Tax Act - Home Loan Benefits",
                "category": "deductions",
                "content": """Home Loan Tax Benefits (Old Regime):

Section 24(b) - Interest on home loan:
- Self-occupied property: Up to ₹2,00,000 per year
- Let-out property: No limit (can set off against rental income)
- Under construction: No deduction until construction completes (5 years limit)

Section 80C - Principal repayment:
- Up to ₹1,50,000 (within overall 80C limit)
- Only after construction is complete

Section 80EE - First-time buyers:
- Additional ₹50,000 for loan sanctioned in FY 2016-17
- Loan amount ≤ ₹35 lakhs, property value ≤ ₹50 lakhs

Section 80EEA - Affordable housing:
- Additional ₹1,50,000 for loans sanctioned between 2019-2022
- Stamp duty ≤ ₹45 lakhs

Joint home loan: Both co-borrowers can claim deductions separately (2x benefit).""",
            },
            {
                "id": "capital_gains",
                "source": "Income Tax Act - Capital Gains",
                "category": "capital_gains",
                "content": """Capital Gains Tax Rules (FY 2024-25):

Short-Term Capital Gains (STCG):
- Equity/Mutual Funds (held < 1 year): 20% (Budget 2024: increased from 15%)
- Other assets (< 2 years for property): Added to income, taxed at slab rate

Long-Term Capital Gains (LTCG):
- Equity/Mutual Funds (held > 1 year): 12.5% above ₹1.25 lakh exemption (Budget 2024: increased from 10%, exemption raised from ₹1L)
- Property/Gold (held > 2 years): 12.5% WITHOUT indexation (Budget 2024 change)
- Debt funds (held > 3 years): Now taxed as per slab rate (Finance Act 2023)

Key Budget 2024 Changes:
- STCG on equity increased to 20%
- LTCG on equity increased to 12.5% but exemption raised to ₹1.25L
- Indexation benefit removed for property (with some grandfather clauses)

Section 54: LTCG on property can be reinvested in another property to save tax.
Section 54EC: Invest LTCG in NHAI/REC bonds (up to ₹50L) within 6 months.""",
            },
            {
                "id": "form16_guide",
                "source": "Income Tax Department - Form 16",
                "category": "documents",
                "content": """Form 16 - Your TDS Certificate Explained:

Form 16 is issued by your employer by June 15 every year.
It has TWO PARTS:

Part A - TDS Details:
- Employer name and TAN
- Employee name and PAN
- Quarterly TDS deducted and deposited
- Assessment year

Part B - Salary Breakdown:
- Gross salary
- Exemptions (HRA, LTA, etc.)
- Net taxable salary
- All deductions claimed (80C, 80D, etc.)
- Total taxable income
- Total tax payable
- TDS already deducted

How to use Form 16 for ITR filing:
1. Check if TDS matches 26AS (tax credit statement)
2. Verify all exemptions and deductions
3. Use figures to fill ITR-1 or ITR-2
4. If multiple employers in a year, collect Form 16 from each

Common issues: Incorrect PAN, mismatch in TDS amount, missing allowances.""",
            },
            {
                "id": "itr_guide",
                "source": "Income Tax Department - ITR Filing",
                "category": "filing",
                "content": """ITR Filing Guide for Salaried Employees:

Who must file ITR:
- Income exceeds basic exemption limit (₹2.5L or ₹3L for new regime)
- Has foreign assets or foreign income
- Deposited ₹1 crore+ in bank accounts
- Foreign travel expense > ₹2 lakhs
- Has paid electricity > ₹1 lakh
- Wants to claim refund

ITR Forms:
- ITR-1 (Sahaj): Salary income + 1 house property + other income (< ₹50L total)
- ITR-2: Multiple properties, capital gains, foreign income
- ITR-3: Business/profession income
- ITR-4 (Sugam): Presumptive business income

Deadline: July 31 (without penalty), December 31 (with late fee of ₹5,000)

Documents needed: Form 16, bank statements, investment proofs, rent receipts, 26AS, AIS

Online filing: incometax.gov.in (free for all)
Assisted filing: CA or tax filing platforms (Cleartax, myITReturn)""",
            },
        ]


# Singleton
rag_service = RAGService()

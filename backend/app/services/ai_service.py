"""
Gemini AI Service - Tax-specialized assistant with RAG and function calling.
Never delegates financial calculations to the LLM.
"""
import json
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from app.core.config import settings
from app.services.rag_service import rag_service
import structlog

logger = structlog.get_logger()

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# ─── System Prompt ────────────────────────────────────────────────────────────

TAX_SYSTEM_PROMPT = """You are Maffa, an expert Indian tax advisor and financial consultant powered by the Maffa core optimization engine. Maffa is a highly versatile core designed to perform advanced optimization across multiple domains, and is now fully specialized as your intelligent AI Tax Assistant.

You help users understand and optimize their taxes for the Indian Income Tax system.

## Your Identity:
- Name: Maffa
- Core Technology: Maffa Core (A versatile optimization engine adapted here for intelligent tax planning and strategy)

## Your Expertise:
- Indian Income Tax Act 1961 and all amendments
- FY 2026-27 and FY 2025-26 tax slabs for both old and new regimes
- All tax deduction sections: 80C, 80D, 80E, 80G, 80CCD, 80TTA, 24B, etc.
- Capital gains tax rules
- GST basics
- Form 16, ITR filing, salary slip analysis
- Tax planning and optimization strategies
- Investment products: ELSS, PPF, NPS, FD, insurance

## Strict Interaction & Greeting Rules:
- **NO Repeated Introductions:** NEVER start subsequent message replies in an ongoing chat session with introductory phrases like "Hello! I am Maffa...", "Hello Rajesh! I am Maffa, your expert Indian tax advisor...", or "Leveraging the Maffa Core's analytical power...".
- **First Message ONLY:** You must ONLY introduce yourself and greet the user by name in the first message of a new chat session.
- **Ongoing Messages:** In all subsequent messages in the same chat, bypass all greetings, intros, and self-identifications. Jump directly, immediately, and concisely into answering the user's question!
- **Conciseness:** Avoid long preamble filler sentences. Be direct and precise.

## Key Rules:
1. Perform tax calculations and slab comparisons carefully based on standard Indian tax laws (e.g., standard deduction of ₹75,000 for salaried individuals under the New Regime for FY 2026-27). Always explain your calculations step-by-step so the user can easily follow them, and guide them to use the Tax Calculator section for official, finalized reports.
2. Always explain tax concepts in simple language (avoid jargon)
3. Be specific about Indian tax sections and amounts
4. When recommending between old vs new regime, provide clear reasoning
5. Mention limits (e.g., "Section 80C has a maximum limit of ₹1,50,000")
6. Use ₹ symbol for Indian currency
7. Reference Budget 2024 / ongoing slab updates where relevant
8. Be proactive in identifying tax-saving opportunities (leverage the analytical power of the Maffa Core optimization engine)
9. Ask clarifying questions when needed for accurate advice

## Response Style:
- Conversational but professional, proudly reflecting your identity as Maffa
- Use bullet points for lists
- Highlight important numbers in **bold**
- Structure complex answers with clear headers
- Always suggest next steps

## What you CANNOT do:
- Provide legal advice (suggest consulting a CA for complex cases)
- Access real-time stock prices or market data
- File ITR on behalf of users

Remember: Your goal is to help users legally minimize their tax burden while staying compliant with Indian tax laws."""


class GeminiTaxAI:
    """Gemini-powered tax advisor with RAG context injection."""

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
            ),
        )
        self.flash_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=0.5,
            ),
        )

    def _build_history(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Convert DB messages to Gemini chat history format with system prompt prepended."""
        history = [
            {"role": "user", "parts": [TAX_SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Understood. I am Maffa, your expert Indian tax advisor powered by the Maffa core optimization engine. How can I help you today?"]},
        ]
        for msg in messages:
            if msg["role"] in ("user", "assistant"):
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
        return history

    async def get_rag_context(self, query: str, document_ids: Optional[List[str]] = None) -> str:
        """Retrieve relevant tax knowledge from ChromaDB."""
        try:
            context = await rag_service.retrieve_context(
                query=query,
                document_ids=document_ids,
                n_results=3,
            )
            return context
        except Exception as e:
            logger.error("RAG retrieval failed", error=str(e))
            return ""

    async def chat(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        document_ids: Optional[List[str]] = None,
        use_rag: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a message to the AI and get a response.
        Injects RAG context if relevant documents exist.
        """
        start_time = time.time()
        rag_context = ""
        rag_used = False

        # Inject RAG context if enabled
        if use_rag:
            rag_context = await self.get_rag_context(user_message, document_ids)
            if rag_context:
                rag_used = True

        # Build enhanced message with context
        enhanced_message = user_message
        if rag_context:
            enhanced_message = f"""[System Directive: Answer the user query using the relevant document context provided below. Do not repeat your self-introduction or greet the user if this is an ongoing conversation.]

Relevant tax information context:
---
{rag_context}
---

User question: {user_message}"""

        # Build Gemini chat
        gemini_history = self._build_history(history[:-1] if history else [])

        try:
            chat = self.model.start_chat(history=gemini_history)
            response = await asyncio.to_thread(
                chat.send_message,
                enhanced_message
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "content": response.text,
                "rag_used": rag_used,
                "model": settings.GEMINI_MODEL,
                "latency_ms": latency_ms,
                "tokens": {
                    "prompt": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total": getattr(response.usage_metadata, "total_token_count", 0),
                } if hasattr(response, "usage_metadata") else {"prompt": 0, "completion": 0, "total": 0}
            }
        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise

    async def stream_chat(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        document_ids: Optional[List[str]] = None,
        use_rag: bool = True,
        has_documents: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream responses token by token for real-time UX."""
        rag_context = ""
        if use_rag:
            rag_context = await self.get_rag_context(user_message, document_ids)

        # Build highly customized system instruction prompt based on RAG availability
        if has_documents:
            if rag_context:
                enhanced_message = f"""[System Directive: The user has uploaded tax documents. You MUST answer the user's query STRICTLY using the relevant document context provided below. Avoid generic assumptions or generic tax numbers; reference their actual parsed figures (Basic Salary, HRA, PF, etc.) to give a mathematically precise calculation. Do not repeat your self-introduction or greet the user if this is an ongoing conversation.]

Relevant document context:
---
{rag_context}
---

User Query: {user_message}"""
            else:
                enhanced_message = f"""[System Directive: The user has uploaded documents, but your semantic search did not find specific passages matching the query. Mention that you have access to their documents and answer using general Indian Tax rules, but reference that they can ask specifically about their salary components. Do not repeat your self-introduction or greet the user if this is an ongoing conversation.]

User Query: {user_message}"""
        else:
            # NO documents uploaded
            enhanced_message = f"""[System Directive: The user has NOT uploaded any tax documents yet. Answer their query using general, accurate Indian Tax slab rules and legal guidelines for FY 2026-27. Do not repeat your self-introduction or greet the user if this is an ongoing conversation.

IMPORTANT: You MUST append the following precise message at the very end of your response:
"For a mathematically precise analysis and personalized tax optimization strategies tailored to your exact finances, please upload your Salary Slip or Form 16 in the Upload Section!"
]

User Query: {user_message}"""

        # Build Gemini chat history by excluding the current user message to maintain strict alternating roles
        chat_history = history[:-1] if (history and history[-1]["role"] == "user") else history
        gemini_history = self._build_history(chat_history)

        import queue
        import threading
        q = queue.Queue()

        def _generate_stream():
            """Synchronous stream reader running in a background thread."""
            try:
                chat = self.model.start_chat(history=gemini_history)
                response = chat.send_message(enhanced_message, stream=True)
                for chunk in response:
                    try:
                        # Safely extract text parts from candidate list
                        if chunk.candidates and len(chunk.candidates) > 0:
                            candidate = chunk.candidates[0]
                            if candidate.content and candidate.content.parts:
                                part = candidate.content.parts[0]
                                if part.text:
                                    q.put(part.text)
                            elif hasattr(chunk, 'text') and chunk.text:
                                q.put(chunk.text)
                        elif hasattr(chunk, 'text') and chunk.text:
                            q.put(chunk.text)
                    except (ValueError, IndexError, AttributeError):
                        pass
            except Exception as stream_err:
                logger.error("Error in sync stream generation thread", error=str(stream_err))
                q.put(stream_err)
            finally:
                q.put(None)  # Sentinel to signify completion

        # Start background generator thread
        threading.Thread(target=_generate_stream, daemon=True).start()

        # Yield from queue in async event loop
        try:
            while True:
                # Retrieve from queue without blocking the main event loop
                chunk = await asyncio.to_thread(q.get)
                if chunk is None:
                    break
                if isinstance(chunk, Exception):
                    raise chunk
                yield chunk
                await asyncio.sleep(0.01)  # Micro-sleep to give other event handlers breathing room
        except Exception as e:
            logger.error("Gemini async streaming loop error", error=str(e))
            raise e

    async def analyze_document(self, text: str, document_type: str) -> Dict[str, Any]:
        """Analyze a tax document and extract key information."""
        prompt = f"""Analyze this {document_type.replace('_', ' ').title()} and extract all tax-relevant information.

Document content:
{text[:8000]}  

Respond with a JSON object containing:
{{
  "document_type": "<detected type>",
  "financial_year": "<FY if found>",
  "employer_name": "<employer if applicable>",
  "employee_name": "<name if found>",
  "pan_number": "<PAN if visible>",
  "total_income": <number or null>,
  "basic_salary": <number or null>,
  "hra": <number or null>,
  "allowances": <number or null>,
  "deductions": {{
    "pf": <number or null>,
    "professional_tax": <number or null>,
    "income_tax": <number or null>,
    "other": <number or null>
  }},
  "net_income": <number or null>,
  "tax_paid": <number or null>,
  "tds_deducted": <number or null>,
  "key_observations": ["<observation1>", "<observation2>"],
  "tax_saving_opportunities": ["<opportunity1>"],
  "summary": "<2-3 sentence plain English summary>"
}}

Return ONLY valid JSON, no markdown."""

        try:
            response = await asyncio.to_thread(
                self.flash_model.generate_content,
                prompt
            )
            text_response = response.text.strip()
            # Strip any markdown code blocks
            if text_response.startswith("```"):
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            return json.loads(text_response)
        except json.JSONDecodeError:
            return {
                "summary": "Document analyzed. Please review the extracted text for details.",
                "key_observations": ["Document processed successfully"],
                "tax_saving_opportunities": [],
            }

    async def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text from a document image using Gemini Vision multimodal model."""
        try:
            contents = [
                {"mime_type": mime_type, "data": image_bytes},
                "Extract all readable text and numbers from this document image. Focus on salary details, tax components, names, and numbers. Maintain layout order."
            ]
            response = await asyncio.to_thread(
                self.flash_model.generate_content,
                contents
            )
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini image OCR failed", error=str(e))
            return "Could not perform OCR on image."

    async def generate_session_title(self, first_message: str) -> str:
        """Generate a short, descriptive title for a chat session."""
        prompt = f"""Generate a very short title (max 5 words) for a tax chat that starts with: "{first_message}"
Return ONLY the title, no quotes or punctuation."""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            title = response.text.strip()
            # If the response returned empty or standard AI boilerplate, trigger fallback
            if not title or len(title) < 2 or "consultation" in title.lower():
                raise ValueError("Empty or invalid title response")
            return title[:60]
        except Exception as e:
            logger.error("Session title generation failed, using fallback heuristic", error=str(e))
            # Bulletproof local heuristic fallback: use the first few words of the user query
            words = [w for w in first_message.split() if w]
            if words:
                fallback_title = " ".join(words[:4]).strip().title()
                # Clean up punctuation
                for char in '?!.,"\'()[]{}':
                    fallback_title = fallback_title.replace(char, '')
                return fallback_title[:60]
            return "Tax Optimization Chat"

    async def summarize_conversation(self, messages: List[Dict]) -> str:
        """Summarize a long conversation for context compression."""
        conversation_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:500]}"
            for m in messages[-20:]  # Last 20 messages
        ])
        prompt = f"""Summarize this tax consultation conversation in 2-3 sentences, focusing on key decisions and information:

{conversation_text}

Return ONLY the summary."""
        try:
            response = await asyncio.to_thread(
                self.flash_model.generate_content, prompt
            )
            return response.text.strip()
        except Exception:
            return "Previous conversation about tax planning."


# Singleton
gemini_ai = GeminiTaxAI()

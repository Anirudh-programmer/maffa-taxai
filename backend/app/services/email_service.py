"""
Email Service - Handles sending system notifications and welcome emails.
Features non-blocking SMTP transmission with premium Maffa HTML styling and dev fallbacks.
"""
from typing import Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class EmailService:
    """Production-ready Email Service supporting both local mock logging and live SMTP delivery."""

    @staticmethod
    def _send_smtp_sync(recipient: str, subject: str, html_content: str, text_content: str) -> None:
        """Synchronous helper to execute SMTP delivery in a background thread."""
        import os
        import httpx

        # Check if Vercel SMTP Bridge is configured to bypass Render's SMTP block
        bridge_token = os.environ.get("SMTP_BRIDGE_TOKEN")
        if bridge_token:
            vercel_url = os.environ.get("NEXT_PUBLIC_APP_URL") or "https://taxai-beta.vercel.app"
            bridge_url = f"{vercel_url.rstrip('/')}/api/public/send-email"
            try:
                logger.info("Sending email via Vercel SMTP Bridge...", recipient=recipient)
                response = httpx.post(
                    bridge_url,
                    json={
                        "token": bridge_token,
                        "recipient": recipient,
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                logger.info("Email sent successfully via Vercel SMTP Bridge", recipient=recipient)
                return
            except Exception as e:
                logger.error("Vercel SMTP Bridge failed, falling back to direct SMTP", error=str(e))

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f'"{settings.EMAILS_FROM_NAME}" <{settings.EMAILS_FROM_EMAIL}>'
        msg["To"] = recipient

        # Attach text and html versions
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Connect and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_SECURE:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, recipient, msg.as_string())

    async def send_welcome_email(self, email: str, full_name: Optional[str] = None) -> bool:
        """
        Sends a premium, responsive welcome email to the user.
        If SMTP settings are present, dispatches live email. Otherwise, falls back to mock console logs.
        """
        name = full_name or email.split("@")[0]
        subject = "Welcome to Maffa TaxAI - Premium AI Tax Advisor!"

        # Plain Text Fallback
        text_content = f"""
        Hello {name},

        Welcome to Maffa TaxAI! We are thrilled to welcome you to our family.
        Maffa is your ultimate AI-driven tax optimization agent designed to optimize your Indian income tax planning. Our platform seamlessly audits your Form 16, parses salary slips with optical precision, and dynamically calculates the highest-yielding deductions under both tax regimes to save you maximum money.

        WHO IS MAFFA?
        Maffa is our state-of-the-art AI engine designed to perform complex optimization tasks across tax and financial strategy planning.

        WHAT MAFFA CAN DO FOR YOU:
        - Compare old & new Indian Tax Regimes with mathematical precision.
        - Perform deep semantic scans on your Form 16s and salary slips.
        - Uncover proactive, high-yield tax deductions.

        Get started today: http://localhost:3000/dashboard

        To your financial optimization,
        The Maffa TaxAI Team
        """

        # Premium HTML Version
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{subject}</title>
          <style>
            body {{
              font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              background-color: #030712;
              color: #f3f4f6;
              margin: 0;
              padding: 0;
              -webkit-font-smoothing: antialiased;
            }}
            .wrapper {{
              width: 100%;
              background-color: #030712;
              padding: 40px 20px;
              box-sizing: border-box;
            }}
            .container {{
              max-width: 600px;
              margin: 0 auto;
              background: linear-gradient(135deg, #0b1528 0%, #030712 100%);
              border: 1px solid rgba(255, 255, 255, 0.05);
              border-radius: 24px;
              overflow: hidden;
              box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            }}
            .header {{
              background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%);
              padding: 35px 40px;
              text-align: center;
              border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .header h1 {{
              margin: 0;
              font-size: 26px;
              font-weight: 800;
              letter-spacing: 2px;
              color: #ffffff;
              text-transform: uppercase;
            }}
            .header p {{
              margin: 8px 0 0 0;
              font-size: 13px;
              color: rgba(255, 255, 255, 0.85);
              letter-spacing: 0.5px;
            }}
            .content {{
              padding: 40px;
            }}
            .greeting {{
              font-size: 18px;
              font-weight: 600;
              color: #ffffff;
              margin-top: 0;
              margin-bottom: 16px;
            }}
            .body-text {{
              font-size: 14px;
              line-height: 1.6;
              color: #9ca3af;
              margin-bottom: 30px;
            }}
            .feature-box {{
              background: rgba(255, 255, 255, 0.02);
              border: 1px solid rgba(255, 255, 255, 0.05);
              border-radius: 16px;
              padding: 24px;
              margin-bottom: 30px;
            }}
            .feature-title {{
              font-size: 15px;
              font-weight: 700;
              color: #14b8a6;
              margin-top: 0;
              margin-bottom: 12px;
              text-transform: uppercase;
              letter-spacing: 0.5px;
            }}
            .feature-list {{
              margin: 0;
              padding: 0;
              list-style: none;
            }}
            .feature-item {{
              font-size: 13.5px;
              color: #d1d5db;
              margin-bottom: 10px;
              padding-left: 20px;
              position: relative;
            }}
            .feature-item::before {{
              content: "✦";
              position: absolute;
              left: 0;
              color: #14b8a6;
            }}
            .cta-button {{
              display: inline-block;
              background: linear-gradient(90deg, #0d9488 0%, #14b8a6 100%);
              color: #ffffff !important;
              text-decoration: none !important;
              font-weight: 600;
              font-size: 14px;
              padding: 14px 30px;
              border-radius: 12px;
              text-align: center;
              box-shadow: 0 10px 20px rgba(20, 184, 166, 0.2);
              transition: all 0.3s ease;
            }}
            .footer {{
              padding: 30px 40px;
              background-color: rgba(0, 0, 0, 0.2);
              border-top: 1px solid rgba(255, 255, 255, 0.03);
              text-align: center;
              font-size: 11px;
              color: #4b5563;
              line-height: 1.5;
            }}
            .footer a {{
              color: #14b8a6;
              text-decoration: none;
            }}
          </style>
        </head>
        <body>
          <div class="wrapper">
            <div class="container">
              <div class="header">
                <h1>M A F F A</h1>
                <p>Premium AI Tax Optimization Core</p>
              </div>
              <div class="content">
                <p class="greeting">Hello {name},</p>
                <p class="body-text">
                  Welcome to <strong>Maffa TaxAI</strong>! We are thrilled to welcome you to our family. 
                  Maffa is your ultimate AI-driven tax optimization agent designed to optimize your Indian income tax planning. 
                  Our platform seamlessly audits your Form 16, parses salary slips with optical precision, and dynamically calculates the highest-yielding deductions under both tax regimes to save you maximum money.
                </p>
                
                <div class="feature-box">
                  <p class="feature-title">Who is Maffa?</p>
                  <p class="body-text" style="margin-bottom: 0;">
                    Maffa is our versatile, next-generation optimization core specialized to make Indian Tax planning, regimes, deductions, and Form 16 reconciliation mathematically perfect and extremely high-yield.
                  </p>
                </div>

                <div class="feature-box">
                  <p class="feature-title">What Maffa Can Do For You</p>
                  <ul class="feature-list">
                    <li class="feature-item">Compare Old vs. New progressive tax slabs with 100% mathematical precision.</li>
                    <li class="feature-item">Extract and analyze raw text dynamically from your uploaded Salary Slips or Form 16s.</li>
                    <li class="feature-item">Discover active Section 80C, 80D, and progressive deduction leakage flags to reclaim lost capital.</li>
                  </ul>
                </div>

                <div style="text-align: center; margin: 35px 0 10px 0;">
                  <a href="http://localhost:3000/dashboard" class="cta-button">Access Your Tax Dashboard</a>
                </div>
              </div>
              <div class="footer">
                You are receiving this welcome email because you registered an account on Maffa TaxAI.<br>
                © 2026 Maffa TaxAI Core. All rights reserved. · <a href="http://localhost:3000">Visit Maffa TaxAI</a>
              </div>
            </div>
          </div>
        </body>
        </html>
        """

        if settings.SMTP_HOST:
            try:
                # Dispatch async via background thread pool to ensure non-blocking FastAPIs
                await asyncio.to_thread(
                    self._send_smtp_sync,
                    email,
                    subject,
                    html_content,
                    text_content
                )
                logger.info(
                    "Welcome Email Sent Successfully via SMTP",
                    recipient=email,
                    subject=subject,
                    delivery_status="DELIVERED"
                )
                return True
            except Exception as e:
                logger.error(
                    "SMTP Email delivery failed, falling back to mock logs",
                    recipient=email,
                    error=str(e)
                )

        # Fallback Mock Logging for local development
        mock_ascii = f"""
+-------------------------------------------------------------------------------+
|                                  M A F F A                                    |
|                   Premium AI-Powered Tax Optimization Core                    |
+-------------------------------------------------------------------------------+
|                                                                               |
|  Hello {name},                                                                 |
|                                                                               |
|  Welcome to Maffa TaxAI! We are thrilled to welcome you to our family.         |
|  Maffa is your ultimate AI-driven tax optimization agent designed to          |
|  optimize your Indian income tax planning. Our platform seamlessly audits     |
|  your Form 16, parses salary slips with optical precision, and dynamically    |
|  calculates the highest-yielding deductions to save you maximum money.        |
|                                                                               |
|  WHO IS MAFFA?                                                                |
|  Maffa is our state-of-the-art, highly versatile AI engine designed to        |
|  perform complex optimization tasks across a wide array of fields. Now, Maffa  |
|  has been specialized to serve as your intelligent, AI-based Tax Assistant.   |
|                                                                               |
|  WHAT MAFFA CAN DO FOR YOU:                                                    |
|  - Compare old & new Indian Tax Regimes with 100% mathematical precision.     |
|  - Perform deep semantic scans on your Form 16s and investment receipts.      |
|  - Uncover proactive, high-yield tax deductions and strategy planning.        |
|                                                                               |
|  GET STARTED TODAY:                                                           |
|  Log in to your dashboard to run your first simulation or ask Maffa a question!|
|  URL: http://localhost:3000/dashboard                                         |
|                                                                               |
|  To your financial optimization,                                              |
|  The Maffa TaxAI Team                                                         |
|                                                                               |
+-------------------------------------------------------------------------------+
|  You are receiving this welcome email as a registered user of Maffa TaxAI.          |
+-------------------------------------------------------------------------------+
"""
        logger.info(
            "Welcome Email Simulated Successfully (Console Fallback)",
            recipient=email,
            subject=subject,
            delivery_status="SIMULATED_SUCCESS"
        )
        print(mock_ascii)
        return True

# Singleton instance
email_service = EmailService()

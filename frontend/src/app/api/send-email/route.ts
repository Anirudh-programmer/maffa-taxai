import { NextResponse } from 'next/server'
import nodemailer from 'nodemailer'

export async function POST(request: Request) {
  try {
    const { token, recipient, subject, html, text } = await request.json()

    // Secure the endpoint with a shared secret key
    const secretToken = process.env.SMTP_BRIDGE_TOKEN
    if (!secretToken || token !== secretToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    if (!recipient || !subject || (!html && !text)) {
      return NextResponse.json({ error: 'Missing required email fields' }, { status: 400 })
    }

    // SMTP configuration from Vercel environment variables
    const transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT || '587', 10),
      secure: process.env.SMTP_SECURE === 'true', // false for 587 starttls, true for 465 SSL
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASSWORD,
      },
    })

    const mailOptions = {
      from: `"${process.env.EMAILS_FROM_NAME || 'Maff TaxAI'}" <${process.env.EMAILS_FROM_EMAIL || process.env.SMTP_USER}>`,
      to: recipient,
      subject: subject,
      text: text,
      html: html,
    }

    await transporter.sendMail(mailOptions)

    return NextResponse.json({ success: true, message: 'Email sent successfully via Vercel SMTP Bridge' })
  } catch (error: any) {
    console.error('SMTP Bridge error:', error)
    return NextResponse.json({ error: 'Failed to send email', details: error.message }, { status: 500 })
  }
}

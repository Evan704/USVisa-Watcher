# notifier.py
import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Settings

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self, settings: "Settings"):
        self.settings = settings

    def send_notification(self, available_date: date) -> bool:
        """Send email notification about available appointment date."""
        try:
            msg = self._build_message(available_date)

            # Use SSL for port 465, STARTTLS for port 587
            if self.settings.smtp_port == 465:
                # SSL connection (QQ, 163, etc.)
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as server:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                    server.send_message(msg)
            else:
                # STARTTLS connection (Gmail, Outlook, etc.)
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                    server.starttls()
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                    server.send_message(msg)

            logger.info(
                f"Notification sent to {self.settings.notify_email} "
                f"for date {available_date}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _build_message(self, available_date: date) -> MIMEMultipart:
        """Build the email message."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"[美签预约提醒] {self.settings.city} {self.settings.visa_type} "
            f"新名额: {available_date}"
        )
        msg["From"] = self.settings.smtp_user
        msg["To"] = self.settings.notify_email

        text_body = f"""美签预约提醒

城市: {self.settings.city}
签证类型: {self.settings.visa_type}
签证类别: {self.settings.visa_category}

最新可预约日期: {available_date}

该日期早于您设定的目标日期 ({self.settings.target_date})，请尽快登录系统预约！

---
本邮件由自动脚本发送
"""

        html_body = f"""\
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #d32f2f;">美签预约提醒</h2>
    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">城市</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{self.settings.city}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">签证类型</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{self.settings.visa_type}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">签证类别</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{self.settings.visa_category}</td>
        </tr>
    </table>
    <p style="font-size: 18px; margin: 20px 0;">
        <strong>最新可预约日期:</strong>
        <span style="color: #d32f2f; font-size: 24px;">{available_date}</span>
    </p>
    <p style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107;">
        该日期早于您设定的目标日期 <strong>{self.settings.target_date}</strong>，请尽快登录系统预约！
    </p>
    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">本邮件由自动脚本发送</p>
</body>
</html>
"""

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        return msg

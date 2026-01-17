import smtplib
import logging
import threading
import atexit
from collections import deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
import traceback


def send_alert(from_addr, to_addr, subject, body, pwdfile, smtp_server, smtp_port=587):
    """Send an email alert.

    Args:
        from_addr: Email address to send from
        to_addr: Email address(es) to send to (string or list of strings)
        subject: Email subject line
        body: Email body text
        pwdfile: Path to password file (relative to home directory)
        smtp_server: SMTP server address
        smtp_port: SMTP server port (default: 587)
    """
    pwd = Path.home().joinpath(pwdfile).read_text().strip()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr if isinstance(to_addr, str) else ", ".join(to_addr)

    with smtplib.SMTP(smtp_server, smtp_port) as s:
        s.starttls()
        s.login(from_addr, pwd)
        s.send_message(msg)


def send_html_alert(from_addr, to_addr, subject, html_body, pwdfile, smtp_server, smtp_port=587):
    """Send an email alert with HTML formatting.

    Args:
        from_addr: Email address to send from
        to_addr: Email address(es) to send to (string or list of strings)
        subject: Email subject line
        html_body: Email body as HTML
        pwdfile: Path to password file (relative to home directory)
        smtp_server: SMTP server address
        smtp_port: SMTP server port (default: 587)
    """
    pwd = Path.home().joinpath(pwdfile).read_text().strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr if isinstance(to_addr, str) else ", ".join(to_addr)

    # Attach HTML part
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    with smtplib.SMTP(smtp_server, smtp_port) as s:
        s.starttls()
        s.login(from_addr, pwd)
        s.send_message(msg)


class EmailHandler(logging.Handler):
    """Logging handler that sends ERROR and above to email when script ends.

    Args:
        from_addr: Email address to send from
        to_addr: Email address(es) to send to (string or list of strings)
        subject_prefix: Prefix for email subjects (e.g., "[ALERT]")
        pwdfile: Path to password file (relative to home directory)
        smtp_server: SMTP server address
        smtp_port: SMTP server port (default: 587)
        max_batch_size: Maximum errors per batch; sends immediately when reached (default: None for unlimited)
    """

    def __init__(self, from_addr, to_addr, subject_prefix, pwdfile, smtp_server,
                 smtp_port=587, max_batch_size=None):
        super().__init__(level=logging.ERROR)
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.subject_prefix = subject_prefix
        self.pwdfile = pwdfile
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.max_batch_size = max_batch_size

        # Batching
        self.error_queue = deque()
        self.batch_lock = threading.Lock()

        # Auto-flush on program exit
        atexit.register(self.flush)

    def emit(self, record):
        """Collect log record for batched email sending."""
        try:
            with self.batch_lock:
                self.error_queue.append(record)

                # Send immediately if batch size limit is reached
                if self.max_batch_size and len(self.error_queue) >= self.max_batch_size:
                    self._send_batch()
        except Exception:
            self.handleError(record)

    def _send_batch(self, wait=False):
        """Send batched errors as a single email.

        Args:
            wait: If True, wait for email to send before returning (for flush/close)
        """
        with self.batch_lock:
            if not self.error_queue:
                return

            # Collect all queued errors
            records = list(self.error_queue)
            self.error_queue.clear()

            # Send in background thread
            thread = threading.Thread(
                target=self._send_email_batch,
                args=(records,),
                daemon=not wait  # Non-daemon if we need to wait
            )
            thread.start()

            # Wait for completion if requested (e.g., during flush/close)
            if wait:
                thread.join(timeout=30)  # 30 second timeout for email sending

    def _send_email_batch(self, records):
        """Send the actual email (runs in background thread)."""
        try:
            if len(records) == 1:
                subject = f"{self.subject_prefix} {records[0].levelname}: {records[0].getMessage()}"
            else:
                subject = f"{self.subject_prefix} {len(records)} errors occurred"

            html_body = self._format_html_batch(records)

            send_html_alert(
                from_addr=self.from_addr,
                to_addr=self.to_addr,
                subject=subject,
                html_body=html_body,
                pwdfile=self.pwdfile,
                smtp_server=self.smtp_server,
                smtp_port=self.smtp_port
            )
        except Exception as e:
            # Log to stderr since we can't use the handler
            print(f"EmailHandler failed to send: {e}", flush=True)

    def _format_html_batch(self, records):
        """Format log records as HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .error-container { margin: 20px 0; padding: 15px; border-left: 4px solid #d32f2f; background: #ffebee; }
                .critical-container { margin: 20px 0; padding: 15px; border-left: 4px solid #b71c1c; background: #ffcdd2; }
                .error-header { font-weight: bold; color: #d32f2f; margin-bottom: 10px; }
                .critical-header { font-weight: bold; color: #b71c1c; margin-bottom: 10px; }
                .error-time { color: #666; font-size: 0.9em; }
                .error-location { color: #666; font-size: 0.9em; margin: 5px 0; }
                .error-message { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }
                .stacktrace { background: #263238; color: #aed581; padding: 15px; border-radius: 4px;
                             overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.85em;
                             white-space: pre-wrap; word-wrap: break-word; }
                .summary { background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
        """

        if len(records) > 1:
            html += f"""
            <div class="summary">
                <strong>Summary:</strong> {len(records)} error(s) occurred<br>
                <strong>Time Range:</strong> {self._format_time(records[0].created)} - {self._format_time(records[-1].created)}
            </div>
            """

        for i, record in enumerate(records, 1):
            container_class = "critical-container" if record.levelname == "CRITICAL" else "error-container"
            header_class = "critical-header" if record.levelname == "CRITICAL" else "error-header"

            html += f"""
            <div class="{container_class}">
                <div class="{header_class}">
                    {"Error " + str(i) + " - " if len(records) > 1 else ""}{record.levelname}: {record.getMessage()}
                </div>
                <div class="error-time">Time: {self._format_time(record.created)}</div>
                <div class="error-location">
                    Location: {record.pathname}:{record.lineno} in {record.funcName}()
                </div>
            """

            if record.exc_info:
                exc_text = ''.join(traceback.format_exception(*record.exc_info))
                html += f"""
                <div class="error-message">
                    <strong>Stack Trace:</strong>
                    <div class="stacktrace">{self._escape_html(exc_text)}</div>
                </div>
                """

            html += "</div>"

        html += """
        </body>
        </html>
        """
        return html

    @staticmethod
    def _format_time(timestamp):
        """Format timestamp as readable string."""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _escape_html(text):
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def flush(self):
        """Flush any pending errors immediately."""
        if self.error_queue:
            self._send_batch(wait=True)

    def close(self):
        """Close handler and flush any pending errors."""
        self.flush()
        super().close()

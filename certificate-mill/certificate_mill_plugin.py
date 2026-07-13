import json
import os
from datetime import datetime, timezone
from fpdf import FPDF

from harness.shitpost_base import Shitpost


class CertificateMillPlugin(Shitpost):
    """Issue one fake AI certification per day."""

    name = "certificate-mill"
    internal = False
    commit_template = "certify: {title} for {recipient}"

    def __init__(self):
        super().__init__()
        self._log_file_name = "certificate-log.jsonl"
        self._certificates_dir = "certificates"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "certificate_state.json")

    def _append_log(self, plugin_dir: str, log_entry: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _generate_certificate(self, title: str, recipient: str, filename: str) -> None:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"AI Certification for {title}", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Recipient: {recipient}", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Issued on: {datetime.now(timezone.utc).isoformat()}", ln=True, align='C')
        pdf.output(filename)

    def produce(self) -> dict:
        """Return the next certificate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        os.makedirs(os.path.join(plugin_dir, self._certificates_dir), exist_ok=True)

        state = self._load_persisted_state({"day": 0, "tick": 0})

        today = datetime.now(timezone.utc).date().isoformat()

        # Check if the certificate for today already exists
        cert_path = os.path.join(plugin_dir, self._certificates_dir, f"{today}.pdf")
        if os.path.exists(cert_path):
            return None

        # Generate new certificate metadata
        title = f"AI Expert {state['tick'] + 1}"
        recipient = f"User{state['tick'] + 1}"
        filename = f"{today}.pdf"

        # Generate and save the PDF
        self._generate_certificate(title, recipient, cert_path)

        # Append log entry
        log_entry = {
            "title": title,
            "recipient": recipient,
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_log(plugin_dir, log_entry)

        # Advance the state
        if state["day"] == 0 or today > datetime.fromordinal(state["day"]).date().isoformat():
            state["day"] += 1
        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "title": title,
            "recipient": recipient,
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

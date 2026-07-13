import json
import os
import sys
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
        self._state_file_name = "certificate_state.json"
        self._log_file_name = "certificate-log.jsonl"
        self._certificates_dir = "certificates"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running certificate state, or initialise it at day 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: certificate state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"day", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: certificate state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next day to emit is always ``day``.
            "day": 0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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

        state = self._load_state(plugin_dir)

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
        state["day"] += 1 if today > datetime.fromordinal(state['day']).date().isoformat() else 0
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "title": title,
            "recipient": recipient,
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

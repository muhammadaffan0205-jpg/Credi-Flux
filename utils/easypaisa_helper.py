# crediflux/utils/easypaisa_helper.py
import webbrowser
import subprocess
import sys
from config import EASYPAISA_URL

class EasypaisaHelper:
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        try:
            if sys.platform == "win32":
                subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
            elif sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            else:
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
                except FileNotFoundError:
                    subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode("utf-8"), check=True)
            return True
        except Exception:
            return False

    @staticmethod
    def open_easypaisa() -> None:
        webbrowser.open(EASYPAISA_URL)

    @staticmethod
    def format_amount(amount: float) -> str:
        return f"Rs. {amount:,.0f}"
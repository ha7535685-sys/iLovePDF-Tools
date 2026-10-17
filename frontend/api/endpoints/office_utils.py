import os
import shutil
import subprocess
import glob
import tempfile

LO_PROFILE_DIR = os.path.join(tempfile.gettempdir(), "lo_profile").replace("\\", "/")


def find_soffice() -> str | None:
    """Find the LibreOffice / OpenOffice executable."""
    env_path = os.getenv("SOFFICE_PATH", "")
    if env_path and os.path.isfile(env_path):
        return env_path

    which_path = shutil.which("soffice")
    if which_path and os.path.isfile(which_path):
        return which_path

    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice 7\program\soffice.exe",
        r"C:\Program Files\OpenOffice 4\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def convert_office_to_pdf(input_path: str, output_dir: str, timeout: int = 30) -> str:
    """Convert a Word (.doc, .docx) or Excel (.xls, .xlsx) file to PDF using LibreOffice headless.
    Returns the absolute path to the generated PDF.
    """
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice executable not found on system.")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(LO_PROFILE_DIR, exist_ok=True)
    ext = os.path.splitext(input_path)[1].lower()

    if ext in [".xls", ".xlsx"]:
        convert_to_arg = "pdf:calc_pdf_Export"
    elif ext in [".doc", ".docx"]:
        convert_to_arg = "pdf:writer_pdf_Export"
    else:
        convert_to_arg = "pdf"

    abs_input = os.path.abspath(input_path)
    abs_outdir = os.path.abspath(output_dir)

    cmd = [
        soffice,
        f"-env:UserInstallation=file:///{LO_PROFILE_DIR}",
        "--headless",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--nologo",
        "--convert-to",
        convert_to_arg,
        "--outdir",
        abs_outdir,
        abs_input,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"LibreOffice conversion failed (exit code {result.returncode}): {error_msg}")

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    expected_output = os.path.join(output_dir, f"{base_name}.pdf")

    if os.path.exists(expected_output):
        return expected_output

    matches = glob.glob(os.path.join(output_dir, "*.pdf"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Expected converted PDF not found at {expected_output}")

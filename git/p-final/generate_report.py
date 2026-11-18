from html import escape
from pathlib import Path
import json
import re
import sys
import tkinter as tk
from tkinter import filedialog
import webbrowser

BASE_DIR = Path(__file__).resolve().parent


def choose_response() -> Path:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).expanduser().resolve()
        if path.exists():
            return path
        raise SystemExit(f"فایل پاسخ پیدا نشد: {path}")
    root = tk.Tk()
    root.withdraw()
    selected = filedialog.askopenfilename(
        title="فایل پاسخ JSON هوش مصنوعی را انتخاب کنید",
        filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
        initialdir=str(BASE_DIR),
    )
    root.destroy()
    if not selected:
        raise SystemExit("هیچ فایل پاسخی انتخاب نشد.")
    return Path(selected)


def load_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise SystemExit("پاسخ انتخاب‌شده JSON معتبر نیست.")
        return json.loads(match.group(0))


def as_list(value):
    return value if isinstance(value, list) else []


def build_report(data: dict, source_name: str) -> str:
    devices = "".join(
        f"<tr><td>{escape(str(item.get('device', '')))}</td><td>{escape(str(item.get('status', '')))}</td><td>{escape(str(item.get('details', '')))}</td></tr>"
        for item in as_list(data.get("device_status")) if isinstance(item, dict)
    )
    errors = "".join(
        f"<article class='error'><h3>اولویت {escape(str(item.get('priority', '')))}: {escape(str(item.get('problem', '')))}</h3><p><b>شواهد:</b> {escape(str(item.get('evidence', '')))}</p><p><b>اطمینان:</b> {escape(str(item.get('confidence', '')))}</p></article>"
        for item in as_list(data.get("possible_errors")) if isinstance(item, dict)
    ) or "<p>خطای مشخصی ثبت نشده است.</p>"
    solutions = "".join(
        f"<article class='solution'><h3>{escape(str(item.get('problem', '')))}</h3><p>{escape(str(item.get('explanation', '')))}</p><pre>{escape(chr(10).join(str(c) for c in as_list(item.get('commands'))))}</pre></article>"
        for item in as_list(data.get("solutions")) if isinstance(item, dict)
    ) or "<p>راه‌حلی ثبت نشده است.</p>"
    tests = "".join(f"<li>{escape(str(item))}</li>" for item in as_list(data.get("next_tests"))) or "<li>تست دیگری ثبت نشده است.</li>"
    return f'''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>گزارش عیب‌یابی شبکه</title>
<style>
@font-face{{font-family:IRANSansLocal;src:local("IRANSans"),local("IRANSansWeb")}}
body{{font-family:IRANSansLocal,IRANSans,Tahoma,Arial,sans-serif;background:#f4f6f8;color:#17202a;max-width:950px;margin:35px auto;padding:0 18px;line-height:1.9}}
h1{{text-align:center;color:#123b5d;font-size:25px}}.card{{background:#fff;border:1px solid #d8dee4;border-radius:10px;padding:18px;margin:18px 0;box-shadow:0 2px 8px #00000010}}h2{{color:#075985;border-bottom:1px solid #e5e7eb;padding-bottom:7px}}
.summary{{background:#e0f2fe;border-right:4px solid #0284c7;padding:12px 16px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d8dee4;padding:8px;text-align:right}}th{{background:#e0f2fe}}.error{{border-right:4px solid #d97706;background:#fffbeb;padding:8px 14px;margin:10px 0}}.solution{{border-right:4px solid #059669;background:#ecfdf5;padding:8px 14px;margin:10px 0}}pre{{direction:ltr;text-align:left;background:#17202a;color:#f8fafc;padding:12px;border-radius:6px;white-space:pre-wrap;font-family:Consolas,monospace}}button{{font-family:inherit;background:#075985;color:#fff;border:0;border-radius:7px;padding:10px 18px;font-size:15px;cursor:pointer}}
</style></head><body><h1>گزارش هوشمند عیب‌یابی شبکه</h1>
<div class="summary"><b>وضعیت کلی:</b> {escape(str(data.get('summary', 'گزارشی تولید نشده است')))}<br><b>اطمینان کلی:</b> {escape(str(data.get('confidence', 'نامشخص')))}</div>
<section class="card"><h2>وضعیت تجهیزات</h2><table><tr><th>تجهیز</th><th>وضعیت</th><th>جزئیات</th></tr>{devices or '<tr><td colspan="3">اطلاعاتی ثبت نشده است.</td></tr>'}</table></section>
<section class="card"><h2>خطاهای احتمالی</h2>{errors}</section><section class="card"><h2>راه‌حل‌های پیشنهادی</h2>{solutions}</section>
<section class="card"><h2>تست‌های بعدی</h2><ul>{tests}</ul></section><p>منبع پاسخ: {escape(source_name)}</p><button onclick="window.print()">چاپ یا ذخیره PDF</button></body></html>'''


def main() -> None:
    source = choose_response()
    output = source.parent / "report.html"
    output.write_text(build_report(load_json(source), source.name), encoding="utf-8")
    print(f"گزارش ساخته شد: {output}")
    webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()

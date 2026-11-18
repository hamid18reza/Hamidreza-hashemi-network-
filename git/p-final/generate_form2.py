from pathlib import Path
import re
import sys
import webbrowser
import json
from html import escape
import tkinter as tk
from tkinter import filedialog

BASE_DIR = Path(__file__).resolve().parent
FORM1 = BASE_DIR / "form1.txt"
FORM1_FILLED = BASE_DIR / "form1-filled.txt"
FORM1_HTML = BASE_DIR / "form1.html"
FORM2 = BASE_DIR / "form2.txt"
FORM2_HTML = BASE_DIR / "form2.html"


def read_fields(path: Path) -> dict[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Z_]+):\s*(.*)$", line.strip())
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def names(value: str) -> list[str]:
    result = [item.strip() for item in value.split(",") if item.strip()]
    return result


def commands_for(problem: str, services: str, device_type: str) -> list[str]:
    text = f"{problem} {services}".lower()
    commands = ["show ip interface brief"]

    if device_type == "router" and any(word in text for word in ["dhcp", "ip", "آدرس", "دریافت"]):
        commands += ["show ip dhcp binding", "show ip dhcp pool"]
    if device_type == "router" and any(word in text for word in ["روتینگ", "roas", "vlan"]):
        commands.append("show running-config | section interface")
    if device_type == "switch" and any(word in text for word in ["vlan", "trunk", "روتینگ", "roas"]):
        commands += ["show vlan brief", "show interfaces trunk"]
    if device_type == "switch" and any(word in text for word in ["etherchannel", "lacp", "pagp"]):
        commands.append("show etherchannel summary")
    if device_type == "switch" and any(word in text for word in ["stp", "spanning"]):
        commands.append("show spanning-tree")
    if any(word in text for word in ["ssh", "telnet", "مدیریت"]):
        commands.append("show running-config | section line vty")
    if len(commands) == 1:
        commands.append("show cdp neighbors")
    return list(dict.fromkeys(commands))


def device_block(device: str, commands: list[str]) -> list[str]:
    lines = [f"===== {device} =====", ""]
    for command in commands:
        lines += [f"دستور: {command}", "خروجی:", "[خروجی را اینجا وارد کنید]", ""]
    return lines


def html_device_block(device: str, commands: list[str]) -> list[str]:
    lines = [f'<section class="device"><h2>{escape(device)}</h2>']
    for index, command in enumerate(commands, start=1):
        field_id = f"{re.sub(r'[^A-Za-z0-9_-]', '_', device)}_{index}"
        lines += [
            '<div class="command-row" dir="ltr">',
            f"<code>{escape(command)}</code>",
            f'<button class="copy-btn" data-command="{escape(command, quote=True)}" onclick="copyCommand(this)">کپی دستور</button>',
            "</div>",
            f'<label for="{field_id}">خروجی دستور:</label>',
            f'<textarea id="{field_id}" data-label="{escape(device)} | {escape(command)}" placeholder="خروجی را اینجا وارد کنید"></textarea>',
        ]
    lines.append("</section>")
    return lines


def build_html(routers: list[str], switches: list[str], problem: str, services: str, initial_fields: dict[str, str], prompt_text: str) -> str:
    form1_text = "فرم ۱: اطلاعات اولیه شبکه\n\n" + "\n".join(
        f"{key}: {initial_fields.get(key, '')}" for key in ["ROUTERS", "SWITCHES", "CLIENTS", "VLANS", "SERVICES", "PROBLEM"]
    )
    form1_js = json.dumps(form1_text, ensure_ascii=False)
    prompt_js = json.dumps(prompt_text, ensure_ascii=False)
    lines = [
        "<!doctype html>",
        '<html lang="fa" dir="rtl">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>فرم عیب‌یابی شبکه</title>",
        "<style>",
        "@font-face{font-family:IRANSansLocal;src:local('IRANSans'),local('IRANSansWeb')}",
        "body{font-family:IRANSansLocal,IRANSans,Tahoma,Arial,sans-serif;background:#f4f6f8;color:#17202a;max-width:950px;margin:35px auto;padding:0 18px;line-height:1.9}",
        "h1{text-align:center;font-size:27px;background:linear-gradient(90deg,#075985,#0e7490,#14b8a6);-webkit-background-clip:text;color:transparent}.device{background:#fff;border:1px solid #d8dee4;border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 4px 14px #07598518;border-right:6px solid #0e7490}.device:nth-of-type(3n+1){border-right-color:#7c3aed}.device:nth-of-type(3n+2){border-right-color:#ea580c}.device:nth-of-type(3n+3){border-right-color:#059669}",
        "h2{margin-top:0;color:#075985;border-bottom:2px solid #bae6fd;padding-bottom:7px}.command-row{direction:ltr;text-align:left;background:linear-gradient(135deg,#17202a,#164e63);color:#f8fafc;border-radius:7px;padding:9px 10px;margin-top:12px;font-family:Consolas,monospace;display:flex;align-items:center;gap:10px;box-shadow:0 2px 6px #07598522}.command-row code{flex:1}.copy-btn{font-family:IRANSansLocal,IRANSans,Tahoma,sans-serif;background:#14b8a6;color:#fff;border:0;border-radius:5px;padding:5px 9px;cursor:pointer}.copy-btn:hover{background:#0f766e}",
        "label{display:block;margin-top:10px;font-weight:bold;color:#24445c}textarea{direction:ltr;text-align:left;width:100%;min-height:105px;box-sizing:border-box;margin-top:5px;padding:10px;border:1px solid #cbd5e1;border-radius:7px;font-family:Consolas,monospace;font-size:14px;resize:vertical;transition:border-color .2s,box-shadow .2s}textarea:focus{outline:none;border-color:#0e7490;box-shadow:0 0 0 3px #cffafe}",
        ".note{background:#e0f2fe;border-right:4px solid #0284c7;padding:10px 14px;border-radius:7px}.actions{text-align:center;position:sticky;bottom:12px}button{font-family:IRANSansLocal,IRANSans,Tahoma,sans-serif;background:#075985;color:#fff;border:0;border-radius:7px;padding:11px 18px;font-size:15px;cursor:pointer;margin:4px;box-shadow:0 2px 5px #07598533}button:hover{background:#0c4a6e}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>فرم تخصصی عیب‌یابی شبکه</h1>",
        f'<div class="note"><b>مشکل ثبت‌شده:</b> {escape(problem or "در فرم اول وارد نشده است")}<br><b>راهنما:</b> خروجی هر دستور را در کادر همان بخش وارد کنید.</div>',
    ]
    for device in routers:
        lines.extend(html_device_block(device, commands_for(problem, services, "router")))
    for device in switches:
        lines.extend(html_device_block(device, commands_for(problem, services, "switch")))
    lines += [
        '<div class="actions"><button onclick="downloadTxt()">دانلود فرم تکمیل‌شده به‌صورت TXT</button><button onclick="downloadCase()">ساخت فایل نهایی برای هوش مصنوعی</button><button onclick="window.print()">چاپ یا ذخیره PDF</button></div>',
        "<script>",
        "function copyCommand(button){navigator.clipboard.writeText(button.dataset.command).then(()=>{let old=button.textContent;button.textContent='کپی شد';setTimeout(()=>button.textContent=old,1200)}).catch(()=>alert('کپی خودکار انجام نشد؛ دستور را دستی انتخاب کنید.'))}",
        "function downloadTxt(){let out='فرم ۲: اطلاعات تخصصی عیب‌یابی شبکه\\n\\n';document.querySelectorAll('textarea').forEach(x=>{out+='===== '+x.dataset.label+' =====\\n'+(x.value||'خروجی وارد نشده')+'\\n\\n'});let blob=new Blob([out],{type:'text/plain;charset=utf-8'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='form2-filled.txt';a.click();URL.revokeObjectURL(a.href)}",
        f"function downloadCase(){{let out='===== دستور تحلیل هوش مصنوعی =====\\n'+{prompt_js}+ '\\n\\n===== اطلاعات فرم ۱ =====\\n'+{form1_js}+'\\n\\n===== خروجی فرم ۲ =====\\n';document.querySelectorAll('textarea').forEach(x=>{{out+='===== '+x.dataset.label+' =====\\n'+(x.value||'خروجی وارد نشده')+'\\n\\n'}});let blob=new Blob([out],{{type:'text/plain;charset=utf-8'}});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='network_case.txt';a.click();URL.revokeObjectURL(a.href)}}",
        "</script>",
        "</body>",
        "</html>",
    ]
    return "\n".join(lines)


def choose_form1() -> Path:
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise SystemExit(f"فایل پیدا نشد: {candidate}")
    preferred = FORM1_FILLED if FORM1_FILLED.exists() else None
    if preferred:
        return preferred
    root = tk.Tk()
    root.withdraw()
    selected = filedialog.askopenfilename(
        title="فایل فرم اول تکمیل‌شده را انتخاب کنید",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialdir=str(BASE_DIR),
    )
    root.destroy()
    if selected:
        return Path(selected)
    raise SystemExit("هیچ فایل فرم اولی انتخاب نشد.")


def build_form1_html(fields: dict[str, str]) -> str:
    values = {key: escape(value) for key, value in fields.items()}
    return f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>فرم اطلاعات اولیه شبکه</title>
<style>
@font-face{{font-family:IRANSansLocal;src:local("IRANSans"),local("IRANSansWeb")}}
body{{font-family:IRANSansLocal,IRANSans,Tahoma,Arial,sans-serif;background:#f4f6f8;color:#17202a;max-width:820px;margin:35px auto;padding:0 18px;line-height:1.9}}
h1{{text-align:center;color:#123b5d;font-size:25px}}.card{{background:#fff;border:1px solid #d8dee4;border-radius:12px;padding:24px;box-shadow:0 3px 12px #00000012}}
label{{display:block;margin-top:14px;font-weight:bold;color:#24445c}}input,textarea{{font-family:inherit;width:100%;box-sizing:border-box;padding:11px;margin-top:5px;border:1px solid #cbd5e1;border-radius:7px;font-size:15px;direction:rtl}}
textarea{{min-height:85px;resize:vertical}}.hint{{background:#e0f2fe;border-right:4px solid #0284c7;padding:10px 14px;margin-bottom:18px}}.actions{{text-align:center;margin-top:20px}}
button{{font-family:inherit;background:#075985;color:#fff;border:0;border-radius:7px;padding:11px 20px;font-size:15px;cursor:pointer;margin:4px}}button:hover{{background:#0c4a6e}}
</style></head><body>
<h1>فرم اطلاعات اولیه شبکه</h1>
<div class="card"><div class="hint">اطلاعات شبکه را وارد کنید. نام تجهیزات را با ویرگول جدا کنید.</div>
<label>تعداد و نام روترها</label><input id="ROUTERS" value="{values.get('ROUTERS','')}" placeholder="مثال: Router0">
<label>تعداد و نام سوئیچ‌ها</label><input id="SWITCHES" value="{values.get('SWITCHES','')}" placeholder="مثال: SW1, SW2, SW3">
<label>تعداد کلاینت‌ها</label><input id="CLIENTS" value="{values.get('CLIENTS','')}" placeholder="مثال: 12">
<label>شماره VLANها</label><input id="VLANS" value="{values.get('VLANS','')}" placeholder="مثال: 10, 20, 30">
<label>سرویس‌ها و قابلیت‌های استفاده‌شده</label><textarea id="SERVICES" placeholder="مثال: DHCP, ROAS, EtherChannel, STP">{values.get('SERVICES','')}</textarea>
<label>شرح کوتاه مشکل</label><textarea id="PROBLEM" placeholder="مشکل شبکه را کوتاه و ساده توضیح دهید">{values.get('PROBLEM','')}</textarea>
<div class="actions"><button onclick="downloadForm1()">دانلود فرم تکمیل‌شده</button><button onclick="window.print()">چاپ یا ذخیره PDF</button></div>
</div>
<script>
function downloadForm1(){{let keys=['ROUTERS','SWITCHES','CLIENTS','VLANS','SERVICES','PROBLEM'];let out='فرم ۱: اطلاعات اولیه شبکه\\n\\n';keys.forEach(k=>{{out+=k+': '+document.getElementById(k).value+'\\n'}});let blob=new Blob([out],{{type:'text/plain;charset=utf-8'}});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='form1-filled.txt';a.click();URL.revokeObjectURL(a.href)}}
</script></body></html>'''


def main() -> None:
    source_form = choose_form1()

    fields = read_fields(source_form)
    prompt_file = BASE_DIR / "master_prompt.txt"
    prompt_text = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""
    FORM1_HTML.write_text(build_form1_html(fields), encoding="utf-8")
    output_dir = source_form.parent
    form2 = output_dir / "form2.txt"
    form2_html = output_dir / "form2.html"
    routers = names(fields.get("ROUTERS", ""))
    switches = names(fields.get("SWITCHES", ""))
    problem = fields.get("PROBLEM", "")
    services = fields.get("SERVICES", "")
    lines = [
        "فرم ۲: اطلاعات تخصصی عیب‌یابی شبکه",
        "",
        f"مشکل ثبت‌شده: {problem or '[در فرم اول وارد نشده است]'}",
        "",
        "راهنما: خروجی هر دستور را دقیقاً زیر همان دستور وارد کنید.",
        "اگر دستوری خروجی ندارد، بنویسید: خروجی ندارد",
        "",
    ]

    for device in routers:
        lines.extend(device_block(device, commands_for(problem, services, "router")))
    for device in switches:
        lines.extend(device_block(device, commands_for(problem, services, "switch")))

    form2.write_text("\n".join(lines) + "\n", encoding="utf-8")
    form2_html.write_text(build_html(routers, switches, problem, services, fields, prompt_text), encoding="utf-8")
    print(f"فرم دوم ساخته شد: {form2}")
    print(f"نسخه مرتب HTML ساخته شد: {form2_html}")
    print(f"فرم اول HTML ساخته شد: {FORM1_HTML}")
    webbrowser.open(form2_html.as_uri())


if __name__ == "__main__":
    main()

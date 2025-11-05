from flask import Flask, render_template_string
import traceback

path = r"c:\mypro\templates\login.html"
with open(path, 'r', encoding='utf-8') as f:
    tpl = f.read()

app = Flask(__name__, static_folder=r"c:\mypro\static")

try:
    with app.test_request_context('/'):
        out = render_template_string(tpl, error=None)
    print('RENDER_OK')
except Exception as e:
    print('RENDER_ERROR')
    traceback.print_exc()

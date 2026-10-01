"""Persist provider/model choices; API keys remain in process environment."""
import json
import os
import re
import tempfile
from pathlib import Path
from app_runtime import DATA_DIR


def load(path=None):
    path=Path(path) if path else DATA_DIR/'ai_preferences.json'
    default={'provider':'OpenAI','models':{'OpenAI':'','Gemini':''}}
    if not path.exists():return default
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        if data.get('provider') not in default['models']:return default
        for name in default['models']:
            value=data.get('models',{}).get(name,'')
            if isinstance(value,str) and (not value or re.fullmatch(r'[A-Za-z0-9._-]{1,160}',value)):
                default['models'][name]=value
        default['provider']=data['provider']
    except (OSError,ValueError,AttributeError):pass
    return default


def save(provider,model,path=None):
    if provider not in ('OpenAI','Gemini'):raise ValueError('Nhà cung cấp không hợp lệ')
    model=model.strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,160}',model):raise ValueError('Nhập tên model hợp lệ trước khi lưu')
    path=Path(path) if path else DATA_DIR/'ai_preferences.json';path.parent.mkdir(parents=True,exist_ok=True)
    data=load(path);data['provider']=provider;data['models'][provider]=model
    fd,temporary=tempfile.mkstemp(prefix='.ai_preferences_',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return data


def key_status(provider):
    name='OPENAI_API_KEY' if provider=='OpenAI' else 'GEMINI_API_KEY'
    return name+(' đã được cấu hình trong phiên hiện tại.' if os.environ.get(name) else ' chưa có trong phiên hiện tại; đặt biến môi trường rồi mở lại app.')

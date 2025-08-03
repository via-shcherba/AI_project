import os
import json
import aiofiles # type: ignore
from django.conf import settings # type: ignore
from django.shortcuts import render # type: ignore
from django.http import StreamingHttpResponse # type: ignore
from django.http import JsonResponse, HttpResponse # type: ignore
from django.http import HttpResponseNotFound, HttpResponseBadRequest # type: ignore


def index(request, session_id):
    return render(request, "index.html", {"session_id": session_id})


async def get_script(request):
    cache_buster = request.GET.get('cb')
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    embed_file = 'embed.js'
    script_path = os.path.join(project_root, 'static', 'js', embed_file)

    if os.path.exists(script_path):
        async with aiofiles.open(script_path, 'r') as file:
            params = {'is_local': settings.IS_LOCAL_RUN, 'cache_buster': cache_buster}        
            add_text = f'(function() {{ \nconst params = {json.dumps(params)};\nconst cacheBuster = "{cache_buster}";\n'           
            if settings.CORS_ALLOWED_ORIGINS[0]:            
                add_text += f'const serverUrl = "{settings.CORS_ALLOWED_ORIGINS[0]}";\n'
            script_content = await file.read()          
            script_content = add_text + script_content + '\n })();'       
        return HttpResponse(script_content, content_type="application/javascript")
    
    return JsonResponse({'error': False})


def get_content_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.css':
        return 'text/css'
    elif ext == '.js':
        return 'application/javascript'
    elif ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.webp':
        return 'image/webp'
    elif ext == '.gif':
        return 'image/gif'
    return 'application/octet-stream'


async def get_static_file(request, path):
    if not path:
        return HttpResponseBadRequest("Empty path provided")

    file_path = os.path.join(settings.STATIC_ROOT, path)

    if not os.path.exists(file_path):
        return HttpResponseNotFound("File not found")

    try:
        content_type = get_content_type(file_path)
        async def file_iterator():
            async with aiofiles.open(file_path, mode='rb') as f:
                while True:
                    chunk = await f.read(8192)  
                    if not chunk:
                        break
                    yield chunk
        response = StreamingHttpResponse(file_iterator(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
        return response
    except Exception as e:
        return HttpResponseNotFound(f"Error while serving the file: {str(e)}")
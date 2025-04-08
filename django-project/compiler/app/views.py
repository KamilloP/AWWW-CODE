from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Folder, File, CodeSection, SectionKind, Status, StatusData
from .forms import SignUpForm
import datetime
from django.http import JsonResponse
from django.utils.timezone import make_aware
 
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.first_name = form.cleaned_data.get('name')
            user.save()

            naive_time = datetime.datetime.now()
            time = make_aware(naive_time)

            folder = Folder(
                name = "root",
                owner = user,
                availability_change_date = time,
                content_change_date = time,
            )
            folder.save()

            return HttpResponseRedirect("/app")
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def index(request):
    """View function for home page of site."""
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', {})

@login_required
def file(request):
    if request.method == "POST":
      id = request.POST.get('file_id')
      try:
        file = File.objects.get(pk=id)
      except File.DoesNotExist:
        file = None
      if file and file.owner.id == request.user.id:
        s = ""
        for code in file.codesection_set.all():
          s += code.content
        file_info = {
          'status' : 'success',
          'pk': id,
          'name': file.name,
          'description': file.description,
          'content': s
        }
        return JsonResponse(file_info)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

@login_required
def saveFile(request):
    if request.method == "POST":
      id = request.POST.get('file_id')
      content = request.POST.get('content')
      kind = SectionKind.objects.filter(type='Procedure')[0]
      status = Status.objects.filter(name="Unknown")[0]
      status_data = StatusData.objects.filter(data="Unknown")[0]
      try:
        file = File.objects.get(pk=id)
      except File.DoesNotExist:
        file = None
      if kind and status and status_data and file and content and file.owner.id == request.user.id:
        code_sections = CodeSection.objects.filter(file=file)
        if code_sections.exists():
           code_sections.delete()
        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)
        file.content_change_date = time
        file.save()
        up = file.up
        while up:
          up.content_change_date = time
          up.save()
          up = up.up
        try:
          code_section = CodeSection(
            file = file,
            pub_date = time,
            begin = 1,
            end = content.count('\n') + content.count('\r\n') + 1,
            kind = kind,
            status = status,
            statusData = status_data,
            content = content,
          )
          code_section.save()
        except Exception as e:
          print("Creating failed!")
          response_data = {'status': 'error'}
          return JsonResponse(response_data, status=400)
        response_data = {
          'status' : 'success',
          'pk': id,
        }
        return JsonResponse(response_data)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

def deleteFolderDFS(folder, time):
    if folder.availability:
      folder.availability = False
      folder.availability_change_date = time
      folder.save()
      for file in folder.file_set.all():
        if file.availability:
          file.availability = False
          file.availability_change_date = time
          file.save()
      for child_folder in folder.folder_set.all():
          deleteFolderDFS(child_folder, time)

@login_required
def deleteFolder(request):
    if request.method == "POST":
      id = request.POST.get('folder_id')
      try:
        folder = Folder.objects.get(pk=id)
      except Folder.DoesNotExist:
        folder = None
      if folder and folder.owner.id == request.user.id and folder.up:
          naive_time = datetime.datetime.now()
          time = make_aware(naive_time)
          # In folders that are closer to root I have to change content_date.
          up = folder.up
          while up:
              up.content_change_date = time
              up.save()
              up = up.up
          # Recursive deleting elements in folder because we change availability_change_date
          deleteFolderDFS(folder, time)
          response_data = {'status': 'success', 'pk': id}
          return JsonResponse(response_data)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

@login_required
def deleteFile(request):
    if request.method == "POST":
      id = request.POST.get('file_id')
      try:
        file = File.objects.get(pk=id)
      except File.DoesNotExist:
        file = None
      if request.user.is_authenticated and file and file.owner.id == request.user.id and file.up:
        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)
        file.availability = False
        file.availability_change_date = time
        file.save()
        up = file.up
        while up:
          up.content_change_date = time
          up.save()
          up = up.up
        response_data = {'status': 'success', 'pk': id}
        return JsonResponse(response_data)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

@login_required
def postFolderForm(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name and pk and description:
          try:
            folder = Folder.objects.get(pk=pk)
          except Folder.DoesNotExist:
            folder = None
          if request.user.is_authenticated and folder and folder.owner.id == request.user.id:
            naive_time = datetime.datetime.now()
            time = make_aware(naive_time)
            newFolder = Folder(
                up = folder,
                description = description,
                name = name,
                owner = request.user,
                availability_change_date = time,
                content_change_date = time,
            )
            newFolder.save()
            up = newFolder.up
            while up:
              up.content_change_date = time
              up.save()
              up = up.up
            response_data = {'status': 'success', 'pk': pk, 'new_id': newFolder.pk, 'name': name,}
            return JsonResponse(response_data)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

@login_required
def postFileForm(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name and pk and description:
          try:
            folder = Folder.objects.get(pk=pk)
          except Folder.DoesNotExist:
            folder = None
          if request.user.is_authenticated and folder and folder.owner.id == request.user.id:
            naive_time = datetime.datetime.now()
            time = make_aware(naive_time)
            newFile = File(
                up = folder,
                description = description,
                name = name,
                owner = request.user,
                availability_change_date = time,
                content_change_date = time,
            )
            newFile.save()
            up = newFile.up
            while up:
              up.content_change_date = time
              up.save()
              up = up.up
            response_data = {'status': 'success', 'pk': pk, 'new_id': newFile.pk, 'name': name,}
            return JsonResponse(response_data)
    response_data = {'status': 'error'}
    return JsonResponse(response_data, status=400)

import subprocess

# TODO - kompilacja która uwzględnia opcje kompilatora, zmienia codeSection.
@login_required
def compileFile(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        if pk:
          try:
            file = File.objects.get(pk=pk)
          except File.DoesNotExist:
            file = None
          if request.user.is_authenticated and file and file.owner.id == request.user.id:
            code = ""
            for codeS in file.codesection_set.all():
              code += codeS.content
            # 
            # atexit.register(cleanup_temp_files, temp_file_name, temp_dir)
            with open(file.name, 'w') as f:
              f.write(code)

            # Wywołaj sdcc, używając tymczasowego pliku
            process = subprocess.Popen(['sdcc', '-S', file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            # Prześlij skompilowany kod użytkownikowi
            if process.returncode == 0:
                compiled_code = stdout.decode('utf-8')
                response_data = {'status': "compiled", 'return': 0, 'assm': compiled_code}
                return JsonResponse(response_data)
            else:
                error_message = stderr.decode('utf-8')
                response_data = {'status': "compiled", 'return': process.returncode, 'assm': error_message}
                return JsonResponse(response_data)
    response_data = {'status': "error"}
    return JsonResponse(response_data, status=400)
   
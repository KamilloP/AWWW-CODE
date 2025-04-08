import datetime
import time
import pytz
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_aware
import json
from bs4 import BeautifulSoup
from rest_framework.test import APIClient

from .models import Folder, File, CodeSection, SectionKind, Status, StatusData

def create_basic_user():
    user = User.objects.create_user('myusername', 'myemail@crazymail.com', 'mypassword')
    user.first_name = 'Kamil'
    user.last_name = 'Pilkiewicz'
    user.save()
    return user

def create_root_folder(user, time):
    folder = Folder(
        name = "root",
        owner = user,
        availability_change_date = time,
        content_change_date = time,
    )
    folder.save()
    return folder

def create_basic_file(user, folder, description, name, time):
    file = File(
        up = folder,
        description = description,
        name = name,
        owner = user,
        availability_change_date = time,
        content_change_date = time,
    )
    file.save()
    return file

class FolderModelTests(TestCase):

    def test_folder(self):
        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        user = create_basic_user()
        folder = create_root_folder(user, time)

        duration = folder.content_change_date - folder.availability_change_date  # For build-in functions
        duration_in_s = duration.total_seconds()

        self.assertEqual(str(folder), "root myusername")
        self.assertEqual(folder.content_change_date, folder.availability_change_date)
        self.assertEqual(duration_in_s < 10, True)
        self.assertEqual(duration_in_s > -10, True)
        self.assertEqual(folder.availability, True)
    
class FileModelTests(TestCase):

    def test_file(self):
        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        user = create_basic_user()
        folder = create_root_folder(user, time)
        file = create_basic_file(user, folder, 'Opis', 'file.c', time)
        
        duration = file.content_change_date - file.availability_change_date  # For build-in functions
        duration_in_s = duration.total_seconds()

        self.assertEqual(str(file), "file.c myusername")
        self.assertEqual(file.content_change_date, file.availability_change_date)
        self.assertEqual(duration_in_s < 10, True)
        self.assertEqual(duration_in_s > -10, True)
        self.assertEqual(file.availability, True)
        self.assertEqual(file.up.name, "root")

class StatusDataModelTests(TestCase):
    def test_status_data(self):
        sd = StatusData(
            data = "Unknown",
        )
        sd.save()
        self.assertEqual(sd.data, "Unknown")
        self.assertEqual(str(sd), "Unknown")

class StatusModelTests(TestCase):
    def test_status(self):
        s = Status(
            name = "Unknown",
        )
        s.save()
        self.assertEqual(s.name, "Unknown")
        self.assertEqual(str(s), "Unknown")

class SectionKindModelTests(TestCase):
    def test_section_kind(self):
        sk = SectionKind(
            type = "Procedure",
        )
        sk.save()
        self.assertEqual(sk.type, "Procedure")
        self.assertEqual(str(sk), "Procedure")


class CodeSectionModelTests(TestCase):

    def test_code_section(self):
        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        user = create_basic_user()
        folder = create_root_folder(user, time)
        file = create_basic_file(user, folder, 'Opis', 'file.c', time)
        sk = SectionKind(type = "Procedure",)
        sk.save()
        s = Status(name = "Unknown",)
        s.save()
        sd = StatusData(data = "Unknown",)
        sd.save()
        content = "hello \n how \n are \n u"
        code_section = CodeSection(
          name = 'codesection',
          file = file,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = sk,
          status = s,
          statusData = sd,
          content = content,
        )
        code_section.save()

        self.assertEqual(str(code_section), "codesection file.c")
        self.assertEqual(code_section.end, 4)
        self.assertEqual(code_section.file.up.name, "root")
        self.assertEqual(code_section.description, '')

def addFolder(up, name, user, time, availability):
      folder = Folder(
          name = name,
          owner = user,
          availability_change_date = time,
          content_change_date = time,
      )
      if up:
          folder.up = up
          if folder.up.owner != folder.owner:
              raise AssertionError("Folder owner(" + up.name +") and subfolder(" + name + ") owner must be the same!")
      if not availability:
          folder.availability = False
      folder.save()
      return folder

def addFile(up, name, user, time, availability):
  if up is None:
    raise AssertionError("File " + name + " must be in existing folder!")
  file = File(
      up = up,
      name = name,
      owner = user,
      availability_change_date = time,
      content_change_date = time,
  )
  if not availability:
      file.availability = False
  file.save()
  return file

class IndexViewTestCase(TestCase):

    def setUp(self):
        # Przygotowanie danych testowych
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user.first_name = "testname"
        self.user.save()
        self.index_url = '/app/'

    def test_index_view_redirects_to_login(self):
        # Symulowanie żądania GET na stronie index
        response = self.client.get(self.index_url)

        # Sprawdzenie, czy odpowiedź przekierowuje na stronę logowania
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/')

    def test_index_view_with_authenticated_user(self):
        # Logowanie użytkownika
        self.client.login(username='testuser', password='testpass')

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        # Foldery - sprawdzenie widoku
        root = addFolder(None, 'root', self.user, time, True)
        backend = addFolder(root, 'backend', self.user, time, True)
        frontend = addFolder(root, 'frontend', self.user, time, True)
        notA = addFolder(root, 'not_available', self.user, time, False)
        src = addFolder(backend, 'source', self.user, time, True)

        # Pliki - sprawdzenie widoku
        readme = addFile(root, "README", self.user, time, True)
        sort = addFile(src, "sort.c", self.user, time, True)
        queue = addFile(src, "queue.c", self.user, time, True)
        fNot = addFile(notA, "not", self.user, time, True)

        # Symulowanie żądania GET na stronie index
        response = self.client.get(self.index_url)

        # Sprawdzenie, czy odpowiedź ma kod statusu 200
        self.assertEqual(response.status_code, 200)
        # Sprawdzenie, czy poprawny szablon jest używany
        self.assertTemplateUsed(response, 'index.html')
        
        # Analiza HTML odpowiedzi
        soup = BeautifulSoup(response.content, 'html.parser')

        # Menu
        menu = soup.find('div', class_=['item menu'])
        self.assertIsNotNone(menu, "Menu should be here!")
        ul_menu = menu.find('ul')
        self.assertIsNotNone(ul_menu, "Menu should have ul!")
        self.assertIsNotNone(ul_menu.find('li'), "Menu should have li!")
        # print(ul_menu.findAll('li'))
        self.assertIsNotNone(ul_menu.find('li').find('a'), "Menu should have li a!")
        self.assertIsNotNone(ul_menu.find('li').find('a').text, "User: testuser (testname)")

        # Files
        root_dom = soup.findAll('span', class_=['folder ' + str(root.pk)])
        self.assertEqual(len(root_dom), 1)
        self.assertEqual(root_dom[0].text, "root")
        root_dom = soup.find('span', class_=['folder ' + str(root.pk)])
        li_root = root_dom.parent
        self.assertIsNotNone(li_root.find('span', class_=['insert']), "There is no span insert (folder)!")
        self.assertIsNotNone(li_root.find('span', class_=['delete']), "There is no span delete (folder)!")
        self.assertIsNotNone(li_root.find('span', class_=['file ' + str(readme.pk)]), "No file (README)!")
        self.assertEqual(li_root.find('span', class_=['file ' + str(readme.pk)]).find('a', class_=['file-id']).text, "README")
        self.assertIsNotNone(li_root.find('span', class_=['folder ' + str(frontend.pk)]), "No subfolder(frontend)!")
        self.assertIsNotNone(li_root.find('span', class_=['folder ' + str(backend.pk)]), "No subfolder(backend)!")
        li_backend = li_root.find('span', class_=['folder ' + str(backend.pk)]).parent
        self.assertIsNotNone(li_backend.find('span', class_=['folder ' + str(src.pk)]), "No subfolder(src)!")
        li_src = li_backend.find('span', class_=['folder ' + str(src.pk)]).parent
        self.assertIsNotNone(li_src.find('span', class_=['file ' + str(sort.pk)]), "No file(sort.c)!")
        self.assertIsNotNone(li_src.find('span', class_=['file ' + str(queue.pk)]), "No file(queue.c)!")
        self.assertIsNone(li_src.find('span', class_=['file ' + str(queue.pk + sort.pk)]), "File should not exist!")
        self.assertIsNone(li_src.find('span', class_=['folder ' + str(backend.pk)]), "Backend should not be subfolder for src!")
        self.assertIsNone(li_root.find('span', class_=['folder ' + str(notA.pk)]), "NotA should not be available!")
        self.assertIsNone(li_root.find('span', class_=['file ' + str(fNot.pk)]), "fNot is set as available, but it's folder as not!")

class FileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.emptyFile = addFile(self.root, "empty.c", self.user, time, True)
        self.readme = addFile(self.root, "README", self.user, time, True)
        
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.emptyFile2 = addFile(self.root2, "empty.c", self.user2, time, True)
    
    def test_file_view_file_no_data(self):
        url = reverse('fileInfo')
        data = {}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_file_view_file_not_found(self):
        url = reverse('fileInfo')
        data = {'file_id': 999}  # ID, które nie istnieje w bazie danych

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_file_view_file_owner_not_user(self):
        url = reverse('fileInfo')
        data = {'file_id': self.emptyFile2.pk}  # ID, które należy do innego użytkownika

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_file_view_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('fileInfo')
        data = {'file_id': self.readme.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/file')
    
    def test_file_view_authenticated_owner(self):
        url = reverse('fileInfo')
        self.client.login(username='testuser', password='testpass')

        # README - jest zawartość
        data = {'file_id': self.readme.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.readme.pk))
        self.assertEqual(response.json()['description'], str(self.readme.description))
        self.assertEqual(response.json()['content'], str("hello \n how \n are \n u"))

        # empty.c - brak zawartości
        data = {'file_id': self.emptyFile.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.emptyFile.pk))
        self.assertEqual(response.json()['description'], str(self.emptyFile.description))
        self.assertEqual(response.json()['content'], "")

class SaveFileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.emptyFile = addFile(self.root, "empty.c", self.user, time, True)
        self.readme = addFile(self.root, "README", self.user, time, True)
        
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.emptyFile2 = addFile(self.root2, "empty.c", self.user2, time, True)
    
    def test_save_file_file_no_data(self):
        url = reverse('saveFile')
        data = {}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'file_id': self.readme.pk} # Nie ma content

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_save_file_file_not_found(self):
        url = reverse('saveFile')
        data = {'file_id': 999, 'content': ""}  # ID, które nie istnieje w bazie danych

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_save_file_file_owner_not_user(self):
        url = reverse('saveFile')
        data = {'file_id': self.emptyFile2.pk, 'content': ""}  # ID, które należy do innego użytkownika

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_save_file_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('saveFile')
        data = {'file_id': self.readme.pk, 'content': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/save/file')
    
    def test_save_file_authenticated_owner(self):
        url = reverse('saveFile')
        self.client.login(username='testuser', password='testpass')

        # README - jest zawartość
        data = {'file_id': self.readme.pk, 'content': "hello\n here\n I\n am"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.readme.pk))
        try:
          file = File.objects.get(pk=self.readme.pk)
        except File.DoesNotExist:
          file = None
        self.assertIsNotNone(file, "readme should still exists!")
        s = ""
        for code in file.codesection_set.all():
          s += code.content
        self.assertEqual(s, "hello\n here\n I\n am")

        # # empty.c - brak zawartości
        data = {'file_id': self.emptyFile.pk, 'content': "hello\n here\n I\n am"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.emptyFile.pk))
        try:
          file = File.objects.get(pk=self.emptyFile.pk)
        except File.DoesNotExist:
          file = None
        self.assertIsNotNone(file, "readme should still exists!")
        s = ""
        for code in file.codesection_set.all():
          s += code.content
        self.assertEqual(s, "hello\n here\n I\n am")


class DeleteFolderViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.backend = addFolder(self.root, 'backend', self.user, time, True)
        self.src = addFolder(self.backend, 'src', self.user, time, True)
        self.readme = addFile(self.src, "README", self.user, time, True)
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.backend2 = addFolder(self.root2, 'backend', self.user2, time, True)
        self.emptyFile2 = addFile(self.backend2, "empty.c", self.user2, time, True)
    
    def test_delete_folder_root_attempt(self):
        url = reverse('deleteFolder')
        data = {'folder_id': self.root.pk}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_delete_folder_folder_no_data(self):
        url = reverse('deleteFolder')
        data = {}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_delete_folder_folder_not_found(self):
        url = reverse('deleteFolder')
        data = {'folder_id': 999}  # ID, które nie istnieje w bazie danych

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_delete_folder_folder_owner_not_user(self):
        url = reverse('deleteFolder')
        data = {'folder_id': self.backend2.pk}  # ID, które należy do innego użytkownika

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_delete_folder_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('deleteFolder')
        data = {'folder_id': self.backend.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/delete/folder')
    
    def test_delete_folder_authenticated_owner(self):
        url = reverse('deleteFolder')
        self.client.login(username='testuser', password='testpass')

        data = {'folder_id': self.backend.pk}
        time.sleep(5)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.backend.pk))

        self.root = Folder.objects.get(pk=self.root.pk)
        self.backend = Folder.objects.get(pk=self.backend.pk)
        self.src = Folder.objects.get(pk=self.src.pk)
        self.readme = File.objects.get(pk=self.readme.pk)

        self.assertEqual(self.backend.availability, False)
        self.assertEqual(self.src.availability, False)
        self.assertEqual(self.readme.availability, False)
        duration = self.root.content_change_date - self.backend.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True) # Root ma zmienione content_change_date, ale backend już nie
        duration = self.backend.availability_change_date - self.backend.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.readme.availability_change_date - self.backend.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.src.availability_change_date - self.backend.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)

class DeleteFileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.backend = addFolder(self.root, 'backend', self.user, time, True)
        self.src = addFolder(self.backend, 'src', self.user, time, True)
        self.readme = addFile(self.src, "README", self.user, time, True)
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.backend2 = addFolder(self.root2, 'backend', self.user2, time, True)
        self.emptyFile2 = addFile(self.backend2, "empty.c", self.user2, time, True)
    
    def test_delete_file_file_no_data(self):
        url = reverse('deleteFile')
        data = {}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_delete_file_file_not_found(self):
        url = reverse('deleteFile')
        data = {'file_id': 999}  # ID, które nie istnieje w bazie danych

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_delete_file_file_owner_not_user(self):
        url = reverse('deleteFile')
        data = {'file_id': self.emptyFile2.pk}  # ID, które należy do innego użytkownika

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_delete_file_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('deleteFile')
        data = {'file_id': self.backend.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/delete/file')
    
    def test_delete_file_authenticated_owner(self):
        url = reverse('deleteFile')
        self.client.login(username='testuser', password='testpass')

        data = {'file_id': self.readme.pk}
        time.sleep(5)
        time_before = self.readme.pub_date
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.readme.pk))

        self.root = Folder.objects.get(pk=self.root.pk)
        self.backend = Folder.objects.get(pk=self.backend.pk)
        self.src = Folder.objects.get(pk=self.src.pk)
        self.readme = File.objects.get(pk=self.readme.pk)

        self.assertEqual(self.readme.availability, False)
        duration = self.root.content_change_date - time_before
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True) # Root ma zmienione content_change_date, ale backend już nie
        duration = self.backend.content_change_date - time_before
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.src.content_change_date - time_before
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.readme.availability_change_date - time_before
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)

class postFolderFormViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.backend = addFolder(self.root, 'backend', self.user, time, True)
        self.src = addFolder(self.backend, 'src', self.user, time, True)
        self.readme = addFile(self.src, "README", self.user, time, True)
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.backend2 = addFolder(self.root2, 'backend', self.user2, time, True)
        self.emptyFile2 = addFile(self.backend2, "empty.c", self.user2, time, True)
    
    def test_insert_folder_folder_no_data(self):
        url = reverse('postFolderForm')

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'pk': self.backend.pk, 'name': "temp"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'pk': self.backend.pk, 'description': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'name': 'temp', 'description': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_insert_folder_folder_not_found(self):
        url = reverse('postFolderForm')
        data = {'pk': 999, 'name': 'temp', 'description': "cos"}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_insert_folder_folder_owner_not_user(self):
        url = reverse('postFolderForm')
        data = {'pk': self.backend2.pk, 'name': 'temp', 'description': "cos"}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_insert_folder_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('postFolderForm')
        data = {'pk': self.backend.pk, 'name': 'temp', 'description': "cos"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/postFolderForm')
    
    def test_insert_folder_authenticated_owner(self):
        url = reverse('postFolderForm')
        self.client.login(username='testuser', password='testpass')

        data = {'pk': self.backend.pk, 'name': 'temp', 'description': "cos"}
        time.sleep(5)
        time_before = self.readme.pub_date
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.backend.pk))
        self.assertIsNotNone(response.json()['new_id'], "New_id must be in response!")
        self.assertEqual(response.json()['name'], 'temp')

        self.root = Folder.objects.get(pk=self.root.pk)
        self.backend = Folder.objects.get(pk=self.backend.pk)
        self.src = Folder.objects.get(pk=self.src.pk)
        self.temp = Folder.objects.get(pk=int(response.json()['new_id']))

        self.assertEqual(self.temp.name, 'temp')
        self.assertEqual(self.temp.description, 'cos')
        self.assertEqual(self.temp.up.pk, self.backend.pk)
        self.assertEqual(self.temp.owner, self.user)
        self.assertEqual(self.temp.availability, True)
        duration = self.root.content_change_date - self.root.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.backend.content_change_date - self.backend.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = duration = self.src.content_change_date - self.src.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)
        duration = self.root.content_change_date - self.temp.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)
        duration = self.root.content_change_date - self.temp.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)

class postFileFormViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.backend = addFolder(self.root, 'backend', self.user, time, True)
        self.src = addFolder(self.backend, 'src', self.user, time, True)
        self.readme = addFile(self.src, "README", self.user, time, True)
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how \n are \n u"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.readme,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.backend2 = addFolder(self.root2, 'backend', self.user2, time, True)
        self.emptyFile2 = addFile(self.backend2, "empty.c", self.user2, time, True)
    
    def test_insert_file_no_data(self):
        url = reverse('postFileForm')

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'pk': self.backend.pk, 'name': "temp"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'pk': self.backend.pk, 'description': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        data = {'name': 'temp', 'description': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_insert_file_file_not_found(self):
        url = reverse('postFileForm')
        data = {'pk': 999, 'name': 'temp', 'description': "cos"}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_insert_file_file_owner_not_user(self):
        url = reverse('postFileForm')
        data = {'pk': self.backend2.pk, 'name': 'temp', 'description': "cos"}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_insert_file_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('postFileForm')
        data = {'pk': self.backend.pk, 'name': 'temp', 'description': "cos"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/postFileForm')
    
    def test_insert_file_authenticated_owner(self):
        url = reverse('postFileForm')
        self.client.login(username='testuser', password='testpass')

        data = {'pk': self.backend.pk, 'name': 'temp', 'description': "cos"}
        time.sleep(5)
        time_before = self.readme.pub_date
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['pk'], str(self.backend.pk))
        self.assertIsNotNone(response.json()['new_id'], "New_id must be in response!")
        self.assertEqual(response.json()['name'], 'temp')

        self.root = Folder.objects.get(pk=self.root.pk)
        self.backend = Folder.objects.get(pk=self.backend.pk)
        self.src = Folder.objects.get(pk=self.src.pk)
        self.temp = File.objects.get(pk=int(response.json()['new_id']))

        self.assertEqual(self.temp.name, 'temp')
        self.assertEqual(self.temp.description, 'cos')
        self.assertEqual(self.temp.up.pk, self.backend.pk)
        self.assertEqual(self.temp.owner, self.user)
        self.assertEqual(self.temp.availability, True)
        duration = self.root.content_change_date - self.root.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = self.backend.content_change_date - self.backend.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s >= 5, True)
        duration = duration = self.src.content_change_date - self.src.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)
        duration = self.root.content_change_date - self.temp.availability_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)
        duration = self.root.content_change_date - self.temp.content_change_date
        duration_in_s = duration.total_seconds()
        self.assertEqual(duration_in_s, 0)

class CompileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.user.first_name = 'testname'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        naive_time = datetime.datetime.now()
        time = make_aware(naive_time)

        self.root = addFolder(None, 'root', self.user, time, True)
        self.backend = addFolder(self.root, 'backend', self.user, time, True)
        self.src = addFolder(self.backend, 'src', self.user, time, True)
        self.test = addFile(self.src, "test.c", self.user, time, True)
        self.sk = SectionKind(type = "Procedure",)
        self.sk.save()
        self.s = Status(name = "Unknown",)
        self.s.save()
        self.sd = StatusData(data = "Unknown",)
        self.sd.save()
        content = "hello \n how"
        self.code_section = CodeSection(
          name = 'codesection',
          file = self.test,
          pub_date = time,
          begin = 1,
          end = content.count('\n') + content.count('\r\n') + 1,
          kind = self.sk,
          status = self.s,
          statusData = self.sd,
          content = content,
        )
        self.code_section.save()

        # Plik nienależący do właściciela:
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )
        self.user2.first_name = 'testname2'
        self.user2.save()

        self.root2 = addFolder(None, 'root', self.user2, time, True)
        self.backend2 = addFolder(self.root2, 'backend', self.user2, time, True)
        self.emptyFile2 = addFile(self.backend2, "empty.c", self.user2, time, True)
    
    def test_compile_no_data(self):
        url = reverse('compileFile')

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_compile_file_not_found(self):
        url = reverse('compileFile')
        data = {'pk': 999}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_compile_file_owner_not_user(self):
        url = reverse('compileFile')
        data = {'pk': self.emptyFile2.pk}

        # Uwierzytelnienie użytkownika przed wykonaniem żądania
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_compile_not_authenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('compileFile')
        data = {'pk': self.test.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/app/compile')
    
    def test_compile_authenticated_owner(self):
        url = reverse('compileFile')
        self.client.login(username='testuser', password='testpass')

        data = {'pk': self.test.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'compiled')
        self.assertEqual(response.json()['return'], 1)
        self.assertEqual(response.json()['assm'], "test.c:2: syntax error: token -> 'how' ; column 4\n")

class SignUpViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_signup_get_method(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
    
    def test_signup_post_not_proper_data(self):
        url = reverse('signup')

        form = {}
        response = self.client.post(url, form)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')

    def test_signup_post_proper_data(self):
        url = reverse('signup')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpassword',
            'password2': 'testpassword',
            'name': 'Test User',
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        folders = Folder.objects.all()
        self.assertEqual(folders.count(), 1)
        root = folders[0]
        self.assertIsNone(root.up, "Root should not be subfolder!")
        self.assertEqual(str(root), "root testuser")
        # https://stackoverflow.com/questions/9571624/how-do-i-get-the-password-in-django - password is hashed.
        self.assertEqual(root.owner.first_name, 'Test User')

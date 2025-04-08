from django.db import models
from django.contrib.auth.models import User
from datetime import date

# class Users(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     # name = models.CharField(max_length=40)
#     mob = models.IntegerField(null=True)

class Folder(models.Model):
    up = models.ForeignKey('self', on_delete = models.CASCADE, blank = True, null = True, default = None)
    name = models.CharField(max_length = 255)
    description = models.CharField(max_length = 255, blank = True, default = '')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    availability = models.BooleanField(blank = True, default = True)
    availability_change_date = models.DateTimeField('availability change date')
    content_change_date = models.DateTimeField('content change date')
    def __str__(self):
        return self.name + " " + self.owner.username

class File(models.Model):
    up = models.ForeignKey(Folder, on_delete = models.CASCADE)
    name = models.CharField(max_length = 255)
    description = models.CharField(max_length = 255, blank = True, default = '')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    availability = models.BooleanField(blank = True, default = True)
    availability_change_date = models.DateTimeField('availability change date')
    content_change_date = models.DateTimeField('content change date')
    def __str__(self):
        return self.name + " " + self.owner.username

# In future may be developed
class StatusData(models.Model):
    data = models.CharField(max_length = 255)
    def __str__(self):
        return self.data

class Status(models.Model):
    name = models.CharField(max_length = 255)
    def __str__(self):
        return self.name

class SectionKind(models.Model):
    type = models.CharField(max_length = 255)
    def __str__(self):
        return self.type

class CodeSection(models.Model):
    file = models.ForeignKey(File, on_delete = models.CASCADE)
    up = models.ForeignKey('self', on_delete = models.CASCADE, blank = True, null = True, default = None)
    name = models.CharField(max_length = 255, blank = True, default = '')
    description = models.CharField(max_length = 255, blank = True, default = '')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    begin = models.IntegerField()
    end = models.IntegerField()
    kind = models.ForeignKey(SectionKind, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    statusData = models.ForeignKey(StatusData, on_delete=models.CASCADE)
    content = models.CharField(max_length = 10000)
    def __str__(self):
        return self.name + " " + self.file.name



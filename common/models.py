from django.db import models



class BaseModel(models.Model):
    created_at = models.DateTimeField('Yaratilgan sana', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan sana', auto_now=True)

    class Meta:
        abstract = True



class Role(models.TextChoices):
    STUDENT = "student", "Talaba"
    MENTOR = "mentor", "Mentor"
    ADMIN = "admin", "Administrator"
    SUPPORT = "support", "Qo'llab-quvvatlash"
 
import re
from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Novice'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Expert'),
    ]

    title = models.CharField(max_length=255, verbose_name="Назва навички")
    slug = models.SlugField(unique=True, verbose_name="URL ідентифікатор")
    category = models.CharField(max_length=100, verbose_name="Категорія")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1, verbose_name="Складність")

    description = models.TextField(blank=True, verbose_name="Опис (Markdown)")
    video_url = models.URLField(blank=True, null=True, verbose_name="Посилання на відео (YouTube)")

    #Directed Graph
    dependencies = models.ManyToManyField(
        'self',
        through='SkillDependency',
        symmetrical=False,
        related_name='related_to'
    )

    def get_video_id(self):
        """
        Витягує ID відео за допомогою регулярних виразів.
        Це найнадійніший спосіб.
        """
        if not self.video_url:
            return None

        # Цей вираз шукає 11 символів (цифри, букви, -, _),
        # які йдуть після "v=", "embed/" або "youtu.be/"
        regex = r'(?:v=|/|embed/|youtu\.be/)([0-9A-Za-z_-]{11})'

        match = re.search(regex, self.video_url)

        if match:
            return match.group(1)  # Повертає чистий ID
        return None

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

    class Meta:
        verbose_name = "Навичка"
        verbose_name_plural = "Навички"
        ordering = ['category', 'difficulty', 'title']


class SkillDependency(models.Model):
    DEPENDENCY_TYPE = [
        ('hard', 'Обовʼязково'),
        ('soft', 'Бажано'),
    ]

    # from_skill
    from_skill = models.ForeignKey(Skill, related_name='required_by', on_delete=models.CASCADE)
    # to_skill
    to_skill = models.ForeignKey(Skill, related_name='requires', on_delete=models.CASCADE)

    dependency_type = models.CharField(max_length=10, choices=DEPENDENCY_TYPE, default='hard')

    class Meta:
        unique_together = ('from_skill', 'to_skill')
        verbose_name = "Залежність"
        verbose_name_plural = "Залежності"

    def __str__(self):
        return f"{self.from_skill.title} -> {self.to_skill.title}"


class UserSkillProgress(models.Model):
    STATUS_CHOICES = [
        ('todo', 'Треба вивчити'),
        ('in_progress', 'В процесі'),
        ('done', 'Завершено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_progress')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'skill')
        verbose_name = "Прогрес користувача"
        verbose_name_plural = "Прогрес користувачів"
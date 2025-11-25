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
    slug = models.SlugField(unique=True, max_length=255, verbose_name="URL ідентифікатор")
    category = models.CharField(max_length=100, verbose_name="Категорія")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1, verbose_name="Складність")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills', null=True)

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
        if not self.video_url:
            return None

        regex = r'(?:v=|/|embed/|youtu\.be/)([0-9A-Za-z_-]{11})'

        match = re.search(regex, self.video_url)

        if match:
            return match.group(1)
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

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    avatar = models.ImageField(default='default.jpg', upload_to='profile_avatars', blank=True, verbose_name='Аватар')
    bio = models.TextField(max_length=500, blank=True, verbose_name='Про мене')

    is_public = models.BooleanField(default=True, verbose_name="Показувати в рейтингу")
    dark_mode = models.BooleanField(default=False, verbose_name="Темна тема")

    github_link = models.URLField(max_length=200, blank=True, verbose_name='GitHub')
    linkedin_link = models.URLField(max_length=200, blank=True, verbose_name='LinkedIn')
    website_link = models.URLField(max_length=200, blank=True, verbose_name='Вебсайт')

    def __str__(self):
        return f'{self.user.username} Profile'

class Feedback(models.Model):
    CATEGORY_CHOICES = [
        ('bug', '🐛 Помилка / Баг'),
        ('feature', '💡 Ідея / Пропозиція'),
        ('other', '📝 Інше'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="Категорія")
    subject = models.CharField(max_length=200, verbose_name="Тема")
    message = models.TextField(verbose_name="Повідомлення")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    is_resolved = models.BooleanField(default=False, verbose_name="Вирішено")

    def __str__(self):
        return f"[{self.get_category_display()}] {self.subject} ({self.user.username})"

    class Meta:
        verbose_name = "Зворотний зв'язок"
        verbose_name_plural = "Зворотний зв'язок"
        ordering = ['-created_at']
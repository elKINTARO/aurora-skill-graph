from django import forms
from .models import Skill, SkillDependency

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['title', 'category', 'difficulty', 'video_url', 'description']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наприклад: Вивчити Docker'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DevOps'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Можна використовувати Markdown'}),
        }

class DependencyForm(forms.ModelForm):
    class Meta:
        model = SkillDependency
        fields = ['from_skill', 'dependency_type']
        labels = {
            'from_skill': 'Необхідна навичка',
            'dependency_type': 'Тип залежності'
        }
        widgets = {
            'from_skill': forms.Select(attrs={'class': 'form-select'}),
            'dependency_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, user, current_skill, *args, **kwargs):
        super().__init__(*args, **kwargs)

        already_linked = current_skill.requires.values_list('from_skill_id', flat=True)

        self.fields['from_skill'].queryset = Skill.objects.filter(
            author=user
        ).exclude(
            id=current_skill.id
        ).exclude(
            id__in=already_linked
        )
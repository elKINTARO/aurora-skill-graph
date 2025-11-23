from django.shortcuts import render
from .models import Skill

def skill_list(request):
    skills = Skill.objects.prefetch_related(
        'requires__from_skill',
        'required_by__to_skill',
    ).all()

    return render(request, 'skills/skill_list.html', {'skills': skills}

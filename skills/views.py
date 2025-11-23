from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Skill, UserSkillProgress

def skill_list(request):
    skills = Skill.objects.prefetch_related(
        'requires__from_skill',
        'required_by__to_skill',
    ).all()

    if request.user.is_authenticated:
        user_progress = {
            p.skill_id: p.status
            for p in UserSkillProgress.objects.filter(user=request.user)
        }

        for skill in skills:
            skill.my_status = user_progress.get(skill.id, 'todo')

    return render(request, 'skills/skill_list.html', {'skills': skills})

@login_required
def change_status(request, skill_slug, new_status):
    skill = get_object_or_404(Skill, slug=skill_slug)

    progress, created = UserSkillProgress.objects.get_or_create(
        user=request.user,
        skill=skill
    )

    progress.status = new_status
    progress.save()

    return redirect('skill_list')

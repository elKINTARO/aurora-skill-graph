from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Skill, UserSkillProgress

def skill_list(request):
    skills = Skill.objects.prefetch_related(
        'requires__from_skill',
        'required_by__to_skill'
    ).order_by('category', 'difficulty', 'title').all()

    if request.user.is_authenticated:
        user_progress_qs = UserSkillProgress.objects.filter(user=request.user)

        user_progress_map = {
            p.skill_id: p.status
            for p in user_progress_qs
        }

        completed_ids = {
            p.skill_id
            for p in user_progress_qs
            if p.status == 'done'
        }

        for skill in skills:
            skill.my_status = user_progress_map.get(skill.id, 'todo')

            skill.is_locked = False

            for req in skill.requires.all():
                if req.from_skill.id in completed_ids:
                    req.is_met = True
                else:
                    req.is_met = False

                if req.dependency_type == 'hard' and not req.is_met:
                    skill.is_locked = True

    else:
        pass

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

def skill_detail(request, skill_slug):
    skill = get_object_or_404(Skill, slug=skill_slug)
    if request.user.is_authenticated:
        try:
            progress = UserSkillProgress.objects.get(user=request.user, skill=skill)
            skill.my_status = progress.status
        except UserSkillProgress.DoesNotExist:
            skill.my_status = 'todo'

        if skill.my_status == 'todo':
            skill.is_locked = False
            for req in skill.requires.all():
                if req.dependency_type == 'hard':
                    is_parent_done = UserSkillProgress.objects.filter(
                        user=request.user,
                        skill=req.from_skill,
                        status='done'
                    ).exists()

                    if not is_parent_done:
                        skill.is_locked = True
                        break

    return render(request, 'skills/skill_detail.html', {'skill': skill})

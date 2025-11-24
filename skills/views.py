from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Skill, UserSkillProgress, SkillDependency
from django.views.decorators.cache import never_cache
from django.utils.text import slugify
from .forms import SkillForm, DependencyForm



@login_required
def user_profile(request):
    user_progress = UserSkillProgress.objects.filter(user=request.user).select_related('skill')
    in_progress_skills = user_progress.filter(status='in_progress')
    finished_skills = user_progress.filter(status='done')
    total_xp = finished_skills.aggregate(
        total_points=Sum(F('skill__difficulty') * 10)
    )['total_points'] or 0

    context = {
        'in_progress': in_progress_skills,
        'finished_count': finished_skills.count(),
        'total_xp': total_xp,
    }

    return render(request, 'skills/profile.html', context)

@login_required
@never_cache
def skill_list(request):
    skills = Skill.objects.filter(author=request.user).prefetch_related(
        'requires__from_skill',
        'required_by__to_skill'
    ).order_by('category', 'difficulty', 'title')

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

@never_cache
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


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('skill_list')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def skill_create(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.author = request.user
            base_slug = slugify(skill.title)
            skill.slug = f"{base_slug}-{request.user.id}-{Skill.objects.count()}"
            skill.save()

            return redirect('skill_list')
    else:
        form = SkillForm()

    return render(request, 'skills/skill_form.html', {'form': form})


@login_required
def skill_edit(request, skill_slug):
    skill = get_object_or_404(Skill, slug=skill_slug, author=request.user)
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect('skill_detail', skill_slug=skill.slug)
    else:
        form = SkillForm(instance=skill)

    return render(request, 'skills/skill_form.html', {
        'form': form,
        'is_edit': True,
        'skill': skill
    })

@login_required
def skill_delete(request, skill_slug):
    skill = get_object_or_404(Skill, slug=skill_slug, author=request.user)

    if request.method == 'POST':
        skill.delete()
        return redirect('skill_list')

    return render(request, 'skills/skill_confirm_delete.html', {'skill': skill})


@login_required
def skill_add_dependency(request, skill_slug):
    current_skill = get_object_or_404(Skill, slug=skill_slug, author=request.user)

    if request.method == 'POST':
        form = DependencyForm(request.user, current_skill, request.POST)
        if form.is_valid():
            dependency = form.save(commit=False)
            dependency.to_skill = current_skill
            dependency.save()
            return redirect('skill_detail', skill_slug=current_skill.slug)
    else:
        form = DependencyForm(request.user, current_skill)

    return render(request, 'skills/skill_add_dependency.html', {
        'form': form,
        'skill': current_skill
    })


@login_required
def skill_remove_dependency(request, skill_slug, dependency_id):
    current_skill = get_object_or_404(Skill, slug=skill_slug, author=request.user)

    dependency = get_object_or_404(SkillDependency, id=dependency_id, to_skill=current_skill)

    if request.method == 'POST':
        dependency.delete()

    return redirect('skill_detail', skill_slug=current_skill.slug)

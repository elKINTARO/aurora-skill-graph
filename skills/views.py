from django.db.models import Q
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Skill, UserSkillProgress, SkillDependency
from django.views.decorators.cache import never_cache
from .forms import SkillForm, DependencyForm
from .gamification import get_rank_info
from django.contrib.auth.models import User
from django.db.models import Case, When, IntegerField
from .forms import UserUpdateForm, ProfileUpdateForm
from .ai_service import generate_roadmap
from django.utils.text import slugify
from youtubesearchpython import VideosSearch
import uuid
import time

@login_required
def user_profile(request):
    user_progress = UserSkillProgress.objects.filter(user=request.user).select_related('skill')
    in_progress_skills = user_progress.filter(status='in_progress')
    finished_skills = user_progress.filter(status='done')

    total_xp = finished_skills.aggregate(
        total_points=Sum(F('skill__difficulty') * 10)
    )['total_points'] or 0

    rank_data = get_rank_info(total_xp)

    context = {
        'in_progress': in_progress_skills,
        'finished_count': finished_skills.count(),
        'total_xp': total_xp,
        'rank': rank_data,
    }

    return render(request, 'skills/profile.html', context)

@never_cache
@login_required
def skill_list(request):
    skills = Skill.objects.filter(author=request.user).prefetch_related(
        'requires__from_skill',
        'required_by__to_skill'
    ).order_by('category', 'difficulty', 'title')

    categories = Skill.objects.filter(author=request.user).values_list('category', flat=True).distinct()

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    if search_query:
        skills = skills.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter:
        skills = skills.filter(category=category_filter)

    user_progress_qs = UserSkillProgress.objects.filter(user=request.user)
    user_progress_map = {p.skill_id: p.status for p in user_progress_qs}
    completed_ids = {p.skill_id for p in user_progress_qs if p.status == 'done'}

    for skill in skills:
        skill.my_status = user_progress_map.get(skill.id, 'todo')
        skill.is_locked = False
        for req in skill.requires.all():
            if req.dependency_type == 'hard':
                if req.from_skill.id in completed_ids:
                    req.is_met = True
                else:
                    req.is_met = False
                    skill.is_locked = True

    context = {
        'skills': skills,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }

    return render(request, 'skills/skill_list.html', context)

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
@login_required
def skill_detail(request, skill_slug):
    skill = get_object_or_404(Skill, slug=skill_slug, author=request.user)

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

    mermaid_graph = ["graph TD"]

    mermaid_graph.append("classDef done fill:#d1e7dd,stroke:#0f5132,stroke-width:2px;")
    mermaid_graph.append("classDef in_progress fill:#fff3cd,stroke:#856404,stroke-width:2px;")
    mermaid_graph.append("classDef todo fill:#f8f9fa,stroke:#6c757d,stroke-width:1px,stroke-dasharray: 5 5;")
    mermaid_graph.append("classDef locked fill:#e9ecef,stroke:#adb5bd,stroke-width:1px;")
    mermaid_graph.append("classDef current fill:#cfe2ff,stroke:#0d6efd,stroke-width:4px;")

    for req in skill.requires.all():
        parent = req.from_skill
        try:
            p_status = UserSkillProgress.objects.get(user=request.user, skill=parent).status
        except UserSkillProgress.DoesNotExist:
            p_status = 'todo'

        mermaid_graph.append(f'N{parent.id}["{parent.title}"] --> N{skill.id}')

        mermaid_graph.append(f'class N{parent.id} {p_status};')

        mermaid_graph.append(f'click N{parent.id} "/skill/{parent.slug}/"')

    mermaid_graph.append(f'N{skill.id}["{skill.title}"]')
    mermaid_graph.append(f'class N{skill.id} current;')

    for req in skill.required_by.all():
        child = req.to_skill
        try:
            c_status = UserSkillProgress.objects.get(user=request.user, skill=child).status
        except UserSkillProgress.DoesNotExist:
            c_status = 'todo'

        mermaid_graph.append(f'N{skill.id} --> N{child.id}["{child.title}"]')

        mermaid_graph.append(f'class N{child.id} {c_status};')
        mermaid_graph.append(f'click N{child.id} "/skill/{child.slug}/"')

    mermaid_string = "\n".join(mermaid_graph)

    return render(request, 'skills/skill_detail.html', {
        'skill': skill,
        'mermaid_graph': mermaid_string
    })

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

@login_required
def leaderboard(request):
    users = User.objects.annotate(
        total_xp=Sum(
            Case(
                When(skill_progress__status='done', then=F('skill_progress__skill__difficulty') * 10),
                default=0,
                output_field=IntegerField()
            )
        )
    ).order_by('-total_xp')

    leaderboard_data = []
    for user in users:
        xp = user.total_xp or 0
        rank_info = get_rank_info(xp)
        leaderboard_data.append({
            'user': user,
            'xp': xp,
            'rank': rank_info['current_rank']
        })

    return render(request, 'skills/leaderboard.html', {'leaders': leaderboard_data})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'skills/profile_edit.html', context)


@login_required
def ai_generator(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')

        data = generate_roadmap(topic)

        if data:
            created_skills = []
            created_skills_map = {}
            for item in data.get('skills', []):
                safe_title = item['title'][:50]
                base_slug = slugify(safe_title)
                unique_slug = f"{base_slug}-{request.user.id}-{uuid.uuid4().hex[:6]}"

                ai_category = f"🤖 AI: {topic}"

                skill = Skill.objects.create(
                    title=item['title'],
                    category=ai_category,
                    difficulty=item['difficulty'],
                    description=item['description'],
                    video_url="",  # Пусто
                    author=request.user,
                    slug=unique_slug
                )
                created_skills_map[item['title']] = skill
                created_skills.append(skill)

            mermaid_graph = ["graph TD"]
            mermaid_graph.append("classDef default fill:#e3f2fd,stroke:#0d6efd,stroke-width:2px;")

            for dep in data.get('dependencies', []):
                parent = created_skills_map.get(dep['from'])
                child = created_skills_map.get(dep['to'])

                if parent and child:
                    SkillDependency.objects.create(
                        from_skill=parent,
                        to_skill=child,
                        dependency_type=dep['type']
                    )
                    mermaid_graph.append(f'N{parent.id}["{parent.title}"] --> N{child.id}["{child.title}"]')

            if len(mermaid_graph) == 2:
                for s in created_skills:
                    mermaid_graph.append(f'N{s.id}["{s.title}"]')

            mermaid_string = "\n".join(mermaid_graph)

            return render(request, 'skills/ai_success.html', {
                'topic': topic,
                'skills_count': len(created_skills),
                'mermaid_graph': mermaid_string
            })

        else:
            error = "AI не зміг згенерувати план. Спробуйте спростити тему (наприклад 'Python Basics')."
            return render(request, 'skills/ai_generator.html', {'error': error})

    return render(request, 'skills/ai_generator.html')
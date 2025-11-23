from django.contrib import admin
from .models import Skill, SkillDependency, UserSkillProgress

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'slug')
    list_filter = ('difficulty', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(SkillDependency)
class SkillDependencyAdmin(admin.ModelAdmin):
    list_display = ('from_skill', 'to_skill', 'dependency_type')
    list_filter = ('dependency_type',)

@admin.register(UserSkillProgress)
class UserSkillProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'status')
    list_filter = ('status', 'user')

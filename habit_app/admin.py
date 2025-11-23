from django.contrib import admin
from .models import Category, Habit, HabitCheckin


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    readonly_fields = ("owner",)
    list_display = ("id", "name", "owner", "status", "start_date", "created_at")
    list_filter = ("status", "start_date")
    search_fields = ("name", "owner__username")

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        obj.save()


@admin.register(HabitCheckin)
class HabitCheckinAdmin(admin.ModelAdmin):
    list_display = ("id", "habit", "date", "created_at")
    list_filter = ("date",)
    search_fields = ("habit__name",)

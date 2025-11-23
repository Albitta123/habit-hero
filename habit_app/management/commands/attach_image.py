from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings
from habit_app.models import Habit
import os


class Command(BaseCommand):
    help = 'Attach an image from MEDIA_ROOT/habit_photos to a Habit.photo field.'

    def add_arguments(self, parser):
        parser.add_argument('--habit-id', type=int, help='ID of the habit to attach the image to')
        parser.add_argument('--name', type=str, help='Name of the habit to attach the image to')
        parser.add_argument('--filename', type=str, required=True, help='Filename in MEDIA_ROOT/habit_photos to attach')

    def handle(self, *args, **options):
        filename = options['filename']
        habit_id = options.get('habit_id')
        name = options.get('name')

        media_path = os.path.join(settings.MEDIA_ROOT, 'habit_photos', filename)
        if not os.path.exists(media_path):
            raise CommandError(f'File not found: {media_path}')

        if habit_id:
            qs = Habit.objects.filter(id=habit_id)
        elif name:
            qs = Habit.objects.filter(name=name)
        else:
            qs = Habit.objects.filter(photo__isnull=True) | Habit.objects.filter(photo__exact='')

        if not qs.exists():
            raise CommandError('No matching Habit found for the given criteria.')

        for habit in qs:
            with open(media_path, 'rb') as f:
                django_file = File(f)
                habit.photo.save(filename, django_file, save=True)
                self.stdout.write(self.style.SUCCESS(f'Attached "{filename}" to Habit (id={habit.id}, name="{habit.name}")'))

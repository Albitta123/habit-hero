from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class Category(models.Model):
    """A simple category for habits (e.g., Health, Work, Learning)."""
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Habit(models.Model):
    FREQUENCY_DAILY = 'daily'
    FREQUENCY_WEEKLY = 'weekly'
    FREQUENCY_MONTHLY = 'monthly'
    FREQUENCY_CHOICES = [
        (FREQUENCY_DAILY, 'Daily'),
        (FREQUENCY_WEEKLY, 'Weekly'),
        (FREQUENCY_MONTHLY, 'Monthly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=200)

    # OWNER - auto assigned, not editable in admin
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    start_date = models.DateField(default=timezone.localdate)

    # Target values for measurable habits (alphanumeric allowed)
    target_value = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Target value (alphanumeric OK), e.g. '3 liters', '20 pages'"
    )

    # Habit status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Optional habit photo
    photo = models.ImageField(
        upload_to="habit_photos/",
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def _checkin_dates_set(self):
        qs = self.checkins.all().values_list('date', flat=True)
        return set([d for d in qs])

    def checkin(self, date=None, note=''):
        if date is None:
            date = timezone.localdate()
        obj, created = HabitCheckin.objects.get_or_create(habit=self, date=date, defaults={'note': note})
        if not created and note:
            obj.note = note
            obj.save(update_fields=['note'])
        return obj, created

    # Helper: map a date to the start of the period depending on frequency
    def _period_start(self, d):
        freq = getattr(self, 'frequency', self.FREQUENCY_DAILY)
        if freq == self.FREQUENCY_DAILY:
            return d
        if freq == self.FREQUENCY_WEEKLY:
            return d - datetime.timedelta(days=d.weekday())
        # monthly
        return datetime.date(d.year, d.month, 1)

    # Helper: add `n` periods to a period-start date
    def _period_add(self, d, n=1):
        freq = getattr(self, 'frequency', self.FREQUENCY_DAILY)
        if freq == self.FREQUENCY_DAILY:
            return d + datetime.timedelta(days=n)
        if freq == self.FREQUENCY_WEEKLY:
            return d + datetime.timedelta(weeks=n)
        # monthly
        month = d.month - 1 + n
        year = d.year + month // 12
        month = month % 12 + 1
        return datetime.date(year, month, 1)

    def current_streak(self):
        dates = self._checkin_dates_set()
        if not dates:
            return 0

        today = timezone.localdate()
        start = self._period_start(today)
        periods = set(self._period_start(d) for d in dates)

        streak = 0
        p = start
        while p in periods:
            streak += 1
            p = self._period_add(p, -1)
        return streak

    def best_streak(self):
        dates = sorted(self._checkin_dates_set())
        if not dates:
            return 0

        periods = []
        for d in dates:
            ps = self._period_start(d)
            if not periods or periods[-1] != ps:
                periods.append(ps)

        best = 0
        current = 1
        for i in range(1, len(periods)):
            if periods[i] == self._period_add(periods[i - 1], 1):
                current += 1
            else:
                best = max(best, current)
                current = 1
        best = max(best, current)
        return best

    def success_rate(self):
        today = timezone.localdate()
        if self.start_date > today:
            return 0.0

        total_done = self.checkins.count()

        freq = getattr(self, 'frequency', self.FREQUENCY_DAILY)
        if freq == self.FREQUENCY_DAILY:
            total_expected = (today - self.start_date).days + 1
        elif freq == self.FREQUENCY_WEEKLY:
            total_expected = ((today - self.start_date).days // 7) + 1
        else:  # monthly
            total_expected = (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month) + 1

        if total_expected <= 0:
            return 0.0

        return round((total_done / total_expected) * 100.0, 2)

    def best_day_of_week(self):
        from collections import Counter
        qs = self.checkins.all().values_list('date', flat=True)
        if not qs:
            return None, 0
        weekdays = [d.weekday() for d in qs]
        cnt = Counter(weekdays)
        day, count = cnt.most_common(1)[0]
        return day, count


class HabitCheckin(models.Model):
    habit = models.ForeignKey(
        Habit,
        related_name='checkins',
        on_delete=models.CASCADE
    )
    date = models.DateField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} @ {self.date.isoformat()}"

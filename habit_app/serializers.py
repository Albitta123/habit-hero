from rest_framework import serializers
from django.utils import timezone
from .models import Category, Habit, HabitCheckin

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class HabitSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # Nested category serializer to get full details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',  # maps to model field 'category'
        write_only=True
    )
    owner = serializers.ReadOnlyField(source='owner.username')
    name = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    target_value = serializers.CharField(required=True, allow_blank=False)
    status = serializers.ChoiceField(choices=Habit.STATUS_CHOICES, required=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = Habit
        fields = [
            'id', 'name', 'owner', 'category', 'category_id', 'start_date',
            'target_value', 'status', 'photo', 'notes', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at', 'category']

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError('Name is required.')
        if value[0].isspace():
            raise serializers.ValidationError('Name must not start with a space.')
        if not all(c.isalpha() or c.isspace() for c in value):
            raise serializers.ValidationError('Name must contain only alphabetic characters and spaces.')
        letter_count = sum(1 for c in value if c.isalpha())
        if letter_count < 3:
            raise serializers.ValidationError('Name must contain at least 3 letters.')
        return value.strip()

    def validate_start_date(self, value):
        today = timezone.localdate()
        if value < today:
            raise serializers.ValidationError('Start date cannot be in the past.')
        return value

    def validate_target_value(self, value):
        if value is None:
            raise serializers.ValidationError('Target value is required.')
        if isinstance(value, str):
            if not value.strip():
                raise serializers.ValidationError('Target value must not be empty.')
            return value.strip()
        return str(value)

    def create(self, validated_data):
        # Remove nested category and assign it correctly
        category = validated_data.pop('category', None)
        instance = super().create(validated_data)
        if category:
            instance.category = category
            instance.save()
        return instance

    def update(self, instance, validated_data):
        category = validated_data.pop('category', None)
        if category:
            instance.category = category
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


from rest_framework import serializers
from django.utils import timezone
from .models import HabitCheckin, Habit

class HabitCheckinSerializer(serializers.ModelSerializer):
    habit_id = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.all(),
        source='habit',
        write_only=True
    )
    habit_name = serializers.CharField(source='habit.name', read_only=True)  # habit name read-only

    class Meta:
        model = HabitCheckin
        fields = ['id', 'habit_id', 'habit_name', 'date', 'note', 'created_at']
        read_only_fields = ['created_at', 'habit_name', 'habit_id', 'date']  # Make habit_id and date read-only on update

    def validate_date(self, value):
        today = timezone.localdate()
        if value != today:
            raise serializers.ValidationError("Check-in date must be today's date.")
        return value

    def validate_habit(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if value.owner != request.user:
                raise serializers.ValidationError("You may only add check-ins for your own habits.")
        else:
            raise serializers.ValidationError("Authentication required.")
        return value

    def update(self, instance, validated_data):
        # Allow only 'note' to be updated
        note = validated_data.get('note', instance.note)
        instance.note = note
        instance.save()
        return instance
import django_filters

from apps.availability.models import Parish, Minister

class ParishFilter(django_filters.FilterSet):
    class Meta:
        model = Parish
        fields = {
            'city': ['exact', 'icontains'],
            'is_active': ['exact'],
        }

class MinisterFilter(django_filters.FilterSet):
    class Meta:
        model = Minister
        fields = {
            'role': ['exact'],
            'parish__slug': ['exact'],
            'is_active': ['exact'],
        }

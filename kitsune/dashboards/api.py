import django_filters
from rest_framework import generics
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer

from kitsune.dashboards.models import WikiMetric


class WikiMetricSerializer(ModelSerializer):
    product = SlugRelatedField(slug_field='slug')

    class Meta:
        model = WikiMetric
        fields = ('code', 'locale', 'product', 'date', 'value')


# Note: I hate that I had to create this class just to make
# product= act like product__slug=
# Is there a better way?
class ProductFilter(django_filters.Filter):
    """A custom filter to map 'product' to 'product__slug'."""
    def filter(self, qs, value):
        if value is None:
            return qs

        if value == '' or value == 'null':
            return qs.filter(product=None)

        return qs.filter(product__slug=value)


class WikiMetricFilterSet(django_filters.FilterSet):
    """A custom filter set for WikiMetrics for use by the API."""
    product = ProductFilter()

    class Meta:
        model = WikiMetric
        fields = ['code', 'locale', 'product']


class WikiMetricList(generics.ListAPIView):
    """The API list view for WikiMetrics."""
    queryset = WikiMetric.objects.all()
    serializer_class = WikiMetricSerializer
    filter_class = WikiMetricFilterSet
    paginate_by = 10
    paginate_by_param = 'page_size'

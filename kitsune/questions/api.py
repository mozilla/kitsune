from rest_framework import serializers, viewsets

from kitsune.questions.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    products = serializers.SlugRelatedField(many=True, slug_field='slug')
    topics = serializers.SlugRelatedField(many=True, slug_field='slug')
    creator = serializers.SlugRelatedField(slug_field='username')
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Question
        fields = ('title', 'creator', 'content', 'created', 'updated',
                  'updated_by', 'last_answer', 'num_answers', 'solution',
                  'is_locked', 'is_archived', 'num_votes_past_week',
                  'products', 'topics', 'locale')


class QuestionListSerializer(QuestionSerializer):
    
    class Meta:
        model = Question
        fields = ('title', 'creator', 'created', 'updated', 'updated_by',
                  'last_answer', 'num_answers', 'is_locked', 'is_archived',
                  'num_votes_past_week', 'products', 'topcs', 'locale')


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    pagination_serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    paginate_by = 5

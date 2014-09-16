from rest_framework import serializers, viewsets

from kitsune.questions.models import Question


class QuestionShortSerializer(serializers.ModelSerializer):
    # products = serializers.SlugRelatedField(many=True, slug_field='slug')
    topics = serializers.SlugRelatedField(many=True, slug_field='slug')
    creator = serializers.SlugRelatedField(slug_field='username')
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Question
        fields = (
            'id',
            'created',
            'creator',
            'is_archived',
            'is_locked',
            'last_answer',
            'locale',
            'num_answers',
            'num_votes_past_week',
            'products',
            'title',
            'topics',
            'updated_by',
            'updated',
        )


class QuestionDetailSerializer(QuestionShortSerializer):

    class Meta:
        model = Question
        fields = QuestionShortSerializer.Meta.fields + (
            'content',
            'answers',
        )


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionDetailSerializer
    queryset = Question.objects.all()
    paginate_by = 5

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = QuestionShortSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)

from django.core.exceptions import ValidationError
from rest_framework import serializers, viewsets, permissions, filters

from kitsune.questions.models import Question, Answer


class OnlyCreatorEdits(permissions.BasePermission):
    """
    Only allow objects to be edited and deleted by their creators.

    TODO: This should be tied to user and object permissions better, but
    for now this is a bandaid.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS is a list containing all the read-only methods.
        if request.method in permissions.SAFE_METHODS:
            return True
        # If flow gets here, the method will modify something.
        user = getattr(request, 'user', None)
        owner = getattr(obj, 'creator', None)
        # Only the owner can modify things.
        return user == owner


class QuestionShortSerializer(serializers.ModelSerializer):
    # Use slugs for product and topic instead of ids.
    products = serializers.SlugRelatedField(many=True, slug_field='slug')
    topics = serializers.SlugRelatedField(many=True, slug_field='slug')
    # Use usernames for product and topic instead of ids.
    creator = serializers.SlugRelatedField(
        slug_field='username', required=False)
    updated_by = serializers.SlugRelatedField(
        slug_field='username', required=False)

    class Meta:
        model = Question
        fields = (
            'id',
            'created',
            'creator',
            'is_archived',
            'is_locked',
            'is_spam',
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

    def validate_creator(self, attrs, source):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and attrs.get('creator') is None:
            attrs['creator'] = user
        return attrs

    def validate_products(self, attrs, source):
        if not attrs.get('products', []):
            raise ValidationError('At least one required.')
        return attrs

    def validate_topics(self, attrs, source):
        if not attrs.get('topics', []):
            raise ValidationError('At least one required.')
        return attrs


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
    paginate_by = 100
    permission_classes = [
        OnlyCreatorEdits,
        permissions.IsAuthenticatedOrReadOnly,
    ]
    # filter_backends = [InequalityFilterBackend, filters.DjangoFilterBackend]
    filter_backends = [filters.DjangoFilterBackend]
    filter_fields = [
        'creator',
        'created',
        'is_archived',
        'is_locked',
        'is_spam',
        'locale',
        'num_answers',
        # 'products',
        'title',
        # 'topics',
        'updated',
        'updated_by',
    ]

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = QuestionShortSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)


class AnswerShortSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username')
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Answer
        fields = (
            'question',
            'created',
            'creator',
            'updated',
            'updated_by',
        )


class AnswerDetailSerializer(AnswerShortSerializer):
    class Meta:
        model = Answer
        fields = AnswerShortSerializer.Meta.fields + (
            'content',
        )


class AnswerViewSet(viewsets.ModelViewSet):
    serializer_class = AnswerDetailSerializer
    queryset = Answer.objects.all()
    paginate_by = 100
    permission_classes = [
        OnlyCreatorEdits,
        permissions.IsAuthenticatedOrReadOnly,
    ]
    filter_backends = [filters.DjangoFilterBackend]
    filter_fields = [
        'question',
        'created',
        'creator',
        'updated',
        'updated_by',
    ]

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = AnswerShortSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)

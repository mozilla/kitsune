import django_filters
from django.core.exceptions import ValidationError
from rest_framework import serializers, viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from kitsune.questions.models import Question, Answer, QuestionMetaData
from kitsune.sumo.api import CORSMixin, OnlyCreatorEdits


class QuestionMetaDataSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(
        required=False, write_only=True)

    class Meta:
        model = QuestionMetaData
        fields = ('name', 'value', 'question')

    def get_identity(self, obj):
        return obj['name']

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            for key in self.Meta.fields:
                setattr(instance, key, attrs.get(key, getattr(instance, key)))
            return instance
        else:
            obj, created = self.Meta.model.objects.get_or_create(
                question=attrs['question'], name=attrs['name'],
                defaults={'value': attrs['value']})
            return obj


class QuestionShortSerializer(serializers.ModelSerializer):
    # Use slugs for product and topic instead of ids.
    product = serializers.SlugRelatedField(required=True, slug_field='slug')
    topic = serializers.SlugRelatedField(required=True, slug_field='slug')
    # Use usernames for creator and updated_by instead of ids.
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
            'product',
            'title',
            'topic',
            'updated_by',
            'updated',
        )

    def validate_creator(self, attrs, source):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and attrs.get('creator') is None:
            attrs['creator'] = user
        return attrs


class QuestionDetailSerializer(QuestionShortSerializer):
    metadata = QuestionMetaDataSerializer(
        source='metadata_set', required=False)

    class Meta:
        model = Question
        fields = QuestionShortSerializer.Meta.fields + (
            'content',
            'answers',
            'metadata',
        )


class QuestionFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(name='product__slug')
    creator = django_filters.CharFilter(name='creator__username')

    class Meta(object):
        model = Question
        fields = [
            'creator',
            'created',
            'is_archived',
            'is_locked',
            'is_spam',
            'locale',
            'num_answers',
            'product',
            'title',
            'topic',
            'updated',
            'updated_by',
        ]


class QuestionViewSet(CORSMixin, viewsets.ModelViewSet):
    serializer_class = QuestionDetailSerializer
    queryset = Question.objects.all()
    paginate_by = 20
    permission_classes = [
        OnlyCreatorEdits,
        permissions.IsAuthenticatedOrReadOnly,
    ]
    filter_class = QuestionFilter
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    ordering_fields = [
        'id',
        'created',
        'last_answer',
        'num_answers',
        'num_votes_past_week',
        'updated',
    ]
    # Default, if not overwritten
    ordering = ('-id',)

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = QuestionShortSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)

    @action(methods=['POST'])
    def solve(self, request, pk=None):
        """Accept an answer as the solution to the question."""
        question = self.get_object()
        answer_id = request.DATA.get('answer')

        try:
            answer = Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            return Response({'answer': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        question.set_solution(answer, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'])
    def set_metadata(self, request, pk=None):
        data = request.DATA
        data['question'] = self.get_object().pk

        serializer = QuestionMetaDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', 'DELETE'])
    def delete_metadata(self, request, pk=None):
        question = self.get_object()

        if 'name' not in request.DATA:
            return Response({'name': 'This field is required.'},
                             status=status.HTTP_400_BAD_REQUEST)

        try:
            meta = (QuestionMetaData.objects
                    .get(question=question, name=request.DATA['name']))
            meta.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuestionMetaData.DoesNotExist:
            return Response({'__all__': 'No matching metadata object found.'},
                             status=status.HTTP_404_NOT_FOUND)


class AnswerShortSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username',
                                           required=False)
    updated_by = serializers.SlugRelatedField(slug_field='username',
                                              required=False)

    class Meta:
        model = Answer
        fields = (
            'id',
            'question',
            'created',
            'creator',
            'updated',
            'updated_by',
        )

    def validate_creator(self, attrs, source):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and attrs.get('creator') is None:
            attrs['creator'] = user
        return attrs


class AnswerDetailSerializer(AnswerShortSerializer):
    class Meta:
        model = Answer
        fields = AnswerShortSerializer.Meta.fields + (
            'content',
        )


class AnswerViewSet(CORSMixin, viewsets.ModelViewSet):
    serializer_class = AnswerDetailSerializer
    queryset = Answer.objects.all()
    paginate_by = 20
    permission_classes = [
        OnlyCreatorEdits,
        permissions.IsAuthenticatedOrReadOnly,
    ]
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filter_fields = [
        'question',
        'created',
        'creator',
        'updated',
        'updated_by',
    ]
    ordering_fields = [
        'id',
        'created',
        'updated',
    ]
    # Default, if not overwritten
    ordering = ('-id',)

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = AnswerShortSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)

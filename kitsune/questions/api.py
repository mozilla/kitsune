from datetime import datetime

import django_filters
import json
from django.db.models import Q
from rest_framework import serializers, viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from kitsune.products.api import TopicField
from kitsune.questions.models import (
    Question, Answer, QuestionMetaData, AlreadyTakenException,
    InvalidUserException, QuestionVote, AnswerVote)
from kitsune.sumo.api import DateTimeUTCField, OnlyCreatorEdits, GenericAPIException
from kitsune.users.api import ProfileFKSerializer


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
            obj, created = self.Meta.model.uncached.get_or_create(
                question=attrs['question'], name=attrs['name'],
                defaults={'value': attrs['value']})
            if not created:
                obj.value = attrs['value']
                obj.save()
            return obj


class QuestionSerializer(serializers.ModelSerializer):
    # Use slugs for product and topic instead of ids.
    product = serializers.SlugRelatedField(required=True, slug_field='slug')
    topic = TopicField(required=True)
    # Use usernames for creator and updated_by instead of ids.
    created = DateTimeUTCField(read_only=True)
    creator = ProfileFKSerializer(read_only=True, source='creator.get_profile')
    involved = serializers.SerializerMethodField('get_involved_users')
    is_solved = serializers.Field(source='is_solved')
    metadata = QuestionMetaDataSerializer(source='metadata_set', required=False)
    num_votes = serializers.Field(source='num_votes')
    solution = serializers.PrimaryKeyRelatedField(read_only=True)
    updated = DateTimeUTCField(read_only=True)
    updated_by = serializers.SlugRelatedField(slug_field='username', required=False)

    class Meta:
        model = Question
        fields = (
            'answers',
            'content',
            'created',
            'creator',
            'id',
            'involved',
            'is_archived',
            'is_locked',
            'is_solved',
            'is_spam',
            'last_answer',
            'locale',
            'metadata',
            'num_answers',
            'num_votes_past_week',
            'num_votes',
            'product',
            'solution',
            'taken_until',
            'taken_by',
            'title',
            'topic',
            'updated_by',
            'updated',
        )

    def get_involved_users(self, obj):
        involved = set([obj.creator])
        involved.update(a.creator for a in obj.answers.all())
        return list(involved)

    def validate_creator(self, attrs, source):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and attrs.get(source) is None:
            attrs['creator'] = user
        return attrs


class QuestionFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(name='product__slug')
    creator = django_filters.CharFilter(name='creator__username')
    involved = django_filters.MethodFilter(action='filter_involved')
    metadata = django_filters.MethodFilter(action='filter_metadata')
    is_solved = django_filters.MethodFilter(action='filter_is_solved')

    class Meta(object):
        model = Question
        fields = [
            'creator',
            'created',
            'involved',
            'is_archived',
            'is_locked',
            'is_spam',
            'is_solved',
            'locale',
            'num_answers',
            'product',
            'title',
            'topic',
            'updated',
            'updated_by',
        ]

    def filter_involved(self, queryset, value):
        creator_filter = Q(creator__username=value)
        answer_creator_filter = Q(answers__creator__username=value)
        return queryset.filter(creator_filter | answer_creator_filter)

    def filter_is_taken(self, queryset, value):
        field = serializers.BooleanField()
        value = field.from_native(value)
        # is_taken doesn't exist. Instead, we decide if a question is taken
        # based on ``taken_by`` and ``taken_until``.
        now = datetime.now()
        if value:
            # only taken questions
            return queryset.filter(~Q(taken_by=None), taken_until__gt=now)
        else:
            # only not taken questions
            return queryset.filter(Q(taken_by=None) | Q(taken_until__lt=now))

    def filter_is_solved(self, queryset, value):
        field = serializers.BooleanField()
        value = field.from_native(value)
        solved_filter = Q(solution=None)
        if value:
            solved_filter = ~solved_filter
        return queryset.filter(solved_filter)

    def filter_metadata(self, queryset, value):
        try:
            value = json.loads(value)
        except ValueError:
            raise GenericAPIException(400, 'metadata must be valid JSON.')

        for name, values in value.items():
            if not isinstance(values, list):
                values = [values]
            query = Q()
            for v in values:
                if v is None:
                    query = query | ~Q(metadata_set__name=name)
                else:
                    query = query | Q(metadata_set__name=name, metadata_set__value=v)
            queryset = queryset.filter(query)

        return queryset


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.uncached.all()
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

    @action(methods=['POST'])
    def solve(self, request, pk=None):
        """Accept an answer as the solution to the question."""
        question = self.get_object()
        answer_id = request.DATA.get('answer')

        try:
            answer = Answer.uncached.get(pk=answer_id)
        except Answer.DoesNotExist:
            return Response({'answer': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        question.set_solution(answer, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        question = self.get_object()
        if not question.editable:
            raise GenericAPIException(403, 'Question not editable')
        if question.has_voted(request):
            raise GenericAPIException(409, 'Cannot vote twice')
        QuestionVote(question=question, creator=request.user).save()
        return Response("", status=204)

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
            meta = (QuestionMetaData.uncached
                    .get(question=question, name=request.DATA['name']))
            meta.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuestionMetaData.DoesNotExist:
            raise GenericAPIException(404, 'No matching metadata object found.')

    @action(methods=['POST'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def take(self, request, pk=None):
        question = self.get_object()
        field = serializers.BooleanField()
        force = field.from_native(request.DATA.get('force', False))

        try:
            question.take(request.user, force=force)
        except InvalidUserException:
            raise GenericAPIException(400, 'Question creator cannot take a question.')
        except AlreadyTakenException:
            raise GenericAPIException(409, 'Conflict: question is already taken.')

        return Response(status=204)


class AnswerSerializer(serializers.ModelSerializer):
    created = DateTimeUTCField(read_only=True)
    creator = ProfileFKSerializer(read_only=True, source='creator.get_profile')
    updated = DateTimeUTCField(read_only=True)
    updated_by = serializers.SlugRelatedField(slug_field='username', required=False)
    num_helpful_votes = serializers.Field(source='num_helpful_votes')
    num_unhelpful_votes = serializers.Field(source='num_unhelpful_votes')

    class Meta:
        model = Answer
        fields = (
            'id',
            'question',
            'content',
            'created',
            'creator',
            'updated',
            'updated_by',
            'is_spam',
            'num_helpful_votes',
            'num_unhelpful_votes',
        )

    def validate_creator(self, attrs, source):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and attrs.get('creator') is None:
            attrs['creator'] = user
        return attrs


class AnswerFilter(django_filters.FilterSet):
    creator = django_filters.CharFilter(name='creator__username')
    question = django_filters.Filter(name='question__id')

    class Meta(object):
        model = Answer
        fields = [
            'question',
            'creator',
            'created',
            'updated',
            'updated_by',
            'is_spam',
        ]


class AnswerViewSet(viewsets.ModelViewSet):
    serializer_class = AnswerSerializer
    queryset = Answer.uncached.all()
    paginate_by = 20
    permission_classes = [
        OnlyCreatorEdits,
        permissions.IsAuthenticatedOrReadOnly,
    ]
    filter_class = AnswerFilter
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
                object_serializer_class = AnswerSerializer

        context = self.get_serializer_context()
        return SerializerClass(instance=page, context=context)

    @action(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        answer = self.get_object()
        if not answer.question.editable:
            raise GenericAPIException(403, 'Answer not editable')
        if answer.has_voted(request):
            raise GenericAPIException(409, 'Cannot vote twice')
        AnswerVote(answer=answer, creator=request.user, helpful=True).save()
        return Response("", status=204)

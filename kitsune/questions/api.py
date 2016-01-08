from datetime import datetime

import actstream.actions
import django_filters
import json
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers, viewsets, permissions, filters, status, pagination
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from taggit.models import Tag

from kitsune.products.api_utils import TopicField
from kitsune.products.models import Product, Topic
from kitsune.questions.models import (
    Question, Answer, QuestionMetaData, AlreadyTakenException,
    InvalidUserException, QuestionVote, AnswerVote)
from kitsune.sumo.api_utils import (
    DateTimeUTCField, OnlyCreatorEdits, GenericAPIException, SplitSourceField)
from kitsune.tags.utils import add_existing_tag
from kitsune.upload.models import ImageAttachment
from kitsune.users.api import ProfileFKSerializer
from kitsune.users.models import Profile


class QuestionMetaDataSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(
        required=False,
        write_only=True,
        queryset=Question.objects.all())

    class Meta:
        model = QuestionMetaData
        fields = ('name', 'value', 'question')


class QuestionSerializer(serializers.ModelSerializer):
    answers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    content = SplitSourceField(read_source='content_parsed', write_source='content')
    created = DateTimeUTCField(read_only=True)
    creator = serializers.SerializerMethodField()
    involved = serializers.SerializerMethodField()
    is_solved = serializers.ReadOnlyField()
    is_taken = serializers.ReadOnlyField()
    metadata = QuestionMetaDataSerializer(source='metadata_set', read_only=True, many=True)
    num_votes = serializers.ReadOnlyField()
    product = serializers.SlugRelatedField(
        required=True,
        slug_field='slug',
        queryset=Product.objects.all())
    tags = serializers.SerializerMethodField()
    solution = serializers.PrimaryKeyRelatedField(read_only=True)
    solved_by = serializers.SerializerMethodField()
    taken_by = serializers.SerializerMethodField()
    topic = TopicField(required=True, queryset=Topic.objects.all())
    updated = DateTimeUTCField(read_only=True)
    updated_by = serializers.SerializerMethodField()

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
            'is_taken',
            'last_answer',
            'locale',
            'metadata',
            'tags',
            'num_answers',
            'num_votes_past_week',
            'num_votes',
            'product',
            'solution',
            'solved_by',
            'taken_until',
            'taken_by',
            'title',
            'topic',
            'updated_by',
            'updated',
        )

    def get_involved(self, obj):
        involved = set([obj.creator.profile])
        involved.update(a.creator.profile for a in obj.answers.all())
        return ProfileFKSerializer(involved, many=True).data

    def get_solved_by(self, obj):
        if obj.solution:
            return ProfileFKSerializer(obj.solution.creator.profile).data
        else:
            return None

    def get_creator(self, obj):
        return ProfileFKSerializer(obj.creator.profile).data

    def get_taken_by(self, obj):
        if obj.taken_by:
            return ProfileFKSerializer(obj.taken_by.profile).data
        else:
            return None

    def get_updated_by(self, obj):
        if obj.updated_by:
            return ProfileFKSerializer(obj.updated_by.profile).data
        else:
            return None

    def get_tags(self, obj):
        return [{'name': tag.name, 'slug': tag.slug} for tag in obj.tags.all()]

    def validate(self, data):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and data.get('creator') is None:
            data['creator'] = user
        return data


class QuestionFKSerializer(QuestionSerializer):

    class Meta:
        model = Question
        fields = (
            'creator',
            'id',
            'title',
        )


class QuestionFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(name='product__slug')
    creator = django_filters.CharFilter(name='creator__username')
    involved = django_filters.MethodFilter(action='filter_involved')
    is_solved = django_filters.MethodFilter(action='filter_is_solved')
    is_taken = django_filters.MethodFilter(action='filter_is_taken')
    metadata = django_filters.MethodFilter(action='filter_metadata')
    solved_by = django_filters.MethodFilter(action='filter_solved_by')
    taken_by = django_filters.CharFilter(name='taken_by__username')

    class Meta(object):
        model = Question
        fields = [
            'creator',
            'created',
            'involved',
            'is_archived',
            'is_locked',
            'is_solved',
            'is_spam',
            'is_taken',
            'locale',
            'num_answers',
            'product',
            'solved_by',
            'taken_by',
            'title',
            'topic',
            'updated',
            'updated_by',
        ]

    def filter_involved(self, queryset, username):
        # This will remain unevaluated, and become a subquery of the final query.
        # Using a subquery instead of a JOIN like Django would normally do
        # should be faster in this case.
        questions_user_answered = (
            Answer.objects.filter(creator__username=username).values('question_id'))

        answered_filter = Q(id__in=questions_user_answered)
        creator_filter = Q(creator__username=username)
        return queryset.filter(creator_filter | answered_filter)

    def filter_is_taken(self, queryset, value):
        field = serializers.BooleanField()
        value = field.to_internal_value(value)
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
        value = field.to_internal_value(value)
        solved_filter = Q(solution=None)
        if value:
            solved_filter = ~solved_filter
        return queryset.filter(solved_filter)

    def filter_solved_by(self, queryset, username):
        question_user_solved = (
            Question.objects.filter(solution__creator__username=username).values('id'))

        return queryset.filter(id__in=question_user_solved)

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
    queryset = Question.objects.all()
    pagination_class = pagination.PageNumberPagination
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

    @detail_route(methods=['POST'])
    def solve(self, request, pk=None):
        """Accept an answer as the solution to the question."""
        question = self.get_object()
        answer_id = request.data.get('answer')

        try:
            answer = Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            return Response({'answer': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        question.set_solution(answer, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        question = self.get_object()

        if not question.editable:
            raise GenericAPIException(403, 'Question not editable')
        if question.has_voted(request):
            raise GenericAPIException(409, 'Cannot vote twice')

        QuestionVote(question=question, creator=request.user).save()
        num_votes = QuestionVote.objects.filter(question=question).count()
        return Response({'num_votes': num_votes})

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        question = self.get_object()
        actstream.actions.follow(request.user, question, actor_only=False, send_action=False)
        return Response('', status=204)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        question = self.get_object()
        actstream.actions.unfollow(request.user, question, send_action=False)
        return Response('', status=204)

    @detail_route(methods=['POST'])
    def set_metadata(self, request, pk=None):
        data = {}
        data.update(request.data)
        data['question'] = self.get_object().pk

        serializer = QuestionMetaDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST', 'DELETE'])
    def delete_metadata(self, request, pk=None):
        question = self.get_object()

        if 'name' not in request.data:
            return Response({'name': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            meta = (QuestionMetaData.objects
                    .get(question=question, name=request.data['name']))
            meta.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuestionMetaData.DoesNotExist:
            raise GenericAPIException(404, 'No matching metadata object found.')

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def take(self, request, pk=None):
        question = self.get_object()
        field = serializers.BooleanField()
        force = field.to_internal_value(request.data.get('force', False))

        try:
            question.take(request.user, force=force)
        except InvalidUserException:
            raise GenericAPIException(400, 'Question creator cannot take a question.')
        except AlreadyTakenException:
            raise GenericAPIException(409, 'Conflict: question is already taken.')

        return Response(status=204)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def add_tags(self, request, pk=None):
        question = self.get_object()

        if 'tags' not in request.data:
            return Response({'tags': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        tags = request.data['tags']

        for tag in tags:
            try:
                add_existing_tag(tag, question.tags)
            except Tag.DoesNotExist:
                if request.user.has_perm('taggit.add_tag'):
                    question.tags.add(tag)
                else:
                    raise GenericAPIException(403, 'You are not authorized to create new tags.')

        data = [{'name': tag.name, 'slug': tag.slug} for tag in question.tags.all()]
        return Response(data)

    @detail_route(methods=['POST', 'DELETE'], permission_classes=[permissions.IsAuthenticated])
    def remove_tags(self, request, pk=None):
        question = self.get_object()

        if 'tags' not in request.data:
            return Response({'tags': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        tags = request.data['tags']

        for tag in tags:
            question.tags.remove(tag)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def auto_tag(self, request, pk=None):
        question = self.get_object()
        question.auto_tag()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['POST'])
    def attach_images(self, request, pk=None):
        question = self.get_object()

        user_ct = ContentType.objects.get_for_model(request.user)
        qst_ct = ContentType.objects.get_for_model(question)

        # Move over to the question all of the images I added to the reply form
        up_images = ImageAttachment.objects.filter(creator=request.user, content_type=user_ct)
        up_images.update(content_type=qst_ct, object_id=question.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerSerializer(serializers.ModelSerializer):
    content = SplitSourceField(read_source='content_parsed', write_source='content')
    created = DateTimeUTCField(read_only=True)
    creator = serializers.SerializerMethodField()
    num_helpful_votes = serializers.ReadOnlyField()
    num_unhelpful_votes = serializers.ReadOnlyField()
    updated = DateTimeUTCField(read_only=True)
    updated_by = serializers.SerializerMethodField()

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

    def get_creator(self, obj):
        return ProfileFKSerializer(Profile.objects.get(user=obj.creator)).data

    def get_updated_by(self, obj):
        updated_by = Profile.objects.get(user=obj.updated_by) if obj.updated_by else None
        return ProfileFKSerializer(updated_by).data if updated_by else None

    def validate(self, data):
        user = getattr(self.context.get('request'), 'user')
        if user and not user.is_anonymous() and data.get('creator') is None:
            data['creator'] = user
        return data


class AnswerFKSerializer(AnswerSerializer):

    class Meta:
        model = Answer
        fields = (
            'id',
            'question',
            'creator',
        )


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
    queryset = Answer.objects.all()
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

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        answer = self.get_object()

        if not answer.question.editable:
            raise GenericAPIException(403, 'Answer not editable')
        if answer.has_voted(request):
            raise GenericAPIException(409, 'Cannot vote twice')

        AnswerVote(answer=answer, creator=request.user, helpful=True).save()
        num_helpful_votes = AnswerVote.objects.filter(answer=answer, helpful=True).count()
        num_unhelpful_votes = AnswerVote.objects.filter(answer=answer, helpful=False).count()
        return Response({
            'num_helpful_votes': num_helpful_votes,
            'num_unhelpful_votes': num_unhelpful_votes,
        })

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        answer = self.get_object()
        actstream.actions.follow(request.user, answer, actor_only=False)
        return Response('', status=204)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        answer = self.get_object()
        actstream.actions.unfollow(request.user, answer)
        return Response('', status=204)

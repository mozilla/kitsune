from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers, status

from kitsune.sumo.api import (CORSMixin, GenericAPIException,
                              LocaleNegotiationMixin)
from kitsune.sumo.utils import uselocale
from kitsune.questions.models import Question, Answer


class QuestionShortSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Question
        fields = ('id', 'title', 'creator', 'content', 'locale')


class QuestionDetailSerializer(QuestionShortSerializer):
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta(QuestionShortSerializer.Meta):
        fields = (QuestionShortSerializer.Meta.fields +
                  ('created', 'updated', 'updated_by', 'answers', 'solution',
                   'is_locked', 'is_archived', 'products', 'topics'))


class QuestionList(CORSMixin, generics.ListAPIView):
    """List all questions."""
    queryset = Question.objects.all()
    serializer_class = QuestionShortSerializer
    paginate_by = 100

    def get_queryset(self):
        qs = super(QuestionList, self).get_queryset()
        locale = locale = self.request.QUERY_PARAMS.get('locale')
        if locale is not None:
            qs = qs.filter(locale=locale)
        return qs


class QuestionDetail(CORSMixin, generics.RetrieveAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionDetailSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class AnswerShortSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Answer
        fields = ('id', 'creator', 'content', 'question')


class AnswerDetailSerializer(AnswerShortSerializer):
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta(AnswerShortSerializer.Meta):
        fields = (AnswerShortSerializer.Meta.fields +
                  ())


class AnswerList(CORSMixin, generics.ListAPIView):
    """List all answers."""
    queryset = Answer.objects.all()
    serializer_class = AnswerShortSerializer

    def get_queryset(self):
        qs = super(AnswerList, self).get_queryset()
        qs = qs.filter(**self.kwargs)

        locale = locale = self.request.QUERY_PARAMS.get('locale')
        if locale is not None:
            qs = qs.filter(locale=locale)

        return qs


class AnswerDetail(CORSMixin, generics.RetrieveAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerDetailSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

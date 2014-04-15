# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

# Local application / specific library imports
from machina.core.loading import get_class

Post = get_model('conversation', 'Post')
Topic = get_model('conversation', 'Topic')

PermissionHandler = get_class('permission.handler', 'PermissionHandler')
perm_handler = PermissionHandler()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['subject', 'content', ]

    def __init__(self, *args, **kwargs):
        self.poster = kwargs.pop('poster', None)
        self.poster_ip = kwargs.pop('poster_ip', None)
        self.forum = kwargs.pop('forum', None)
        self.topic = kwargs.pop('topic', None)

        super(PostForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # First handle updates
        if self.instance.pk:
            pass

        post = Post(
            topic=self.topic,
            poster=self.poster,
            poster_ip=self.poster_ip,
            subject=self.cleaned_data['subject'],
            content=self.cleaned_data['content'])

        if commit:
            post.save()

        return post


class TopicForm(PostForm):
    topic_type = forms.ChoiceField(label=_('Post topic as'), choices=Topic.TYPE_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)

        # Perform some checks before doing anything
        self.can_add_stickies = perm_handler.can_add_stickies(self.forum, self.poster)
        self.can_add_announcements = perm_handler.can_add_announcements(self.forum, self.poster)

        if not self.can_add_stickies:
            choices = filter(
                lambda t: t[0] != Topic.TYPE_CHOICES.topic_sticky,
                self.fields['topic_type'].choices)
            self.fields['topic_type'].choices = choices
        if not self.can_add_announcements:
            choices = filter(
                lambda t: t[0] != Topic.TYPE_CHOICES.topic_announce,
                self.fields['topic_type'].choices)
            self.fields['topic_type'].choices = choices

    def save(self, commit=True):
        # First, handle updates
        if self.instance.pk:
            pass

        if self.forum and self.topic is None:
            if 'topic_type' in self.cleaned_data:
                topic_type = self.cleaned_data['topic_type']
            else:
                topic_type = Topic.TYPE_CHOICES.topic_post

            topic = Topic(
                forum=self.forum,
                poster=self.poster,
                subject=self.cleaned_data['subject'],  # The topic's name is the post's name
                type=topic_type,
                status=Topic.STATUS_CHOICES.topic_unlocked)
            self.topic = topic
            if commit:
                topic.save()

        return super(TopicForm, self).save(commit)

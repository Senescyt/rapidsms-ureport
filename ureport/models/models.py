# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q
from poll.models import Poll
from rapidsms.models import Contact, Connection
from django.contrib.auth.models import User, Group
from rapidsms.contrib.locations.models import Location
from script.models import ScriptSession
from rapidsms_httprouter.models import Message
from unregister.models import Blacklist
from django.db.models.signals import post_save
from ussd.models import ussd_complete
import datetime
import re
from script.signals import script_progress_was_completed


class IgnoredTags(models.Model):
    poll = models.ForeignKey(Poll)
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return '%s' % self.name

    class Meta:
        app_label = 'ureport'


class QuoteBox(models.Model):
    question = models.TextField()
    quote = models.TextField()
    quoted = models.TextField()
    creation_date = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = 'creation_date'
        app_label = 'ureport'


class TopResponses(models.Model):
    poll = models.ForeignKey(Poll, related_name="top_responses")
    quote = models.TextField()
    quoted = models.TextField()

    class Meta:
        app_label = 'ureport'


class EquatelLocation(models.Model):
    serial = models.CharField(max_length=50)
    segment = models.CharField(max_length=50, null=True)
    location = models.ForeignKey(Location)
    name = models.CharField(max_length=50, null=True)

    class Meta:
        app_label = 'ureport'


class Permit(models.Model):
    user = models.ForeignKey(User)
    allowed = models.CharField(max_length=200)
    date = models.DateField(auto_now=True)

    def get_patterns(self):
        pats = []
        ropes = self.allowed.split(",")
        for rop in ropes:
            pattern = re.compile(rop + r"(.*)")
            pats.append(pattern)
        return pats

    def __unicode__(self):
        return self.user.username

    class Meta:
        app_label = 'ureport'


class Ureporter(Contact):
    from_cache = False

    def age(self):
        if self.birthdate:
            return (datetime.datetime.now() - self.birthdate).days / 365
        else:
            return ""

    def is_active(self):
        return not Blacklist.objects.filter(connection=self.default_connection)

    def join_date(self):
        ss = ScriptSession.objects.filter(connection__contact=self)
        if ss:
            return ScriptSession.objects.filter(connection__contact=self)[0].start_time.date()
        else:
            messages = Message.objects.filter(connection=self.default_connection).order_by('date')
            if messages:
                return messages[0].date
            else:
                return None

    def quit_date(self):
        quit_msg = Message.objects.filter(connection__contact=self, application="unregister")
        if quit_msg:
            return quit_msg.latest('date').date

    def messages_count(self):
        return Message.objects.filter(connection__contact=self, direction="I").count()

    class Meta:
        permissions = [
            ("view_numbers", "can view private info"),
            ("restricted_access", "can view only particular pages"),
            ("can_filter", "can view filters"),
            ("can_action", "can view actions"),
            ("view_number", "can view numbers"),
            ("can_export", "can view exports"),
            ("can_forward", "can forward messages"),

        ]

        proxy = True
        app_label = 'ureport'


class MessageAttribute(models.Model):
    '''
    The 'MessageAttribute' model represents a class of feature found
    across a set of messages. It does not store any data values
    related to the attribute, but only describes what kind of a
    message feature we are trying to capture.

    Possible attributes include things like number of replies,severity,department    etc
    '''
    name = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        app_label = 'ureport'


class MessageDetail(models.Model):
    '''
    The 'MessageDetail' model represents information unique to a
    specific message. This is a generic design that can be used to
    extend the information contained in the 'Message' model with
    specific, extra details.
    '''

    message = models.ForeignKey(Message, related_name='details')
    attribute = models.ForeignKey('MessageAttribute')
    value = models.CharField(max_length=500)
    description = models.TextField(null=True)

    def __unicode__(self):
        return u'%s: %s' % (self.message, self.attribute)

    class Meta:
        app_label = 'ureport'


class Settings(models.Model):
    """
    configurable  sitewide settings. Its better to store in db table

    """
    attribute = models.CharField(max_length=50, null=False)
    value = models.CharField(default='', max_length=50, null=True)
    description = models.TextField(null=True)
    user = models.ForeignKey(User, null=True, blank=True)


    class Meta:
        app_label = 'ureport'


class AutoregGroupRules(models.Model):
    contains_all_of = 1
    contains_one_of = 2
    group = models.ForeignKey(Group, related_name="rules")
    rule = models.IntegerField(max_length=10,
                               choices=((contains_all_of, "contains_all_of"), (contains_one_of, "contains_one_of"),),
                               null=True)
    values = models.TextField(default=None, null=True)
    closed = models.NullBooleanField(default=False)
    rule_regex = models.CharField(max_length=700, null=True)

    def get_regex(self):
        words = self.values.split(",")

        if self.rule == 1:
            all_template = r"(?=.*\b%s\b)"
            w_regex = r""
            for word in words:
                w_regex = w_regex + all_template % re.escape(word)
            return w_regex

        elif self.rule == 2:
            one_template = r"(\b%s\b)"
            w_regex = r""
            for word in words:
                if len(w_regex):
                    w_regex = w_regex + r"|" + one_template % re.escape(word)
                else:
                    w_regex = w_regex + one_template % re.escape(word)

            return w_regex

    def save(self, *args, **kwargs):
        if self.values:
            self.rule_regex = self.get_regex()
        super(AutoregGroupRules, self).save()


    class Meta:
        app_label = 'ureport'


from .litseners import autoreg, check_conn, update_latest_poll, ussd_poll, add_to_poll

script_progress_was_completed.connect(autoreg, weak=False)
post_save.connect(check_conn, sender=Connection, weak=False)
post_save.connect(update_latest_poll, sender=Poll, weak=False)
ussd_complete.connect(ussd_poll, weak=False)
#post_save.connect(add_to_poll, sender=Blacklist, weak=False)


class UPoll(Poll):
    bool_dict = {'false': False, 'true': True}

    def set_attr(self, key, value):
        p = PollAttribute.objects.get_or_create(poll=self, key=key)[0]
        p.value = value
        p.save()
        return self.get_attr(key)

    def get_attr(self, key):
        try:
            p = PollAttribute.objects.get(poll=self, key=key)
            if p.key_type == 'bool':
                return self.bool_dict[p.value.lower()]
            elif p.key_type == 'int':
                return int(p.value)
            else:
                return p.value
        except PollAttribute.DoesNotExist:
            attributes = PollAttribute.objects.filter(key=key)
            if attributes:
                key_type = attributes[0].key_type
                if key_type == 'bool':
                    return True
                elif key_type == 'int':
                    return 1
                else:
                    return ""
            else:
                raise models.ObjectDoesNotExist("Poll object does not have attribute %s" % key)

    class Meta:
        proxy = True


class PollAttribute(models.Model):
    KEY_TYPES = (('bool', 'bool'), ('char', 'char'), ('int', 'int'), ('obj', 'obj'))
    key = models.CharField(max_length=100)
    key_type = models.CharField(max_length=100, choices=KEY_TYPES)
    value = models.CharField(max_length=200)
    poll = models.ForeignKey(Poll)
    key_default = models.CharField(max_length=100, null=True)


    class Meta:
        app_label = 'ureport'
        unique_together = (('poll', 'key'), ('key', 'key_default'))

    def set_default(self, default):
        self.key_default = str(default).lower()

    @classmethod
    def _get_default_for_key(key):
        attr = PollAttribute.objects.filter(key=key).exclude(key_default=None)
        if attr.exists():
            return attr[0].key_default

        def get_default(self):
            if self.key_type == 'bool':
                return True if self.key_default.lower() == 'true' else False
            elif self.key_type == 'int':
                return int(self.key_default)

        def save(self, force_insert=False, force_update=False, using=None):
            if self.value.lower() in ['false', 'true']:
                self.key_type = 'bool'
            else:
                try:
                    int(self.value)
                    self.key_type = 'int'
                except ValueError:
                    self.key_type = 'char'

            super(PollAttribute, self).save()


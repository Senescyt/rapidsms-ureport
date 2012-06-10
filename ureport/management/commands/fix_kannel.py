from django.core.management.base import BaseCommand
import traceback
import os
from script.models import ScriptSession
from ureport.settings import UREPORT_ROOT
from rapidsms.models import Contact
from django.utils.datastructures import SortedDict
from poll.models import Poll
import datetime
from unregister.models import Blacklist
from django.conf import settings
from rapidsms_httprouter.models import Message
from django.db import connection
from optparse import OptionParser, make_option
import re


class Command(BaseCommand):


    def handle(self, **options):

        poll =Poll.objects.get(pk=236)
        file1=open("/home/mossplix/log_8.txt")
        file2=open("/home/mossplix/log_9.txt")
        files=[file1,file2]
        num=re.compile('([0-9]+)')
        for f in files:
            lines=f.readlines()
            for line in lines:
                parts=line.strip().rsplit('[FID:]')[1].split('] [')
                identity=num.search(parts[0]).groups()[0]
                message_text=parts[3].rsplit(':')[-1]
                msg=Message.objects.filter(connection__identity=identity,text=message_text,direction="I")
                if msg.exists:
                    continue
                else:

                    msg=Message.objects.create(connection__identity=identity,text=message_text,direction="I")
                    print "created "+msg.text
                    poll.process_response(msg)


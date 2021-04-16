from django.core.management.base import BaseCommand
from django.db import transaction as tx
import csv
from website.models import Question, Answer
from django.conf import settings
from django.utils.html import strip_tags
import uuid

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('foss', nargs='+',type=str, help='Indicates the foss list.')

    @tx.atomic
    def handle(self, *args, **options):
        print("Generating Question Metadata. Please wait...")
        meta_file_name = 'metadata_'+uuid.uuid4().hex+".csv"
        with open(settings.MEDIA_ROOT + meta_file_name, "w+", newline='') as metafile:
            metawriter = csv.writer(metafile, dialect='excel', delimiter='|')
            metawriter.writerow(["FOSS","Tutorial","Video Minute Range","Video Second Range","Question Title","Question Body","Question_Date","Question Posted By","Answer No.","Answer Body","Answer Date", "Answer Posted By"])
            foss = options['foss']
            for f in foss:
                questions = Question.objects.filter(category=f, status=1)
                for q in questions:
                    metawriter.writerow([q.category,q.tutorial,q.minute_range,q.second_range,q.title,strip_tags(q.body).strip("&nbsp;"),q.date_created,q.user()])
                    answers = Answer.objects.filter(question=q)
                    for i, a in enumerate(answers):
                        metawriter.writerow(["","","","","","","","",i+1, strip_tags(a.body).strip("&nbsp;"),a.date_created, a.user()])
                    metawriter.writerow([])
            print("Metadata File Generated. Please find the file at location given below.")
            print(metafile.name)


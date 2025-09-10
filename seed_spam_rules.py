# Script to seed the database with predefined spam rules
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "forums.settings")
django.setup()

from django.db.models import Q
from website.models import SpamRule



def seed_spam_rules():
    rules = {
        # Certification/Exam dump patterns
        "Certification/Exam Spam": {
            "score": 30,
            "type": SpamRule.KEYWORD,
            "patterns": [
                r"exam\s+dumps?", r"braindumps?", r"practice\s+test",
                r"certification\s+exam", r"test\s+preparation",
                r"exam\s+questions?", r"study\s+guides?",
                r"pdf\s+\+\s+testing\s+engine", r"testing\s+engine",
                r"exam\s+prep", r"mock\s+exam", r"real\s+exam",
                r"dumps\s+pdf", r"braindump"
            ],
        },

        # Promotional spam
        "Promotional Spam": {
            "score": 25,
            "type": SpamRule.KEYWORD,
            "patterns": [
                r"click\s+here", r"join\s+now", r"limited\s+time",
                r"discount", r"coupon\s+code", r"20%\s+off",
                r"free\s+download", r"get\s+certified",
                r"unlock\s+your\s+career", r"master\s+the",
                r"boost\s+your\s+career", r"cert20",
                r"at\s+checkout", r"special\s+offer",
            ],
        },

        # Suspicious domains
        "Suspicious Domain": {
            "score": 35,
            "type": SpamRule.DOMAIN,
            "patterns": [
                r"dumpscafe\.com", r"certsout\.com", r"mycertshub\.com",
                r"vmexam\.com", r"kissnutra\.com", r"dumps.*\.com",
                r"cert.*\.com", r"exam.*\.com",
            ],
        },

        # Generic business language
        "Business/Career Spam": {
            "score": 15,
            "type": SpamRule.KEYWORD,
            "patterns": [
                r"attests\s+to\s+your\s+proficiency",
                r"esteemed\s+(?:accreditation|certification|credential)",
                r"valuable\s+asset\s+to\s+companies",
                r"demonstrates\s+your\s+ability",
                r"comprehensive\s+study\s+(?:tools|materials)",
                r"interactive\s+practice\s+tests",
                r"real\s+exam\s+questions",
                r"actual\s+exam\s+questions",
                r"validated\s+by\s+.*certification",
                r"urgently\s+need\s+experts",
            ],
        },

        # Gaming content
        "Gaming Spam": {
            "score": 20,
            "type": SpamRule.KEYWORD,
            "patterns": [
                r"spacebar\s+clicker", r"clicker\s+game",
                r"addictive\s+game", r"upgrades\s+available",
                r"instant\s+rewards",
            ],
        },

        # Health/Supplement spam
        "Health Spam": {
            "score": 22,
            "type": SpamRule.KEYWORD,
            "patterns": [
                r"vitalit[äa]t", r"nahrungserg[äa]nzungsmittel",
                r"libido", r"fruchtbarkeit", r"energie",
                r"hormonelle\s+balance", r"perforan",
            ],
        },
    }

    inserted, skipped = 0, 0
    for note, config in rules.items():
        for pattern in config["patterns"]:
            exists = SpamRule.objects.filter(
                Q(pattern=pattern) & Q(type=config["type"])
            ).exists()
            if not exists:
                SpamRule.objects.create(
                    type=config["type"],
                    pattern=pattern,
                    score=config["score"],
                    notes=note,
                )
                inserted += 1
            else:
                skipped += 1

    print(f"✅ Inserted {inserted} new rules, skipped {skipped} existing ones.")


# Run it
seed_spam_rules()

from kitsune.gallery.models import Image, Video
from kitsune.users.models import Profile
from kitsune.wiki.models import Document, Locale


def run():
    """Fix casing in locale code for sr-Cyrl and sr-Latn."""
    Document.objects.filter(locale='sr-CYRL').update(locale='sr-Cyrl')
    Locale.objects.filter(locale='sr-CYRL').update(locale='sr-Cyrl')
    Image.objects.filter(locale='sr-CYRL').update(locale='sr-Cyrl')
    Video.objects.filter(locale='sr-CYRL').update(locale='sr-Cyrl')
    Profile.objects.filter(locale='sr-CYRL').update(locale='sr-Cyrl')

    Document.objects.filter(locale='sr-LATN').update(locale='sr-Latn')
    Locale.objects.filter(locale='sr-LATN').update(locale='sr-Latn')
    Image.objects.filter(locale='sr-LATN').update(locale='sr-Latn')
    Video.objects.filter(locale='sr-LATN').update(locale='sr-Latn')
    Profile.objects.filter(locale='sr-LATN').update(locale='sr-Latn')

from gallery.models import Image, Video
from users.models import Profile
from wiki.models import Document


def run():
    """Move everything from 'sv-SE' to 'sv' locale."""
    Document.objects.filter(locale='sv-SE').update(locale='sv')
    Image.objects.filter(locale='sv-SE').update(locale='sv')
    Video.objects.filter(locale='sv-SE').update(locale='sv')
    Profile.objects.filter(locale='sv-SE').update(locale='sv')

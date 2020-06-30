from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from pipeline.storage import PipelineMixin


class SumoFilesStorage(PipelineMixin, ManifestStaticFilesStorage):
    def __init__(self, *args, **kwargs):
        kwargs["file_permissions_mode"] = 0o644
        kwargs["directory_permissions_mode"] = 0o755
        super(SumoFilesStorage, self).__init__(*args, **kwargs)

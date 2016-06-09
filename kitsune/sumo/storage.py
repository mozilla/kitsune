from pipeline.storage import PipelineCachedStorage


class SumoFilesStorage(PipelineCachedStorage):
    def __init__(self, *args, **kwargs):
        kwargs['file_permissions_mode'] = 0o644
        kwargs['directory_permissions_mode'] = 0o755
        super(SumoFilesStorage, self).__init__(*args, **kwargs)

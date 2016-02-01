class AuthorityException(Exception):
    pass


class NotAModel(AuthorityException):
    def __init__(self, object):
        super(NotAModel, self).__init__(
            "Not a model class or instance")


class UnsavedModelInstance(AuthorityException):
    def __init__(self, object):
        super(UnsavedModelInstance, self).__init__(
            "Model instance has no pk, was it saved?")

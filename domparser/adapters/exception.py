class GWCError(Exception):
    return_code = 1
    reportable = False  # Exception may be reported to core maintainers

    def __init__(self, message, caused_by=None, **kwargs):
        self.message = message
        self._kwargs = kwargs
        self._caused_by = caused_by
        super(GWCError, self).__init__(message)

    # If we add __unicode__ to GWCError then we must also add it to all classes that
    # inherit from it if they have their own __repr__ (and maybe __str__) function.
    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, str(self))

    def __str__(self):
        return str(self.message % self._kwargs)

    def dump_map(self):
        result = dict((k, v) for k, v in vars(self).items() if not k.startswith("_"))
        result.update(
            exception_type=str(type(self)),
            exception_name=self.__class__.__name__,
            message=str(self),
            error=repr(self),
            caused_by=repr(self._caused_by),
            **self._kwargs,
        )
        return result


class AuthenticationError(GWCError):
    pass

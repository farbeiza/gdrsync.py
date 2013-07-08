class Context(object):
    @property
    def drive(self):
        raise NotImplementedError()

    @property
    def http(self):
        raise NotImplementedError()

    def logProgress(self,
                    path,
                    start,
                    bytesUploaded,
                    bytesTotal,
                    progress,
                    end):
        raise NotImplementedError()

    def addToBatch(self, request, callback = None):
        raise NotImplementedError()

    def addToBatchAndExecute(self, request):
        raise NotImplementedError()

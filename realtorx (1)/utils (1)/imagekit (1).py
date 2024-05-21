from imagekit.cachefiles.backends import CacheFileState, Simple


class SafeCacheFileBackend(Simple):
    def generate_now(self, file, **kwargs):
        try:
            super().generate_now(file, **kwargs)
        except OSError:
            self.set_state(file, CacheFileState.DOES_NOT_EXIST)

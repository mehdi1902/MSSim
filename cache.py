# -*- coding: utf-8 -*-

class cache():
    '''
    Cache with LRU for replacement
    '''
    def __init__(self, max_len):
        self.contents = []
        self._len = 0
        self._max_len = max_len
        self._has_cache = False
        self.cache_size = 0
        
    def get_content(self, content):
        if content in self.contents:
            self.contents = [content]+self.contents.remove(content)
        else:
            return False
        
    def has_content(self, content):
        return content in self.contents

    def set_content(self, content):
        if content not in self.contents:
            self.contents = ([content]+self.contents)[:self._max_len]
        else:
            self.get_content(content)

    def set_cache(self, cache_size):
        self.cache_size = cache_size
        self.set_cache = True
        
    def has_cache(self):
        return self._has_cache
        
    def get_cache_size(self):
        return self.cache_size
class File:
    def __init__(self, name: str, kind: str, content=None, base64=False):
        self.content = content
        self.name = name
        self.type = kind
        self.base64 = base64

    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.content)

    def open(self, path):
        with open(path, 'rb') as f:
            self.content = f.read()
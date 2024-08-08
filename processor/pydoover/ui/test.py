class A:
    type = "a"
    def __init__(self):
        pass

    def to_dict(self):
        return {"type": self.type}

class B(A):
    type = "b"


b = B()
print(b.to_dict())

c = {"a": 1, "b": 2}
c.pop("c")
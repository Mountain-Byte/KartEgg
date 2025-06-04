class Flashcard:
    def __init__(self, question, answer, group):
        self.question = question
        self.answer = answer
        self.group = group

    def to_dict(self):
        return {
            "Frage": self.question,
            "Antwort": self.answer,
            "Gruppe": self.group
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["Frage"], data["Antwort"], data["Gruppe"])
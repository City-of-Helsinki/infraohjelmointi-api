from ..models import Note, Project, Person


class NoteService:
    @staticmethod
    def create(content: str, byPerson: Person, project: Project) -> Note:
        return Note.objects.create(content=content, updatedBy=byPerson, project=project)

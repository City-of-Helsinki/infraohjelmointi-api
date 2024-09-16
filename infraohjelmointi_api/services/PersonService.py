from ..models import Person


class PersonService:
    @staticmethod
    def get_or_create_by_last_name(
        lastName: str,
    ) -> Person:
        try:
            return Person.objects.get_or_create(lastName=lastName)
        except Person.MultipleObjectsReturned:
            return (Person.objects.filter(lastName=lastName).first(), False)

    @staticmethod
    def get_or_create_by_first_name(
        firstName: str,
    ) -> Person:
        return Person.objects.get_or_create(firstName=firstName)

    @staticmethod
    def get_or_create_by_name(
        firstName: str,
        lastName: str,
    ) -> Person:
        return Person.objects.get_or_create(firstName=firstName, lastName=lastName)

    @staticmethod
    def get_or_create_by_name_and_email(
        firstName: str,
        lastName: str,
        email: str,
    ) -> Person:
        return Person.objects.get_or_create(firstName=firstName, lastName=lastName, email=email)

    @staticmethod
    def get_by_id(
        id: str,
    ) -> Person:
        return Person.objects.get(id=id)

    @staticmethod
    def get_all_persons() -> list[Person]:
        return Person.objects.all()

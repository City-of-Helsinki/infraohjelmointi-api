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
        email: str = None,
    ) -> Person:
        if email == None:
            return Person.objects.get_or_create(firstName=firstName, lastName=lastName)
        else:
            return Person.objects.get_or_create(firstName=firstName, lastName=lastName, email=email)

    @staticmethod
    def get_by_email(
        email: str
    ) -> Person:
        try:
            return Person.objects.get(email=email)
        except Person.DoesNotExist:
            return None

    @staticmethod
    def get_by_name(
        firstName: str,
        lastName: str
    ) -> Person:
        try:
            return Person.objects.get(firstName=firstName, lastName=lastName)
        except Person.MultipleObjectsReturned:
            return list(Person.objects.filter(firstName=firstName, lastName=lastName))
        except Person.DoesNotExist:
            return None

    @staticmethod
    def create_by_name(
        firstName: str,
        lastName: str,
        email: str
    ) -> Person:
        return Person.objects.create(firstName=firstName, lastName=lastName, email=email)

    @staticmethod
    def get_by_email(
        email: str
    ) -> Person:
        try:
            return Person.objects.get(email=email)
        except Person.DoesNotExist:
            return None

    @staticmethod
    def get_by_id(
        id: str,
    ) -> Person:
        return Person.objects.get(id=id)

    @staticmethod
    def get_all_persons() -> list[Person]:
        return Person.objects.all()

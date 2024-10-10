from os import path
import uuid

from django.test import TestCase
import environ
from overrides import override

from infraohjelmointi_api.models import Person
from infraohjelmointi_api.services import PersonService


if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()

import logging
logger = logging.getLogger("infraohjelmointi_api")

class ResponsiblePersonsCommandTestCase(TestCase):
    _id = "994e931e-3abd-4b8c-b376-f97d913d1877"
    _uuid = uuid.UUID(_id)
    firstname = "John"
    lastname = "Example"
    email = "john.example@example.com"

    @classmethod
    @override
    def setUpTestData(cls):
        Person.objects.create(id=cls._uuid, firstName=cls.firstname, lastName=cls.lastname, email=cls.email)

    def test_get_or_create_by_last_name(self):
        lastname = "Smith"
        
        # Create new person by lastname
        person, created = PersonService.get_or_create_by_last_name(lastName=lastname)
        self.assertTrue(created, "Created should be False when creating a new person by lastname")
        self.assertEqual(person.lastName, lastname, "The last name of the person should match the query")

        # Get existing person by lastname
        person, created = PersonService.get_or_create_by_last_name(lastName=self.lastname)
        self.assertFalse(created, "Created should be False when retrieving an existing person by lastname")
        self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")

    def test_get_or_create_by_first_name(self):
        firstname = "Eva"
        
        # Create new person by firstname
        person, created = PersonService.get_or_create_by_first_name(firstName=firstname)
        self.assertTrue(created, "Created should be False when creating a new person by firstname")
        self.assertEqual(person.firstName, firstname, "The first name of the person should match the query")

        # Get existing person by firstname
        person, created = PersonService.get_or_create_by_first_name(firstName=self.firstname)
        self.assertFalse(created, "Created should be False when retrieving an existing person by firstname")
        self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")

    def test_get_or_create_by_name(self):
        firstname1 = "Matt"
        firstname2 = "Sarah"
        lastname1 = "Kalevala"
        lastname2 = "Vainamoinen"
        email = "matt.kalevala@example.com"

        # Create new person without email
        person, created = PersonService.get_or_create_by_name(firstName=firstname1, lastName=lastname1)
        self.assertTrue(created, "Created should be False when creating a new person by first and lastname")
        self.assertEqual(person.firstName, firstname1, "The first name of the person should match the query")
        self.assertEqual(person.lastName, lastname1, "The first name of the person should match the query")

        # Create new person including email
        person, created = PersonService.get_or_create_by_name(firstName=firstname2, lastName=lastname2, email=email)
        self.assertTrue(created, "Created should be False when creating a new person by first, lastname, and email")
        self.assertEqual(person.firstName, firstname2, "The first name of the person should match the query")
        self.assertEqual(person.lastName, lastname2, "The first name of the person should match the query")
        self.assertEqual(person.email, email, "The email of the person should match the query")

        # Get existing person by name and email
        person, created = PersonService.get_or_create_by_name(firstName=self.firstname, lastName=self.lastname, email=self.email)
        self.assertFalse(created, "Created should be False when retrieving an existing person by firstname")
        self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")
        self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")
        self.assertEqual(person.email, self.email, "The email of the person should match the query")

    def test_get_by_email(self):
        emailnotfound = "email@notfound.com"

        # Get Person with email
        person, _ = PersonService.get_by_email(email=self.email)
        self.assertEqual(person.email, self.email, "The email of the person should match the query")

        # Search Person with no results
        person, _ = PersonService.get_by_email(email=emailnotfound)
        self.assertEqual(person, None, "The Person object should not be found when searching with unknown email")

    def test_get_by_name(self):
        # Get person
        person = PersonService.get_by_name(firstName=self.firstname, lastName=self.lastname)
        self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")
        self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")

        # Create duplicate Person with the same name
        Person.objects.create(firstName=self.firstname, lastName=self.lastname)
        persons = PersonService.get_by_name(firstName=self.firstname, lastName=self.lastname)
        self.assertEqual(isinstance(persons, list), True, "Returned Person should be a list of multiple Persons")
        self.assertEqual(len(persons), 2, "Returned persons list length should be 2")

        for person in persons:
            self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")
            self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")

        # Person does not exists
        person = PersonService.get_by_name(firstName="Patric", lastName="Notfound")
        self.assertEqual(person, None, "The Person object should not be found when searching with unknown email")

    def test_create_by_name(self):
        firstname = "Mark"
        lastname = "Nieminen"
        email = "mark.nieminen@example.com"

        # Create a new person
        try:
            person = PersonService.create_by_name(firstName=firstname, lastName=lastname, email=email)
        except Exception as e:
            print(e)

        # self.assertFalse(created, "Created should be False when creating a new person by first, lastname, and email")
        self.assertEqual(person.firstName, firstname, "The first name of the person should match the query")
        self.assertEqual(person.lastName, lastname, "The first name of the person should match the query")
        self.assertEqual(person.email, email, "The email of the person should match the query")

    def test_get_by_email(self):
        email = "email.not@found.fi"
        
        # Get person by email
        person = PersonService.get_by_email(email=self.email)
        self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")
        self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")
        self.assertEqual(person.email, self.email, "The email of the person should match the query")

        # Person not found
        person = PersonService.get_by_email(email=email)
        self.assertEqual(person, None, "The Person object should not be found when searching with unknown email")

    def test_get_by_id(self):
        idnotfound = "07ba0e37-61fd-4408-8f9b-6ff3ac4f333a"

        # Get person by UUID
        person = PersonService.get_by_id(id=self._id)
        self.assertEqual(person.id, self._uuid, "The UUID of the person should match the query")
        self.assertEqual(person.firstName, self.firstname, "The last name of the person should match the query")
        self.assertEqual(person.lastName, self.lastname, "The last name of the person should match the query")
        self.assertEqual(person.email, self.email, "The email of the person should match the query")

        # Person not found
        person = PersonService.get_by_id(id=idnotfound)
        self.assertEqual(person, None, "The Person object should not be found when searching with unknown email")

    def test_get_all_persons(self):
        _ = PersonService.create_by_name(firstName="Test1", lastName="Example1", email="test.example1@test.com")
        _ = PersonService.create_by_name(firstName="Test2", lastName="Example2", email="test.example2@test.com")
        _ = PersonService.create_by_name(firstName="Test3", lastName="Example3", email="test.example3@test.com")

        # Total count of person is four
        persons = PersonService.get_all_persons()
        self.assertEqual(isinstance(persons, list), True, "Returned data should be a list of multiple Persons")
        self.assertEqual(len(persons), 4, "Returned list of multiple Person should be exactly 10")


from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import ProjectProgrammer, Person, Project, ProjectClass
from infraohjelmointi_api.serializers import ProjectProgrammerSerializer
import uuid
from overrides import override
from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectProgrammerTestCase(TestCase):
    programmer_1_id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    programmer_2_id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    person_1_id = uuid.UUID("fdc89f56-b631-4109-a137-45b950de6b10")
    project_class_1_id = uuid.UUID("7c5b981e-286f-4065-9d9e-29d8d1714e4c")
    project_1_id = uuid.UUID("441d80e1-9ab1-4b35-91cc-6017ea308d87")

    @classmethod
    @override
    def setUpTestData(cls):
        # Create test person
        cls.person_1 = Person.objects.create(
            id=cls.person_1_id,
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            title="Developer",
            phone="1234567890"
        )

        # Create test programmers
        cls.programmer_1 = ProjectProgrammer.objects.create(
            id=cls.programmer_1_id,
            firstName="Alice",
            lastName="Smith",
            person=cls.person_1
        )
        cls.programmer_2 = ProjectProgrammer.objects.create(
            id=cls.programmer_2_id,
            firstName="Bob",
            lastName="Jones"
        )

        # Create test project class with default programmer
        cls.project_class_1 = ProjectClass.objects.create(
            id=cls.project_class_1_id,
            name="Test Class",
            defaultProgrammer=cls.programmer_1
        )

        # Create test project
        cls.project_1 = Project.objects.create(
            id=cls.project_1_id,
            name="Test Project",
            description="Test Description",
            projectClass=cls.project_class_1,
            personProgramming=cls.programmer_1
        )

    def test_programmer_is_created(self):
        """Test that ProjectProgrammer objects are created correctly"""
        self.assertEqual(
            ProjectProgrammer.objects.filter(id=self.programmer_1_id).exists(),
            True,
            msg="Created programmer with Id {} does not exist in DB".format(self.programmer_1_id)
        )

        programmer = ProjectProgrammer.objects.get(id=self.programmer_1_id)
        self.assertIsInstance(
            programmer,
            ProjectProgrammer,
            msg="Object retrieved from DB != typeof ProjectProgrammer"
        )
        self.assertEqual(
            programmer.firstName,
            "Alice",
            msg="Programmer firstName does not match"
        )
        self.assertEqual(
            programmer.lastName,
            "Smith",
            msg="Programmer lastName does not match"
        )
        self.assertEqual(
            programmer.person,
            self.person_1,
            msg="Programmer person relation does not match"
        )

    def test_default_programmer_in_project_class(self):
        """Test that ProjectClass can have a default programmer"""
        project_class = ProjectClass.objects.get(id=self.project_class_1_id)
        self.assertEqual(
            project_class.defaultProgrammer,
            self.programmer_1,
            msg="ProjectClass defaultProgrammer does not match"
        )

    def test_programmer_in_project(self):
        """Test that Project can have a programmer assigned"""
        project = Project.objects.get(id=self.project_1_id)
        self.assertEqual(
            project.personProgramming,
            self.programmer_1,
            msg="Project personProgramming does not match"
        )

    def test_GET_all_programmers(self):
        """Test GET request to list all programmers"""
        response = self.client.get("/project-programmers/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()),
            2,
            msg="Number of returned programmers != 2"
        )

    def test_GET_one_programmer(self):
        """Test GET request to get a single programmer"""
        response = self.client.get(
            "/project-programmers/{}/".format(self.programmer_1_id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        # Compare with serialized data
        serializer = ProjectProgrammerSerializer(
            ProjectProgrammer.objects.get(id=self.programmer_1_id),
            many=False
        )
        result_expected = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, result_expected)

    def test_cannot_POST_programmer(self):
        """Test that POST requests are not allowed (read-only viewset)"""
        data = {
            "firstName": "Charlie",
            "lastName": "Brown"
        }
        response = self.client.post(
            "/project-programmers/",
            data,
            content_type="application/json"
        )
        self.assertEqual(
            response.status_code,
            405,
            msg="POST request should not be allowed"
        )

    def test_cannot_PATCH_programmer(self):
        """Test that PATCH requests are not allowed (read-only viewset)"""
        data = {
            "firstName": "Updated Name"
        }
        response = self.client.patch(
            "/project-programmers/{}/".format(self.programmer_1_id),
            data,
            content_type="application/json"
        )
        self.assertEqual(
            response.status_code,
            405,
            msg="PATCH request should not be allowed"
        )

    def test_cannot_DELETE_programmer(self):
        """Test that DELETE requests are not allowed (read-only viewset)"""
        response = self.client.delete(
            "/project-programmers/{}/".format(self.programmer_1_id)
        )
        self.assertEqual(
            response.status_code,
            405,
            msg="DELETE request should not be allowed"
        )

class ProjectPersonAuthorizationService:
    @staticmethod
    def is_matching_project_person_email(user, person):
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if not person:
            return False

        user_email = (getattr(user, "email", "") or "").strip().lower()
        person_email = (getattr(person, "email", "") or "").strip().lower()
        if not user_email or not person_email:
            return False

        return user_email == person_email

    @classmethod
    def is_person_planning_for_project(cls, user, project):
        project_person_planning = getattr(project, "personPlanning", None)
        return cls.is_matching_project_person_email(user, project_person_planning)

    @classmethod
    def is_person_construction_for_project(cls, user, project):
        project_person_construction = getattr(project, "personConstruction", None)
        return cls.is_matching_project_person_email(user, project_person_construction)

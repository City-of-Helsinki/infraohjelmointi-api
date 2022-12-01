from .models import *
import uuid


class DataGen:
    projectId = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    projectId2 = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    budgetItemId = uuid.UUID("5b1b127f-b4c4-4bea-b994-b2c5c04332f8")
    person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    person_2_Id = uuid.UUID("7fe92cae-d866-4e12-b182-547c367efe12")
    person_3_Id = uuid.UUID("b56ae8c8-f5c2-4abe-a1a6-f3a83265ff49")
    person_4_Id = uuid.UUID("f627e782-81de-4c37-b1f7-ef4c26eeeb99")
    projectSetId = uuid.UUID("fb093e0e-0b35-4b0e-94d7-97c91997f2d0")
    projectAreaId = uuid.UUID("9acb1ac2-259e-4300-8cf0-f89c3adaf577")
    projectPhaseId = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectPhaseId2 = uuid.UUID("d72a6737-3739-475f-8350-da9151d33fa0")
    projectPhaseId3 = uuid.UUID("6b2c8795-e21c-4060-b5f8-1bdead45e1ec")
    projectTypeId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectPriorityId = uuid.UUID("e7f471fb-6eac-4688-aa9b-908b0194a5dc")
    sapNetworkIds_1 = [uuid.UUID("1495aaf7-b0af-4847-a73b-7650145a73dc").__str__()]
    sapProjectIds_1 = [uuid.UUID("e6f0805c-0b20-4248-bfae-21cf6bfe744a").__str__()]
    sapNetworkIds_2 = [uuid.UUID("1c97fff1-e386-4e43-adc5-131af3cd9e37").__str__()]
    sapProjectIds_2 = [uuid.UUID("2cee5e12-eda9-499c-8a3f-f17b2b0b1a98").__str__()]
    noteId = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    taskId = uuid.UUID("580f2efb-63ae-46e8-b6d0-e0e306a0e5bb")
    taskStatusId = uuid.UUID("32fd48c8-c800-47c4-af4f-2038ebeb0a0b")

    @classmethod
    def mkBudgetItem(
        self,
        id=None,
        budgetMain=10000,
        budgetPlan=10000,
        site="Helsinki",
        siteName="Anankatu",
        disctrict="Random",
        need=5000,
    ):

        if id == None:
            return BudgetItem.objects.create(
                id=self.budgetItemId,
                budgetMain=budgetMain,
                budgetPlan=budgetPlan,
                site=site,
                siteName=siteName,
                district=disctrict,
                need=need,
            )

        return BudgetItem.objects.create(
            id=id,
            budgetMain=budgetMain,
            budgetPlan=budgetPlan,
            site=site,
            siteName=siteName,
            district=disctrict,
            need=need,
        )

    @classmethod
    def mkPerson(
        self,
        id=None,
        firstName="John",
        lastName="Doe",
        email="random@random.com",
        title="Manager",
        phone="0414853277",
    ):
        if id == None:
            return Person.objects.create(
                id=self.person_1_Id,
                firstName=firstName,
                lastName=lastName,
                email=email,
                title=title,
                phone=phone,
            )
        return Person.objects.create(
            id=id,
            firstName=firstName,
            lastName=lastName,
            email=email,
            title=title,
            phone=phone,
        )

    @classmethod
    def mkProjectPhase(self, id=None, value="Proposal"):
        if id == None:
            return ProjectPhase.objects.create(id=self.projectPhaseId, value=value)
        return ProjectPhase.objects.create(id=id, value=value)

    @classmethod
    def mkProjectSet(
        self,
        id=None,
        name="Test Project Set",
        hkrId=1234,
        description="This is test project set",
        responsiblePerson=None,
        phase=None,
        programmed=False,
    ):
        projectSet = None
        if id == None:
            projectSet = ProjectSet.objects.create(
                id=self.projectSetId,
                name=name,
                hkrId=hkrId,
                description=description,
                responsiblePerson=responsiblePerson,
                phase=phase,
                programmed=programmed,
            )
        else:
            projectSet = ProjectSet.objects.create(
                id=id,
                name=name,
                hkrId=hkrId,
                description=description,
                responsiblePerson=responsiblePerson,
                phase=phase,
                programmed=programmed,
            )

        return projectSet

    @classmethod
    def mkProjectArea(self, id=None, value="honkasuo", location="Helsinki"):
        if id == None:
            return ProjectArea.objects.create(
                id=self.projectAreaId,
                value=value,
                location=location,
            )
        return ProjectArea.objects.create(
            id=id,
            value=value,
            location=location,
        )

    @classmethod
    def mkProjectType(self, id=None, value="projectComplex"):
        if id == None:
            return ProjectType.objects.create(id=self.projectTypeId, value=value)
        return ProjectType.objects.create(id=id, value=value)

    @classmethod
    def mkProjectPriority(self, id=None, value="high"):
        if id == None:
            return ProjectPriority.objects.create(
                id=self.projectPriorityId, value=value
            )
        return ProjectPriority.objects.create(id=id, value=value)

    @classmethod
    def mkProject(
        self,
        minimal=False,
        id=None,
        siteId=None,
        hkrId=12345,
        sapProject=sapProjectIds_1,
        sapNetwork=sapNetworkIds_1,
        projectSet=None,
        entityName="Sample Entity",
        area=None,
        prType=None,
        name="Test Project",
        description="Test project description",
        personPlanning=None,
        personProgramming=None,
        personConstruction=None,
        phase=None,
        programmed=True,
        constructionPhaseDetail="detail description",
        estPlanningStartYear=2022,
        estDesignEndYear=2023,
        estDesignStartDate="2022-11-20",
        estDesignEndDate="2022-11-28",
        contractPrepStartDate="2022-11-20",
        contractPrepEndDate="2022-11-20",
        warrantyStartDate="2022-11-20",
        warrantyExpireDate="2022-11-20",
        perfAmount=20000.00,
        unitCost=10000.00,
        costForecast=10000.00,
        neighborhood="my random neigbhorhood",
        comittedCost=120.0,
        tiedCurrYear=12000.00,
        realizedCost=20.00,
        spentCost=20000.00,
        riskAssess="Yes very risky test",
        priority=None,
        locked=True,
        comments="Comments random",
        delays="yes 1 delay because of tests",
        hashTags=["#random", "#random2"],
        budgetForecast1CurrentYear=None,
        budgetForecast2CurrentYear=None,
        budgetForecast3CurrentYear=None,
        budgetForecast4CurrentYear=None,
        budgetProposalCurrentYearPlus1=None,
        budgetProposalCurrentYearPlus2=None,
        preliminaryCurrentYearPlus3=None,
        preliminaryCurrentYearPlus4=None,
        preliminaryCurrentYearPlus5=None,
        preliminaryCurrentYearPlus6=None,
        preliminaryCurrentYearPlus7=None,
        preliminaryCurrentYearPlus8=None,
        preliminaryCurrentYearPlus9=None,
        preliminaryCurrentYearPlus10=None,
    ):
        project = None
        if id == None:
            project = Project.objects.create(
                id=self.projectId,
                siteId=siteId,
                hkrId=hkrId,
                sapProject=sapProject,
                sapNetwork=sapNetwork,
                projectSet=projectSet,
                entityName=entityName,
                area=area,
                type=prType,
                name=name,
                description=description,
                personPlanning=personPlanning,
                personProgramming=personProgramming,
                personConstruction=personConstruction,
                phase=phase,
                programmed=programmed,
                constructionPhaseDetail=constructionPhaseDetail,
                estPlanningStartYear=estPlanningStartYear,
                estDesignEndYear=estDesignEndYear,
                estDesignStartDate=estDesignStartDate,
                estDesignEndDate=estDesignEndDate,
                contractPrepStartDate=contractPrepStartDate,
                contractPrepEndDate=contractPrepEndDate,
                warrantyStartDate=warrantyStartDate,
                warrantyExpireDate=warrantyExpireDate,
                perfAmount=perfAmount,
                unitCost=unitCost,
                costForecast=costForecast,
                neighborhood=neighborhood,
                comittedCost=comittedCost,
                tiedCurrYear=tiedCurrYear,
                realizedCost=realizedCost,
                spentCost=spentCost,
                riskAssess=riskAssess,
                priority=priority,
                locked=locked,
                comments=comments,
                delays=delays,
                hashTags=hashTags,
                budgetForecast1CurrentYear=budgetForecast1CurrentYear,
                budgetForecast2CurrentYear=budgetForecast2CurrentYear,
                budgetForecast3CurrentYear=budgetForecast3CurrentYear,
                budgetForecast4CurrentYear=budgetForecast4CurrentYear,
                budgetProposalCurrentYearPlus1=budgetProposalCurrentYearPlus1,
                budgetProposalCurrentYearPlus2=budgetProposalCurrentYearPlus2,
                preliminaryCurrentYearPlus3=preliminaryCurrentYearPlus3,
                preliminaryCurrentYearPlus4=preliminaryCurrentYearPlus4,
                preliminaryCurrentYearPlus5=preliminaryCurrentYearPlus5,
                preliminaryCurrentYearPlus6=preliminaryCurrentYearPlus6,
                preliminaryCurrentYearPlus7=preliminaryCurrentYearPlus7,
                preliminaryCurrentYearPlus8=preliminaryCurrentYearPlus8,
                preliminaryCurrentYearPlus9=preliminaryCurrentYearPlus9,
                preliminaryCurrentYearPlus10=preliminaryCurrentYearPlus10,
            )
        else:
            project = Project.objects.create(
                id=id,
                siteId=siteId,
                hkrId=hkrId,
                sapProject=sapProject,
                sapNetwork=sapNetwork,
                projectSet=projectSet,
                entityName=entityName,
                area=area,
                type=prType,
                name=name,
                description=description,
                personPlanning=personPlanning,
                personProgramming=personProgramming,
                personConstruction=personConstruction,
                phase=phase,
                programmed=programmed,
                constructionPhaseDetail=constructionPhaseDetail,
                estPlanningStartYear=estPlanningStartYear,
                estDesignEndYear=estDesignEndYear,
                estDesignStartDate=estDesignStartDate,
                estDesignEndDate=estDesignEndDate,
                contractPrepStartDate=contractPrepStartDate,
                contractPrepEndDate=contractPrepEndDate,
                warrantyStartDate=warrantyStartDate,
                warrantyExpireDate=warrantyExpireDate,
                perfAmount=perfAmount,
                unitCost=unitCost,
                costForecast=costForecast,
                neighborhood=neighborhood,
                comittedCost=comittedCost,
                tiedCurrYear=tiedCurrYear,
                realizedCost=realizedCost,
                spentCost=spentCost,
                riskAssess=riskAssess,
                priority=priority,
                locked=locked,
                comments=comments,
                delays=delays,
                hashTags=hashTags,
                budgetForecast1CurrentYear=budgetForecast1CurrentYear,
                budgetForecast2CurrentYear=budgetForecast2CurrentYear,
                budgetForecast3CurrentYear=budgetForecast3CurrentYear,
                budgetForecast4CurrentYear=budgetForecast4CurrentYear,
                budgetProposalCurrentYearPlus1=budgetProposalCurrentYearPlus1,
                budgetProposalCurrentYearPlus2=budgetProposalCurrentYearPlus2,
                preliminaryCurrentYearPlus3=preliminaryCurrentYearPlus3,
                preliminaryCurrentYearPlus4=preliminaryCurrentYearPlus4,
                preliminaryCurrentYearPlus5=preliminaryCurrentYearPlus5,
                preliminaryCurrentYearPlus6=preliminaryCurrentYearPlus6,
                preliminaryCurrentYearPlus7=preliminaryCurrentYearPlus7,
                preliminaryCurrentYearPlus8=preliminaryCurrentYearPlus8,
                preliminaryCurrentYearPlus9=preliminaryCurrentYearPlus9,
                preliminaryCurrentYearPlus10=preliminaryCurrentYearPlus10,
            )

        return project

    @classmethod
    def mkNote(
        self,
        id=None,
        content="Test note",
        updatedBy=None,
        project=None,
    ):
        if updatedBy == None or project == None:
            raise ValueError("Fields updatedBy and project cannot be None")
        if id == None:
            return Note.objects.create(
                id=self.noteId,
                content=content,
                updatedBy=updatedBy,
                project=project,
            )
        return Note.objects.create(
            id=id,
            content=content,
            updatedBy=updatedBy,
            project=project,
        )

    @classmethod
    def mkTaskStatus(self, id=None, value="active"):
        if id == None:
            return TaskStatus.objects.create(id=self.taskStatusId, value=value)
        return TaskStatus.objects.create(id=id, value=value)

    @classmethod
    def mkTask(
        self,
        id=None,
        projectId=None,
        hkrId=12345,
        taskType="sample type",
        status=None,
        startDate="2022-11-20",
        endDate="2022-11-20",
        person=None,
        realizedCost=10000,
        plannedCost=10000,
        riskAssess="Risky",
    ):
        task = None
        if projectId == None:
            raise ValueError("Field projectId cannot be None")
        if id == None:
            task = Task.objects.create(
                id=self.taskId,
                projectId=projectId,
                hkrId=hkrId,
                taskType=taskType,
                status=status,
                startDate=startDate,
                endDate=endDate,
                person=person,
                realizedCost=realizedCost,
                plannedCost=plannedCost,
                riskAssess=riskAssess,
            )
        else:

            task = Task.objects.create(
                id=id,
                projectId=projectId,
                hkrId=hkrId,
                taskType=taskType,
                status=status,
                startDate=startDate,
                endDate=endDate,
                person=person,
                realizedCost=realizedCost,
                plannedCost=plannedCost,
                riskAssess=riskAssess,
            )

        return task

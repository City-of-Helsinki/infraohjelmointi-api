from django.db import transaction

import traceback
import re

from ....models import (
    Project,
    ProjectClass,
    ProjectLocation,
    ProjectType,
    ProjectPhase,
    Person,
    ConstructionPhaseDetail,
    ProjectArea,
    ResponsibleZone,
)


def populateProjectClassesWithPWData(session, pw_api_url, stdout, style):
    stdout.write(style.NOTICE("Retrieving classes from PW"))
    response = session.get(
        pw_api_url + "Env_118_HKR_Hankerek_Arvoj?$filter=ROOLI+eq+'ProjLuokat'"
    )

    buildClassOrLocationHierarchy(
        response=response, model_class=ProjectClass, stdout=stdout, style=style
    )
    stdout.write(style.NOTICE("Retrieving classes from PW done"))


def populateProjectLocationsWithPWData(session, pw_api_url, stdout, style):
    stdout.write(style.NOTICE("Retrieving locations from PW"))
    response = session.get(
        pw_api_url + "Env_118_HKR_Hankerek_Arvoj?$filter=ROOLI+eq+'Aluejaot'"
    )

    buildClassOrLocationHierarchy(
        response=response, model_class=ProjectLocation, stdout=stdout, style=style
    )
    stdout.write(style.NOTICE("Retrieving locations from PW done"))


def buildClassOrLocationHierarchy(response, model_class, stdout, style):
    # Check if PW responded with error
    if response.status_code != 200:
        stdout.write(style.ERROR(response.json()))
        return

    # Iterate the result received from PW
    for model_data in response.json()["instances"]:
        model_data = model_data["properties"]

        try:
            master_model, _ = model_class.objects.get_or_create(
                name=model_data["PAALUOKKA"].strip(),
                parent=None,
                path=model_data["PAALUOKKA"].strip(),
            )
            master_model.save()
        except Exception as e:
            stdout.write(
                style.ERROR(
                    "Error occurred while handling master model '{}'. Error: {}".format(
                        model_data["PAALUOKKA"], e
                    )
                )
            )

        if model_data["LUOKKA"]:
            try:
                model, _ = model_class.objects.get_or_create(
                    name=model_data["LUOKKA"].strip(),
                    parent=master_model,
                    path="{}/{}".format(
                        model_data["PAALUOKKA"].strip(),
                        model_data["LUOKKA"].strip(),
                    ).rstrip("/"),
                )
                model.save()
            except Exception as e:
                stdout.write(
                    style.ERROR(
                        "Error occurred while handling model '{}'. Error: {}".format(
                            model_data["LUOKKA"], e
                        )
                    )
                )

        if model_data["ALALUOKKA"]:
            try:
                submodel, _ = model_class.objects.get_or_create(
                    name=model_data["ALALUOKKA"].strip(),
                    parent=model,
                    path="{}/{}/{}".format(
                        model_data["PAALUOKKA"].strip(),
                        model_data["LUOKKA"].strip(),
                        model_data["ALALUOKKA"].strip(),
                    ).rstrip("/"),
                )
                submodel.save()
            except Exception as e:
                stdout.write(
                    style.ERROR(
                        "Error occurred while handling sub model '{}'. Error: {}".format(
                            model_data["ALALUOKKA"], e
                        )
                    )
                )
        stdout.write(
            style.NOTICE(
                "Handled '{}/{}/{}'".format(
                    model_data["PAALUOKKA"].strip(),
                    model_data["LUOKKA"].strip(),
                    model_data["ALALUOKKA"].strip(),
                ).rstrip("/")
            )
        )


def loadAndTransformPhases():
    phase_map = {
        "proposal": "1. Hanke-ehdotus",
        "design": "1.5 Yleissuunnittelu",
        "programming": "2. Ohjelmointi",
        "draftInitiation": "3. Suunnittelun aloitus / Suunnitelmaluonnos",
        "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
        "constructionPlan": "5. Rakennussuunnitelma",
        "constructionWait": "6. Odottaa rakentamista",
        "construction": "7. Rakentaminen",
        "warrantyPeriod": "8. Takuuaika",
        "completed": "9. Valmis / ylläpidossa",
    }
    return {phase_map[pph.value]: pph for pph in ProjectPhase.objects.all()}


def loadAndTransformProjectTypes():
    pt_map = {
        "projectComplex": "hankekokonaisuus",
        "street": "katu",
        "cityRenewal": "kaupunkiuudistus",
        "traffic": "liikenne",
        "sports": "liikunta",
        "omaStadi": "OmaStadi-hanke",
        "projectArea": "projektialue",
        "park": "puisto",
        "bigTrafficProjects": "suuret liikennehankeet",
        "spesialtyStructures": "taitorakenne",
    }
    return {pt_map[pt.value]: pt for pt in ProjectType.objects.all()}


def loadAndTransformConstructionPhaseDetails():
    pd_map = {
        "preConstruction": "1. Esirakentaminen",
        "firstPhase": "2. Ensimmäinen vaihe",
        "firstPhaseComplete": "3. Ensimmäinen vaihe valmis",
        "secondPhase": "4. Toinen vaihe / viimeistely",
    }

    return {pd_map[pd.value]: pd for pd in ConstructionPhaseDetail.objects.all()}


def loadAndTransformProjectAreas():
    pa_map = {
        "honkasuo": "Honkasuo",
        "kalasatama": "Kalasatama",
        "kruunuvuorenranta": "Kruunuvuorenranta",
        "kuninkaantammi": "Kuninkaantammi",
        "lansisatama": "Länsisatama",
        "malminLentokenttaalue": "Malmin lentokenttäalue",
        "pasila": "Pasila",
        "ostersundom": "Östersundom",
    }

    return {pa_map[pa.value]: pa for pa in ProjectArea.objects.all()}


def loadAndTransformResponsibleZones():
    rz_map = {
        "east": "Itä",
        "west": "Länsi",
        "north": "Pohjoinen",
    }

    return {rz_map[rz.value]: rz for rz in ResponsibleZone.objects.all()}


def getProjectPerson(person_data: str, stdout, style) -> Person:
    person_data = person_data.strip().replace(", ", ",")
    stdout.write(style.NOTICE("Handling person data: '{}'".format(person_data)))
    if not person_data.rstrip(","):
        return None
    try:
        full_name, title, phone_nr, email = person_data.split(",")
        last_name, first_name = re.split("(?<=.)(?<!\-)(?=[A-Z])", full_name)
        person, _ = Person.objects.get_or_create(
            firstName=first_name.strip().title(), lastName=last_name.strip().title()
        )

        if title:
            person.title = title.strip().title()
        if phone_nr:
            person.phone = phone_nr.strip()
        if email:
            person.email = email.strip()

        person.save()

        return person
    except Exception as e:
        stdout.write(
            style.ERROR(
                "Error occurred while handling person data. Error: {}".format(e)
            )
        )
        return None


def getFavPersons(person_data: str, stdout, style) -> list[Person]:
    person_data = person_data.strip().replace(", ", ",").rstrip(",")
    stdout.write(style.NOTICE("Handling fav person data: '{}'".format(person_data)))
    if not person_data:
        return None
    fav_persons = []
    # Firstname Lastname, Title, phone, email format
    if re.findall(
        "^[a-zA-ZäöåÄÖÅ]+ [a-zA-ZäöåÄÖÅ]+,[a-zA-ZäöåÄÖ\. ]+,[a-zA-ZäöåÄÖÅ0-9\. ]+,[a-zA-ZäöåÄÖÅ@\.]+$",
        person_data,
    ):
        fav_persons.append(
            getProjectPerson(
                person_data=person_data,
                stdout=stdout,
                style=style,
            )
        )
        return fav_persons

    for person in person_data.split(","):
        # FirstnameLastname or Firstname Lastname
        fav_person_data = re.split("(?<=.)(?=[A-Z])", person)
        if len(fav_person_data) == 1:
            # email format?
            fav_person_data = re.split("\\.|@", person)
        if len(fav_person_data) == 1:
            # just one string so add an empty value to list
            fav_person_data.append(" ")

        fav_person = getProjectPerson(
            fav_person_data[1] + " " + fav_person_data[0] + ",,,",
            stdout=stdout,
            style=style,
        )
        if fav_person:
            fav_persons.append(fav_person)
    return fav_persons


@transaction.atomic
def proceedWithPWArgument(session, env, stdout, style):

    session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
    pw_api_url = env("PW_API_URL")

    # import classes from PW into DB
    populateProjectClassesWithPWData(
        session=session, pw_api_url=pw_api_url, stdout=stdout, style=style
    )
    # import locations from PW into DB
    populateProjectLocationsWithPWData(
        session=session, pw_api_url=pw_api_url, stdout=stdout, style=style
    )

    # load classes from DB
    project_classes = ProjectClass.objects.all()
    master_classes = filter(lambda _class: _class.parent == None, project_classes)

    project_phases = loadAndTransformPhases()
    project_types = loadAndTransformProjectTypes()
    construction_phase_details = loadAndTransformConstructionPhaseDetails()
    project_areas = loadAndTransformProjectAreas()
    responsible_zones = loadAndTransformResponsibleZones()

    for master_class in master_classes:
        projects = queryPWProjectsWithMasterClass(
            masterClass=master_class.name,
            session=session,
            pw_api_url=pw_api_url,
            stdout=stdout,
            style=style,
        )

        if projects == None:
            continue

        for project in projects:
            project_properties = project["properties"]
            name = " ".join(project_properties["PROJECT_Kohde"].split())
            description = (
                " ".join(project_properties["PROJECT_Hankkeen_kuvaus"].split())
                if project_properties["PROJECT_Hankkeen_kuvaus"]
                else "Kuvaus puuttuu"
            )
            try:
                try:
                    project_object = Project.objects.get(name=name)
                except Project.DoesNotExist as e:
                    project_object = Project.objects.create(
                        name=name, description=description
                    )

                if description != "Kuvaus puuttuu" or description != "":
                    project_object.description = description

                if project_properties["PROJECT_Kadun_tai_puiston_nimi"]:
                    project_object.address = project_properties[
                        "PROJECT_Kadun_tai_puiston_nimi"
                    ]

                if project_properties["PROJECT_Hankkeen_vaihe"]:
                    project_object.phase = project_phases[
                        project_properties["PROJECT_Hankkeen_vaihe"]
                    ]

                if project_properties["PROJECT_HKRHanketunnus"]:
                    project_object.hkrId = project_properties["PROJECT_HKRHanketunnus"]

                if project_properties["PROJECT_Louheen"]:
                    project_object.louhi = project_properties["PROJECT_Louheen"] != "Ei"

                if project_properties["PROJECT_Sorakatu"]:
                    project_object.gravel = (
                        project_properties["PROJECT_Sorakatu"] != "Ei"
                    )

                if project_properties["PROJECT_Projektialue"]:
                    project_object.area = project_areas[
                        project_properties["PROJECT_Projektialue"]
                    ]

                if project_properties["PROJECT_Aluekokonaisuuden_nimi"]:
                    project_object.entityName = project_properties[
                        "PROJECT_Aluekokonaisuuden_nimi"
                    ]

                if project_properties["PROJECT_Ohjelmoitu"]:
                    project_object.programmed = (
                        project_properties["PROJECT_Ohjelmoitu"] != "Ei"
                    )

                if project_properties["PROJECT_Rakentamisvaiheen_tarkenne"]:
                    project_object.constructionPhaseDetail = construction_phase_details[
                        project_properties["PROJECT_Rakentamisvaiheen_tarkenne"]
                    ]

                if project_properties["PROJECT_Toimiala"]:
                    project_object.type = project_types[
                        project_properties["PROJECT_Toimiala"]
                    ]

                class_path = "{}/{}/{}".format(
                    project_properties["PROJECT_Pluokka"],
                    project_properties["PROJECT_Luokka"],
                    project_properties["PROJECT_Alaluokka"],
                ).rstrip("/")
                try:
                    project_object.projectClass = ProjectClass.objects.get(
                        path=class_path
                    )
                except ProjectClass.DoesNotExist:
                    stdout.write(
                        style.ERROR(
                            "Class '{}' not found from DB for hkr id {}".format(
                                class_path,
                                project_properties["PROJECT_HKRHanketunnus"],
                            )
                        )
                    )

                location_path = "{}/{}/{}".format(
                    project_properties["PROJECT_Suurpiirin_nimi"],
                    project_properties["PROJECT_Kaupunginosan_nimi"],
                    project_properties["PROJECT_Osa_alue"],
                ).rstrip("/")
                try:
                    project_object.projectLocation = ProjectLocation.objects.get(
                        path=location_path
                    )
                except ProjectLocation.DoesNotExist:
                    stdout.write(
                        style.ERROR(
                            "Location '{}' not found from DB for hkr id {}".format(
                                location_path,
                                project_properties["PROJECT_HKRHanketunnus"],
                            )
                        )
                    )

                if project_properties[
                    "PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"
                ]:
                    project_object.responsibleZone = responsible_zones[
                        project_properties[
                            "PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"
                        ]
                    ]

                if project_properties["PROJECT_Louhi__hankkeen_aloitusvuosi"]:
                    project_object.planningStartYear = project_properties[
                        "PROJECT_Louhi__hankkeen_aloitusvuosi"
                    ]

                if project_properties["PROJECT_Louhi__hankkeen_valmistumisvuosi"]:
                    project_object.constructionEndYear = project_properties[
                        "PROJECT_Louhi__hankkeen_valmistumisvuosi"
                    ]
                planning_person_data = "{}, {}, {}, {}".format(
                    project_properties["PROJECT_Vastuuhenkil"],
                    project_properties["PROJECT_Vastuuhenkiln_titteli"],
                    project_properties["PROJECT_Vastuuhenkiln_puhelinnumero"],
                    project_properties["PROJECT_Vastuuhenkiln_shkpostiosoite"],
                )

                planning_person = getProjectPerson(
                    person_data=planning_person_data, stdout=stdout, style=style
                )
                if planning_person:
                    project_object.personPlanning = planning_person

                if project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"]:
                    construction_person = getProjectPerson(
                        person_data=project_properties[
                            "PROJECT_Vastuuhenkil_rakennuttaminen"
                        ],
                        stdout=stdout,
                        style=style,
                    )

                    if construction_person:
                        project_object.personConstruction = construction_person

                if project_properties["PROJECT_Muut_vastuuhenkilt"]:
                    project_object.favPersons.set(
                        getFavPersons(
                            project_properties["PROJECT_Muut_vastuuhenkilt"],
                            stdout=stdout,
                            style=style,
                        )
                    )

                project_object.save()
                stdout.write(
                    style.SUCCESS(
                        "Project '{}' successfully imported to DB".format(name)
                    )
                )
            except Exception as e:
                stdout.write(
                    style.ERROR(
                        "Error occurred while handling project '{}' ({}). Error: {}".format(
                            name, project_properties["PROJECT_HKRHanketunnus"], e
                        )
                    )
                )
                traceback.print_exc()
                exit(e)


def queryPWProjectsWithMasterClass(masterClass, session, pw_api_url, stdout, style):

    response = session.get(
        pw_api_url
        + "PrType_1121_HKR_Hankerek_Hanke?$filter=PROJECT_Pluokka+eq+'{}'".format(
            masterClass
        )
    )

    # Check if PW responded with error
    if response.status_code != 200:
        stdout.write(style.ERROR(response.json()))
        return None
    # Check if the project exists on PW
    if len(response.json()["instances"]) == 0:
        stdout.write(
            style.ERROR(
                "No result received from PW for master class {}".format(masterClass)
            )
        )
        return None

    return response.json()["instances"]

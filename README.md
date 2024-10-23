# Infraohjelmointi API

Backend repository for infraohjelmointi API service in City of Helsinki.

Instructions in this README.md assume that you know  what __docker__ and __docker-compose__ are, and you already have both installed locally. Also you understand what __docker-compose up -d__ means.
This helps to keep the README.md concise.

### Ways of working
##### Commits

To make our commits more informative those should be written in a format of Conventional Commits i.e. a suitable prefix should be added in the beginning
of every commit e.g. **feat:** built a notification or **refactor**:... etc. The Conventional Commits could be properly configured to the project in the future.

##### Hotfixes

Hotfixes should be done by creating a hotfix branch out of main and then merge that to main and develop to avoid doing any rebases.

##### Merges

The common way of merging branches is using normal merges i.e. not using squash merging unless there is a situation when squashing should be done.

## Setting up local development environment with Docker

In order to create placeholder for your own environment variables file, make a local `.env.template` copy:

```bash
cp .env.template .env
```

Then you can run docker image as detached mode with:

  ```bash
  docker-compose up
  ```

- Access development server on [localhost:8000](http://localhost:8000)

- Login to admin interface with `admin` and 🥥 at [localhost:8000/admin](http://localhost:8000/admin)

- Done!

## What next?

This list is a 'TL;DR'. Steps are described more detailed on this README file under [Populate database](#populate-database).

- [Hierarchy and project data](#hierarchy-and-project-data)
  - Import Location/Class hierarchy structure
  - Import Planning (TS) and Budget (TAE) files in bulk together
- [Populate database](#populate-database)
  - [Import project location options](#import-project-location-options)
  - [Update missing projectDistrict data](#update-missing-projectdistrict-data)

## Populate database

### Hierarchy and project data

Project data and finances can be imported using excel files into the infra tool.

When importing, you need to run scripts in the container:
  ```bash
  docker exec -it infraohjelmointi-api sh
  ```

Importing Location/Class hierarchy structure and Planning (TS) and Budget (TAE) files:

- Location/Class hierarchy structure
  ```bash
  ./import-excels.sh -c path/to/hierarchy.xlsx
  ```

- Planning and Budget files (e.g. in `Excels` folder):
  ```bash
  ./import-excels.sh -d path/to/Excels/
  ```


### Import project location options

Import project location options:

  ```bash
  python manage.py locationimporter --file path/to/locationdata.xlsx
  ```

### Update missing projectDistrict data

Update projects' missing `projectDistrict_id` value with `infraohjelmointi_api_projectdistrict.id`.

  ```bash
  psql $DATABASE_URL
  \i update-districts.sql
  ```

## Other optional file imports

### Import new persons

Import new person information into responsible persons list. The list can be found from project form:

  ```bash
  python manage.py responsiblepersons --file path/to/filename.xlsx
  ```
  

---

## Add or delete API token

Add new API token:

  ```bash
  python manage.py generatetoken --name AppNameToken
  ```

This creates a new User which name is `--name` value.

Delete API token:

  ```bash
  python manage.py generatetoken --name ExistingAPITokenName --deletetoken
  ```

## Managing project packages

- We use `pip` to manage python packages we need
- After adding a new package to requirements.txt file, compile it and re-build the Docker image so that the container would have access to the new package

  ```bash
  docker-compose up --build
  ```

## Running tests

Tests are written for django management commands and the endpoints. They can be found in the following location:

  ```bash
  infraohjelmointi_api/tests
  ```
Run the tests

  ```bash
  python manage.py test
  ```
An optional verbosity parameter can be added to get a more descriptive view of the tests

  ```bash
  python manage.py test -v 1/2/3
  ```

## Test coverage

The codebase should always have a test coverage % higher than 65%. It is usualy measured with SonarCloud in the PR pipeline, but if needed to get
the % locally, a report can be created with pytest-cov.

1. If not installed inside the container, you need to install pytest-django and pytest-cov
    ```bash
    pip install pytest-django
    pip install pytest-cov
    ```

2. Run
    ```bash
    pytest --cov=infraohjelmointi_api/
    ```
    to get the test coverage report from the whole project. You can also specify folders or files by changing the value given to `--cov=`

## External data sources

Infra tool project data and financial data can be imported from external sources.

### SAP

To synchronize project data with SAP in local environment, VPN service provided by platta should be running.

Populate DB with SAP costs and commitments using management command:

  ```bash
  python manage.py sapsynchronizer
  ```
All projects in DB will also be synced with SAP to update SAP costs and commitments at midnight through the CRON job and script:

  ```bash
  ./sync-from-sap.sh
  ```

The CRON job is added on both prod and dev environments.

More documentation on [Confluence](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/IO/pages/8131444804/Infraohjelmointi+API+-sovellus#SAP-integraatio).

### ProjectWise

Sync all project data in the DB with ProjectWise:

  ```bash
  python manage.py projectimporter --sync-projects-with-pw
  ```

Sync project by PW id in the DB with ProjectWise

  ```bash
  python manage.py projectimporter --sync-project-from-pw pw_id
  ```

Projects are also synced to PW service when a PATCH request is made to the projecs endpoint.

Scripts were used when dev and prod environments were setup for the first time.

More documentation on [Confluence](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/IO/pages/8131444804/Infraohjelmointi+API+-sovellus#Project-Wise--integraatio).

## Other optional import scripts

While populating the database the script file `import-excels.sh` was used to create the hierarchy (`/import-excels.sh -c path/to/hierarchy.xlsx`) and importing all Excels (`./import-excels.sh -d path/to/Excels/`).

Import Location/Class hierarchy structure. File `import-excels.sh` uses this:

  ```bash
  python manage.py hierarchies --file path/to/hierarchy.xlsx
  ```

_In some contexts, hierarchy is known as "luokkajako"._

<br>

Import only Planning project data (files with "TS"):

  ```bash
  python manage.py  projectimporter --import-from-plan path/to/planningFile.xlsx
  ```

Import only Budget project data (files with "TAE"):

  ```bash
  python manage.py  projectimporter --import-from-budget path/to/budgetFile.xlsx
  ```

_`./import-excels.sh -d path/to/Excels` includes both of TS and TAE import commands._

## Production release

1. Create a release PR from develop to main
2. Wait for the PR pipeline to run and check that all checks pass
3. Merge the PR
4. Trigger build-infraohjelmointi-api-stageprod
5. Approve pipeline run in [Azure DevOps](https://dev.azure.com/City-of-Helsinki/infraohjelmointi/_build/). Deploy pipelines are triggered by the build pipeline but prod deploy needs to be approved separately (=2 approvals in total). To approve:
    1. Open the pipeline run you want to approve (from left menu, select Pipelines)
    2. Select the correct pipeline
    3. Select the run you need to approve
    4. Wait and click a button to approve it (pipeline run is paused until you approve).

<hr>

- Steps on Confluence with pictures: [Confluence](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/IO/pages/8131444804/Infraohjelmointi+API+-sovellus#Tuotantoonvienti)
- Link to Azure DevOps services: [Azure DevOps](https://dev.azure.com/City-of-Helsinki/infraohjelmointi/_build/)

## Technical documentation

Technical documentation can be found from [Confluence](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/IO/pages/7895089196/Tekninen+dokumentaatio).

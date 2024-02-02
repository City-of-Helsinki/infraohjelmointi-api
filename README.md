# Infraohjelmointi API

Backend repository for infraohjelmointi API service in City of Helsinki.

Instructions in this README.md assume that you know  what __docker__ and __docker-compose__ are, and you already have both installed locally. Also you understand what __docker-compose up -d__ means.
This helps to keep the README.md concise.

## Setting up local development environment with Docker

In order to create placeholder for your own environment variables file, make a local `.env.template` copy:

```bash
$ cp .env.template .env
```

Then you can run docker image as detached mode with:

  ```bash
  docker-compose up -d
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
  $ docker exec -it infraohjelmointi-api sh
  ```

Importing Location/Class hierarchy structure and Planning (TS) and Budget (TAE) files:

- Location/Class hierarchy structure
  ```bash
  $ ./import-excels.sh -c path/to/hierarchy.xlsx
  ```

- Planning and Budget files (e.g. in `Excels` folder):
  ```bash
  $ ./import-excels.sh -d path/to/Excels/
  ```

<br>

*Other available file import scripts:*
<details>
<summary>Click to open</summary>
<br>

Import Location/Class hierarchy structure. File `import-excels.sh` uses this:

  ```bash
  $ python manage.py hierarchies --file path/to/hierarchy.xlsx
  ```

Import only Planning project data (files with "TS"):

  ```bash
  $ python manage.py  projectimporter --import-from-plan path/to/planningFile.xlsx
  ```

Import only Budget project data (files with "TAE"):

  ```bash
  $ python manage.py  projectimporter --import-from-budget path/to/budgetFile.xlsx
  ```
</details>

<br>

### Import project location options

Import project location options:

  ```bash
  $ python manage.py locationimporter --file path/to/locationdata.xlsx
  ```

### Update missing projectDistrict data

Update projects' missing `projectDistrict_id` value with `infraohjelmointi_api_projectdistrict.id`.

  ```bash
  $ psql $DATABASE_URL
  infraohjelmointi_api_db=# \i update-districts.sql
  ```

## Other optional file imports

### Import new persons

Import new person information into responsible persons list. The list can be found from project form:

  ```bash
  $ python manage.py responsiblepersons --file path/to/filename.xlsx
  ```
  

---


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
  $ python manage.py test
  ```
An optional verbosity parameter can be added to get a more descriptive view of the tests

  ```bash
  $ python manage.py test -v 1/2/3
  ```

## How to: production release

1. Create a release PR from develop to main
2. Wait for the PR pipeline to run and check that all checks pass
3. Merge the PR
4. Trigger build-infraohjelmointi-api-stageprod
5. Approve pipeline run in azure. Deploy pipelines are triggered by the build pipeline but prod deploy needs to be approved separately (=2 approvals in total). To approve, open the pipeline run you want to approve (from menu, select pipelines, then select the correct pipeline and then select the run you need to approve) and there should be a button to approve it (pipeline run is paused until you approve).

## External data sources

Infra tool project data and financial data can be imported from external sources.

### SAP

To synchronize project data with SAP in local environment, VPN service provided by platta should be running.

Populate DB with SAP costs and commitments using management command:

  ```bash
  $ python manage.py sapsynchronizer
  ```
All projects in DB will also be synced with SAP to update SAP costs and commitments at midnight through the script:

  ```bash
  $ ./sync-from-sap.sh
  ```

### ProjectWise

Sync all project data in the DB with ProjectWise

  ```bash
  $ python manage.py projectimporter --sync-projects-with-pw
  ```

Sync project by PW id in the DB with ProjectWise

  ```bash
  $ python manage.py projectimporter --sync-project-from-pw pw_id
  ```

Projects are also synced to PW service when a PATCH request is made to the projecs endpoint.

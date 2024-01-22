# Infraohjelmointi API

Backend repository for infraohjelmointi API service in City of Helsinki.

Instructions in this README.md assume that you know  what __docker__ and __docker-compose__ are, and you already have both installed locally. Also you understand what __docker-compose up -d__ means.
This helps to keep the README.md concise.

## Setting Up Local Development Environment With Docker

In order to create placeholder for your own environment variables file, make a local `.env.template` copy:

```bash
$ cp .env.template .env
```

Then you can run docker image with:

  ```bash
  docker-compose up -d
  ```

- Access development server on [localhost:8000](http://localhost:8000)

- Login to admin interface with `admin` and 🥥 at [localhost:8000/admin](http://localhost:8000/admin)

- Done!

### What Next?

This list is a 'TL;DR'. Steps are described more detailed on this README file.

- [Excel Files](#excel-files)
  - Import Location/Class hierarchy structure
  - Import Planning (TS) and Budget (TAE) files in bulk together
- [Fix known issues from database](#fix-database-issues)

- [Optional imports](#other-optional-file-imports)
  - Import project location options
  - Import new person information into responsible persons list

## Managing Project Packages

- We use `pip` to manage python packages we need
- After adding a new package to requirements.txt file, compile it and re-build the Docker image so that the container would have access to the new package

  ```bash
  docker-compose up --build
  ```

## Running Tests

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

## How To: Production Release

1. Create a release PR from develop to main
2. Wait for the PR pipeline to run and check that all checks pass
3. Merge the PR
4. Trigger build-infraohjelmointi-api-stageprod
5. Approve pipeline run in azure. Deploy pipelines are triggered by the build pipeline but prod deploy needs to be approved separately (=2 approvals in total). To approve, open the pipeline run you want to approve (from menu, select pipelines, then select the correct pipeline and then select the run you need to approve) and there should be a button to approve it (pipeline run is paused until you approve).

## External Data Sources

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

### Excel Files

Project data and finances can be imported using excel files into the infra tool.

Import Location/Class hierarchy structure:

  ```bash
  $ python manage.py hierarchies --file path/to/hierarchy.xlsx
  ```

Import Planning (TS) project data:

  ```bash
  $ python manage.py  projectimporter --import-from-plan path/to/planningFile.xlsx
  ```

Import Budget (TAE) project data:

  ```bash
  $ python manage.py  projectimporter --import-from-budget path/to/budgetFile.xlsx
  ```

Import Planning (TS) and Budget (TAE) files in bulk together:

  ```bash
  $ ./import-excels.sh -d path/to/directory/containing/all/Excels
  ```

# Fix Database Issues

Imported files might included typos or incorrectly written information.

Fix known issues from database:

  ```bash
  $ psql $DATABASE_URL
  infraohjelmointi_api_db=# \i fix-database.sql
  ```

### Other Optional File Imports

Import project location options:

  ```bash
  $ python manage.py locationimporter --file path/to/locationData.xlsx
  ```

Import new person information into responsible persons list:

  ```bash
  $ python manage.py responsiblepersons --file path/to/responsiblePersons.xlsx
  ```
  
# Changelog

## [1.11.0](https://github.com/City-of-Helsinki/infraohjelmointi-api/compare/infraohjelmointi-api-v1.10.5...infraohjelmointi-api-v1.11.0) (2026-08-20)


### Features

* Demote suspended phase to a designPlanning detail (IO-863) ([bb71bf3](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/bb71bf31bbd34d6e1967620c63244950eea39d23))
* Prevent haamuluku creation on project schedule changes (IO-894) ([e1caae6](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/e1caae673a17c78af140f3a290852134b33679ad))
* Restructure project phase taxonomy and backfill programming phase (IO-863) ([3cb9eec](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/3cb9eec95ade5f3032b0643a330957f8e44198fd))
* Ship audit logs to platta elastic cloud via django-resilient-logger (IO-845) ([933420b](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/933420b2915e464b6a3f8c4fee7307fdd6344585))


### Bug Fixes

* Align IO-863 migration names with develop to prevent post-merge conflicts ([3f0e020](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/3f0e020fc2ad409bae755e734546b51074482a7a))
* Align phase taxonomy migration with the full IO-863 spec (IO-863) ([a3f9d8b](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/a3f9d8be81925b23e7da7726df236af9718b9681))
* Correct typo and migration number (IO-845) ([36938cd](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/36938cd0596aad1ddbf90d94220913d1842394df))
* Dedupe update-phase-indexes.sql to satisfy sonarcloud (IO-863) ([6a3ebff](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/6a3ebff1a2ab8d554941d8ade0a8bec3e14b4d91))
* Remove warrantyIncomplete phase detail (IO-863) ([6fe9e35](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/6fe9e35d7c9a5ca8d587ce6b20e316d8afec63ce))
* Renumber warranty-incomplete migration for release branch (IO-863) ([c053b07](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/c053b0743488a6a5ffbaa4b163b61f0f472e84b2))
* Stop class budget sum absorbing prefix-named sibling classes (IO-928) ([a871f0f](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/a871f0f47098a1bb5613a04a4f38a681b23cb407))

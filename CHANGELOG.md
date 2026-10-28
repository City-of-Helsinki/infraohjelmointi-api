# Changelog

## [1.12.1](https://github.com/City-of-Helsinki/infraohjelmointi-api/compare/infraohjelmointi-api-v1.12.0...infraohjelmointi-api-v1.12.1) (2026-10-28)


### Bug Fixes

* Fixes to construction handover according to testing comments (IO-849) ([#504](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/504)) ([70cb738](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/70cb738d3c5842a55ecfe63102b72b2005c1994c))
* Invalidate coordinator finance caches when planning finances change (IO-957) ([#501](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/501)) ([fcdd310](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/fcdd3103147e092a7b27d8ea19432046fb9ba683))
* Use fresh values in finance update events (IO-889) ([476c030](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/476c030d350af9f77a3b9fa4b6e2edaae763d53b))

## [1.12.0](https://github.com/City-of-Helsinki/infraohjelmointi-api/compare/infraohjelmointi-api-v1.11.0...infraohjelmointi-api-v1.12.0) (2026-10-22)


### Features

* Add a location map image to project programmes (IO-936) ([2c07a7d](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/2c07a7d7cac976e626fe05cc39da8f515d8c5a2d))
* Add attachments to every project programme section (IO-914) ([01ab10d](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/01ab10d515cca54e4619a0c869b84623d1c46319))
* Add construction handover attachment API (IO-857) ([13fc289](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/13fc289c58e5d68a23c9c5a8aeec46ed7651a126))
* Add endpoint for getting project tasks (IO-899) ([#484](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/484)) ([dfbf9a1](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/dfbf9a1f5b6712c108ff8d3940f37efd7676d203))
* Add note image upload API with Azure Blob storage (IO-812) ([5c2d887](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/5c2d887165ef84d3c6dfddf919da61b550f635d0))
* Add type and sapProject to audit_loggable_fields (IO-881) ([119403a](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/119403a5b95306b2a579719b8a21e0721d540eae))
* **api:** Added new fields to traffic planning criteria ([#489](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/489)) ([bd7da37](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/bd7da370d7818c0f8b07048fe19bb7faeef74b5d))
* Require confirming the linked pw project before saving an hkrid (IO-935) ([4f8c388](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/4f8c388dc5a43982e344143b527aae7e4000e042))


### Bug Fixes

* Add staraProcurementReason field to ConstructionHandover (IO-849) ([#482](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/482)) ([3083cdb](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/3083cdbcc9f2474c6e6cf004658075931b9f813f))
* Allow construction handover editors to return a handover to draft (IO-849) ([#497](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/497)) ([1731b11](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/1731b11f10eb7c2f346e85643f4b68db5172cc74))
* Answer 409 for link writes on a locked section (IO-914) ([5aad958](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/5aad958e4c9576bb81d7f7b8a22562a0956361cc))
* **api:** Added validation for required fields when marking complete in project programme ([#499](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/499)) ([844c228](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/844c22813faffe543a4415be64c499e583e51966))
* **api:** Fixed new clásses not showing in coordinator and f2f-views ([#483](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/483)) ([e90ebe5](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/e90ebe5f74f15e037a0ab79fd8dcc0cabac1c76b))
* **api:** Fixed saving links to all sections ([#502](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/502)) ([d8fc2a3](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/d8fc2a302f339ea275651d041a409dfc7f6ad96c))
* Check that uploaded bytes match the declared file type (IO-857) ([9983bfb](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/9983bfb79fac69149cd6e4defa6b0ae9220cb6a3))
* Close review gaps in the pw link confirmation (IO-935) ([02bba2b](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/02bba2bfefcc4f78bc173412ac0a4225d013c4ba))
* Close the remaining ways to edit outside the restricted classes (IO-756) ([6dac6f6](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/6dac6f6d6475ffa22751b615b6afd2a9dedcf520))
* Fixes according to testing comments (IO-805) ([#486](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/486)) ([6cd9891](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/6cd9891ba18a3bb6d325712d88576967175ddbcf))
* Fixes according to testing comments (IO-899) ([#487](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/487)) ([2f0b4c0](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/2f0b4c00df41dc387f712c08c7644e8a20bb5d05))
* Let restricted programmers create projects in their own classes (IO-756) ([74f0e45](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/74f0e455f0651cc85d976c51edd204ec61f9438d))
* Parse hkrids like the serializer so the pw link guard cannot be skipped (IO-935) ([311c6e3](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/311c6e3637fdb7fc34fef00110695c3b2c8d8a38))
* Raise uvicorn header size limit for large auth tokens (IO-931) ([#498](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/498)) ([22e7161](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/22e7161d8e6da28b085227cffb7ff79702209f24))
* Restore the released dependencies of the IO-863 migrations (IO-863) ([4e99e3e](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/4e99e3eb6279ae63d9b243d92cf96cdcf9e213d0))
* Return a restricted programmer flag from who-am-i (IO-756) ([f4a1026](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/f4a10263db7025375edc277b26cc728fdb01d877))
* Return the editable class ids from who-am-i (IO-756) ([9b2e17f](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/9b2e17f30b0ff65ef67464ef5d5dcc76573df586))
* Widen permissions for SUBMITTED_TO_PROGRAMMER transition (IO-859) ([#485](https://github.com/City-of-Helsinki/infraohjelmointi-api/issues/485)) ([695b358](https://github.com/City-of-Helsinki/infraohjelmointi-api/commit/695b3588d89ecabae1de6f3b2bb2e318427928be))

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

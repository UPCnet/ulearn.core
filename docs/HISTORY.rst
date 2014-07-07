Changelog
=========

1.36 (unreleased)
-----------------

- Nothing changed yet.


1.35 (2014-07-07)
-----------------

* Fix bug in people search [Victor Fernandez de Alba]

1.34 (2014-06-30)
-----------------

* Make Video CT more specific by having its own class and Interface [Victor Fernandez de Alba]

1.33 (2014-06-30)
-----------------

* New widget variables [Victor Fernandez de Alba]

1.32 (2014-06-26)
-----------------

* New video CT and related migrations. New related i18n. Improve fails in hooks. [Victor Fernandez de Alba]

1.31 (2014-06-26)
-----------------

* Migrate code to rest client [Carles Bruguera]

1.30 (2014-06-20)
-----------------

* Fix discussion CT name, add some i18n and tests failing. Fix boolean on edit for push notifications. [Victor Fernandez de Alba]

1.29 (2014-06-16)
-----------------

* F*cking missing limit on query [Victor Fernandez de Alba]
* Fixes #510399, default time set correctly on add BBB reservation [Victor Fernandez de Alba]

1.28 (2014-06-16)
-----------------

* Improve migration initialized communities [Victor Fernandez de Alba]

1.27 (2014-06-13)
-----------------

* Fix unmerged paths [Victor Fernandez de Alba]

1.26 (2014-06-12)
-----------------

* Debats feature [Victor Fernandez de Alba]
* Migration action [Victor Fernandez de Alba]

1.25 (2014-06-06)
-----------------

* Fix case when user is not valid, continue to process the others [Victor Fernandez de Alba]

1.24 (2014-06-06)
-----------------

* Guard in case that the lists of subscribed are empty [Victor Fernandez de Alba]
* More migration [Victor Fernandez de Alba]

1.23 (2014-06-05)
-----------------

* Guard in case that the lists of subscribed are empty [Victor Fernandez de Alba]
* More migration [Victor Fernandez de Alba]

1.22 (2014-06-05)
-----------------

* New view for migrating all communities for mark them as initialized [Victor Fernandez de Alba]

1.21 (2014-05-30)
-----------------

* Traduccions angles [Pilar Marinas]
* Traduccions angles [Pilar Marinas]
* Traduccions angles [Pilar Marinas]

1.20 (2014-05-29)
-----------------

* Translations in English [Pilar Marinas]

1.19 (2014-05-26)
-----------------

* BBB language option [Victor Fernandez de Alba]
* Avoid modify event to be triggered on creation [Carles Bruguera]

1.18 (2014-05-13)
-----------------

* Fix bugs [Victor Fernandez de Alba]

1.17 (2014-05-08)
-----------------

* Turn on the new directory features and improvements [Victor Fernandez de Alba]

1.16 (2014-05-07)
-----------------

* Add new instantiation option for not to show post box on timeline [Victor Fernandez de Alba]
* Updated robot test boilerplate [Victor Fernandez de Alba]
* Not force email the user on user creation [Victor Fernandez de Alba]
* Complete upload ws to match the new contract [Victor Fernandez de Alba]
* Make fullname be required to avoid LDAP error, redefine all schema on ulearn. [Victor Fernandez de Alba]
* include notifications check on create/update [Carles Bruguera]
* Make a single requests for all updates [Carles Bruguera]
* Upgrade to use rest maxclient [Carles Bruguera]
* New community check for enable push notifications. [Victor Fernandez de Alba]
* Traduccions perfil usuari [Pilar Marinas]

1.15 (2014-04-02)
-----------------

* Traduccions [Pilar Marinas]

1.14 (2014-03-25)
-----------------

* Take new directory back as MAX does not reflect yet the last changes. [Victor Fernandez de Alba]

1.13 (2014-03-24)
-----------------

* Go away with the p.a.e. translations [Victor Fernandez de Alba]
* Be more safe doing things [Victor Fernandez de Alba]
* Fix tests [Victor Fernandez de Alba]
* End creation of file from WS [Victor Fernandez de Alba]
* Merge branch 'master' of github.com:UPCnet/ulearn.core [Victor Fernandez de Alba]
* Add link to hook from upload files from app [Victor Fernandez de Alba]
* Merge branch 'master' of github.com:UPCnet/ulearn.core [Corina Riba]
* Traducciones ca es [Corina Riba]
* Upload with parameters to the title [Victor Fernandez de Alba]
* Capture the activity related to an file/image upload. Set new factories for them and modify hook. [Victor Fernandez de Alba]
* More upload tests [Victor Fernandez de Alba]
* Added test for upload files [Victor Fernandez de Alba]
* Search users finished [Victor Fernandez de Alba]
* Deprecate oportunity type. Fix some views, complete user search [Victor Fernandez de Alba]
* Tests for search users [Victor Fernandez de Alba]
* New index by hash community [Victor Fernandez de Alba]
* Migrate to MaxClient RESTish and rethink user directory [Victor Fernandez de Alba]
* Solucionar errors merge traduccions [Pilar Marinas]
* Solucionar errors merge traduccions [Pilar Marinas]
* Afegida vista searchContentTags a Folder i traduccions [Pilar Marinas]

1.12 (2014-03-04)
-----------------

* i18n [Victor Fernandez de Alba]

1.11 (2014-03-04)
-----------------

* Update i18n [Victor Fernandez de Alba]

1.10 (2014-03-03)
-----------------

* Change limit on big_data search user viz [Victor Fernandez de Alba]

1.9 (2014-03-03)
----------------

* Fix i18n.


1.8 (2014-03-03)
----------------

* Fix i18n.


1.7 (2014-03-03)
----------------

* Add setup for timezone of p.a.event. Fix controlpanel i18n [Victor Fernandez de Alba]
* Add tests for calendar [Victor Fernandez de Alba]
* Add guard in case there is no MAX server configured [Victor Fernandez de Alba]

1.6 (2014-02-24)
----------------

* i18n [Victor Fernandez de Alba]
* Uninstall profile, thinnkers literal conditional, new i18n. [Victor Fernandez de Alba]
* Inform of the vip users to the MAX server [Victor Fernandez de Alba]
* Fix setuphandlers [Victor Fernandez de Alba]
* Extend the userschema properly [Victor Fernandez de Alba]
* Move some helpful methods into the g.core [Victor Fernandez de Alba]
* Transfer setup views to genweb [Victor Fernandez de Alba]

1.5 (2014-01-21)
----------------

* i18n [Victor Fernandez de Alba]

1.4 (2014-01-21)
----------------

* new i18n [Victor Fernandez de Alba]
* Unique search user on root [Victor Fernandez de Alba]

1.3 (2014-01-20)
----------------

* Las fixes to search views [Victor Fernandez de Alba]
* Some adjustments [Victor Fernandez de Alba]
* Add guard [Victor Fernandez de Alba]
* Fix several bugs [Victor Fernandez de Alba]
* Last work on permissions [Victor Fernandez de Alba]
* Last bugs on implementation of advanced permissions on communities [Victor Fernandez de Alba]
* End scission on three fields of the permission on communities [Victor Fernandez de Alba]
* Fix BBB form. WIP new permissions on communities field. [Victor Fernandez de Alba]
* change the preference of the search fields favoring fullname over login name [Victor Fernandez de Alba]
* Merge pull request #1 from UPCnet/iskra [Víctor Fernández de Alba]
* Search Users Feature [Víctor Fernández de Alba]
* Apply new widget to field [Victor Fernandez de Alba]
* New VIP users field on control panel [Victor Fernandez de Alba]
* Oportunitats d'innovació [Ramon Navarro Bosch]
* visible users on communities [Ramon Navarro Bosch]
* Update translations [Victor Fernandez de Alba]
* Missing uploads tests, WIP [Victor Fernandez de Alba]
* Function to search users [Ramon Navarro Bosch]
* Adding telèfon [Ramon Navarro Bosch]
* Search User backend [Ramon Navarro Bosch]
* Adding a field of ubicació on User schema [Ramon Navarro Bosch]
* Improve setuphandlers on initial portlet creation and subsequent reinstalls [Victor Fernandez de Alba]

1.2 (2013-11-26)
----------------

* New helper for create member user folder [Victor Fernandez de Alba]
* add infrae.rest to build [Victor Fernandez de Alba]
* Complete site setup and control panel [Victor Fernandez de Alba]

1.1 (2013-11-14)
----------------

* Update tests, setuphandlers and more control panel settings. Inspector view [Victor Fernandez de Alba]
* tests and new colors for control panel and dynamic CSS [Victor Fernandez de Alba]
* Fix tests [Victor Fernandez de Alba]
* Fix portlet home page order [Victor Fernandez de Alba]
* New color tab and related control panel [Victor Fernandez de Alba]

1.0 (2013-11-07)
----------------

* Fix folder creation (2) [Victor Fernandez de Alba]
* Fix community folder creation [Victor Fernandez de Alba]

1.0RC9 (2013-11-04)
-------------------

* Setup parametrization of new sites [Victor Fernandez de Alba]
* Update community tag to [COMMUNITY] [Victor Fernandez de Alba]

1.0RC8 (2013-10-29)
-------------------

* Allow role WebMaster to manage users and uLearn settings. [Victor Fernandez de Alba]
* New default permissions [Victor Fernandez de Alba]

1.0RC7 (2013-10-28)
-------------------

* New badge definition [Victor Fernandez de Alba]

1.0RC6 (2013-10-28)
-------------------

* Migration for the unified folder names. [Victor Fernandez de Alba]
* New badges. Prevent users to add and edit Title communities with an existing one. [Victor Fernandez de Alba]
* New badges definition [Victor Fernandez de Alba]

1.0RC5 (2013-10-23)
-------------------

* subscribers and hooks [Victor Fernandez de Alba]

1.0RC4 (2013-10-18)
-------------------

* New translations [Victor Fernandez de Alba]
* Fix some views and add some translations [Victor Fernandez de Alba]
* Adjusts to BBB form [Victor Fernandez de Alba]
* Merge branch 'master' of github.com:UPCnet/ulearn.core [Victor Fernandez de Alba]
* CAnvis BB [Victor Fernandez de Alba]

1.0RC3 (2013-10-15)
-------------------

* Complete translations, fix hooks for community creation. [Victor Fernandez de Alba]
* Return mo to gitignore list [Victor Fernandez de Alba]

1.0RC2 (2013-10-01)
-------------------

 * Traduccions i càlcul convidats sessió [Corina Riba]

1.0RC1 (2013-09-16)
-------------------

 * Improve the status of successful upload [Victor Fernandez de Alba]
 * Fix to hooks, added endpoint for uploading documents, images to community via oauth [Victor Fernandez de Alba]
 * Added Osiris PAS plugin [Victor Fernandez de Alba]
 * Updated manifest and ignores to be able to add mos while releasing [Victor Fernandez de Alba]

1.0b9 (2013-08-02)
------------------

 * Transferred all portrait modifications to mrs.max [Victor Fernandez de Alba]
 * Traducciones [Corina Riba]

1.0b8 (2013-07-25)
------------------

 * Missing compile mos [Victor Fernandez de Alba]

1.0b7 (2013-07-25)
------------------

 * Various fixes [Victor Fernandez de Alba]
 * traducciones [Corina Riba]

1.0b6 (2013-07-11)
------------------

 * Traducciones [Corina Riba]
 * Script generea .mo [Corina Riba]

1.0b5 (2013-07-10)
------------------

 * Delete community subscriber. [Victor Fernandez de Alba]
 * Traducciones [Corina Riba]

1.0b4 (2013-07-08)
------------------

 * Various fixes [Victor Fernandez de Alba]
 * Transfer the MAX updater for user's profile subscriber to mrs.max. [Victor Fernandez de Alba]
 * Community features [Victor Fernandez de Alba]
 * Unsubscriptions [Victor Fernandez de Alba]
 * Fix add and edit form. [Victor Fernandez de Alba]
 * My communities [Victor Fernandez de Alba]
 * New permission bounded to the community content type. Fix setuphandlers for not to erase the front-page if it's already a DXCT. [Victor Fernandez de
 * Fix location of the maxloader resource. [Victor Fernandez de Alba]
 * update MANIFEST [Victor Fernandez de Alba]
 * Updated community for adding types [Victor Fernandez de Alba]
 * Add default views for folders [Victor Fernandez de Alba]
 * Fix events folder default view and i18n [Victor Fernandez de Alba]
 * Updated control panel icon [Victor Fernandez de Alba]

1.0b3 (2013-06-11)
--------------------

- Missing plone.app.contenttypes package

1.0b2 (2013-06-11)
--------------------

- Missing mrs.max package

1.0b1 (2013-06-11)
--------------------

- First beta version

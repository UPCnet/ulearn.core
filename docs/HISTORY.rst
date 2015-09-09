Changelog
=========

2.13 (unreleased)
-----------------

- Nothing changed yet.


2.12 (2015-09-09)
-----------------

* Translate video_embed [Pilar Marinas]
* Fix tests [Victor Fernandez de Alba]
* translate profile [Paco Gregori]

2.11 (2015-09-07)
-----------------

* Improvements to the sync and create users [Victor Fernandez de Alba]

2.10 (2015-09-07)
-----------------

* Force username to lowercase for global consistency with username casing [Victor Fernandez de Alba]

2.9 (2015-09-07)
----------------

* Add too_many_users to user search [Victor Fernandez de Alba]
* Fix test [Victor Fernandez de Alba]
* CSS tests [Victor Fernandez de Alba]
* translate blanquerna [Paco Gregori]
* translate userextender blanquerna [Paco Gregori]
* Solucio provisional perque no peti cerca usuaris dins una carpeta [Pilar Marinas]
* Fix config.js location for tests [Carles Bruguera]

2.8 (2015-09-04)
----------------

* Sync api to simulat an arbitrary user login [Carles Bruguera]
* Try to decode form data if not json data [Carles Bruguera]
* New test for viewlets resources [Victor Fernandez de Alba]

2.7 (2015-07-14)
----------------

* Fix Document translation [Pilar Marinas]
* modify news_post test [Paco Gregori]
* Fix File translation [Pilar Marinas]
* Default to username if fullname empty [Carles Bruguera]
* API for groups and f-type interactions [Victor Fernandez de Alba]
* add security file [Paco Gregori]
* add manage user avatar on API [Paco Gregori]
* New transform migration [Victor Fernandez de Alba]
* Restrict script tag and others to the nasty tags for ulearn [Victor Fernandez de Alba]
* add API news and test [Paco Gregori]

2.6 (2015-07-01)
----------------

* updated i18n [Pilar Marinas]

2.5 (2015-07-01)
----------------

* Translations properties extended Credit Andorra [Pilar Marinas]

2.4 (2015-06-25)
----------------

* Fix migrations [Victor Fernandez de Alba]
* Add support for custom icon list on TinyMCE. [Victor Fernandez de Alba]
* Add support for custom icon list on TinyMCE. [Victor Fernandez de Alba]

2.3 (2015-06-17)
----------------

* View displayName not id acl community [Pilar Marinas]

2.2 (2015-06-10)
----------------

* Fix search user for using the soup instead of the mutable_properties [Victor Fernandez de Alba]
* Improve the method of acquiring the current (if enabled) user properties extender, and make the default property backend (IPropertiesPlugin) the more preferent one. [Victor Fernandez de Alba]
* Searchuser [Pilar Marinas]

2.1 (2015-05-25)
----------------

* Add granularity to community creation by adding a role for each community type. CC open, CC closed, CC organizative. WebMasters retain their full permissions, and they are the only ones that could change the community type. [Victor Fernandez de Alba]
* Modify hook Save date of user access to the community [Pilar Marinas]
* Save date of user access to the community [Pilar Marinas]

2.0 (2015-05-18)
----------------

* PEP8 [Victor Fernandez de Alba]
* RAtionalize IGWUUID [Victor Fernandez de Alba]
* Improve migration [Victor Fernandez de Alba]
* Put securityindexing in the fridge [Victor Fernandez de Alba]
* Missing send the permissions to the hub [Victor Fernandez de Alba]
* Patch all the IGWUUID [Victor Fernandez de Alba]
* Try to fix viewlet [Victor Fernandez de Alba]
* Add private Folder [Pilar Marinas]
* Fix gwuuid migration [Victor Fernandez de Alba]
* Improve tests fiability [Victor Fernandez de Alba]
* Last PEP8 [Victor Fernandez de Alba]
* MORE PEP8 [Victor Fernandez de Alba]
* More PEP8 [Victor Fernandez de Alba]
* Erase traces of lcms ws for aquology [Victor Fernandez de Alba]
* PEP8, double quotes [Victor Fernandez de Alba]
* Translate Properties extended Credit Andorra [Pilar Marinas]
* Updated patch to accomodate the properties and extended properties [Victor Fernandez de Alba]
* Fix tests [Victor Fernandez de Alba]
* New generic view for directory views [Victor Fernandez de Alba]
* Updated for complete profile [Victor Fernandez de Alba]
* Added experimental.securityindexing [Victor Fernandez de Alba]
* Added migration for folders [Victor Fernandez de Alba]
* Finalized implementation of the new folder distribution on communities [Victor Fernandez de Alba]
* Fix test, new community initial subscriptions [Victor Fernandez de Alba]
* Fix delete button [Victor Fernandez de Alba]
* Sanitize the initialization of the Closed communities [Victor Fernandez de Alba]
* Add manager to list of authorised users for get communities [Victor Fernandez de Alba]
* Cleaning variables [Victor Fernandez de Alba]
* Add hubclient and fix some integration with hub [Victor Fernandez de Alba]
* Revert no creation of default folders [Victor Fernandez de Alba]
* Interactions type-D and fix a serious bug when assigning plone permissions [Victor Fernandez de Alba]
* PEP8 [Victor Fernandez de Alba]
* Add test for (not fail) bug [Victor Fernandez de Alba]
* Implement notlegit mark for users created via a non subscriber means, e.g a test or ACL [Victor Fernandez de Alba]
* Complete changes in searching users when the user properties are extended [Victor Fernandez de Alba]
* Improve search function by allowing to search through all the fields by introducing the new joined searchable_text. [Victor Fernandez de Alba]
* fix delete issue [Victor Fernandez de Alba]
* Not really used nor tested, but fixed people subscriptions [Victor Fernandez de Alba]
* New communities views angular powered [Victor Fernandez de Alba]
* old-style ACL migration [Victor Fernandez de Alba]
* Improve API and specially its tests. Finished editacl view and related angularjs. Angularize alerts, dialogs for old interactions. Fix omega13 views. New i18n. [Victor Fernandez de Alba]
* New endpoint for change community type and related views. Tests. [Victor Fernandez de Alba]
* Fix migration gwuuid [Victor Fernandez de Alba]
* Add documentation [Victor Fernandez de Alba]
* Fix tests [Victor Fernandez de Alba]
* Skip LDAP tests on JENKINS [Victor Fernandez de Alba]
* Fixed tests [Victor Fernandez de Alba]
* Last developments on ACL [Victor Fernandez de Alba]
* Make all tests pass [Victor Fernandez de Alba]
* ng-switch powah [Victor Fernandez de Alba]
* Tabs working for ACL [Victor Fernandez de Alba]
* Refactor of community and new API endpoints [Victor Fernandez de Alba]
* Tested creation and edit communities [Victor Fernandez de Alba]
* Creation working [Victor Fernandez de Alba]
* WIP, refactoring communities [Victor Fernandez de Alba]
* WIP, community refactor [Victor Fernandez de Alba]
* Nou contingut video incrustat youtube [Pilar Marinas]
* new branch portlet comunitats [Pilar Marinas]
* added unrestrcited [Roberto Diaz]
* added LCMS view [Roberto Diaz]
* change community creation parameters to unify all contents in the same folder Documents [Paco Gregori]
* pep8 [Victor Fernandez de Alba]

1.67 (2015-04-01)
-----------------

* add ulearn_utils to ulearn [Paco Gregori]

1.66 (2015-03-12)
-----------------

* Fix new permissions schema [Victor Fernandez de Alba]

1.65 (2015-03-11)
-----------------

* Transferred from g.core [Victor Fernandez de Alba]

1.64 (2015-03-11)
-----------------

* Optimizations and improvements on templates and getMemberById [Victor Fernandez de Alba]
* New search user view [Victor Fernandez de Alba]
* cambios en hook para modificación de documentos [Paco Gregori]
* afegir al activity stream notificació quan modifiquem un document [Paco Gregori]
* Traducciones tooltips iconos vista más comunidades [Paco Gregori]

1.63 (2015-02-12)
-----------------

* Export to csv [Carles Bruguera]

1.62 (2015-02-10)
-----------------

* Add missing location [Victor Fernandez de Alba]

1.61 (2015-02-10)
-----------------

* Fix use case for communities [Victor Fernandez de Alba]

1.60 (2015-02-10)
-----------------

* Refactor searchusers [Victor Fernandez de Alba]
* See more stats [Pilar Marinas]
* Permis genweb.webmaster i unrestrictedSearchResults [Pilar Marinas]
* Traduccions Estadistiques [Pilar Marinas]
* Allow clear user select & styles [Carles Bruguera]
* Allow clear user select [Carles Bruguera]
* Hide access_type widget [Carles Bruguera]

1.59 (2015-02-05)
-----------------

* Fix comment stats [Carles Bruguera]

1.58 (2015-02-05)
-----------------

* Hide right column & translations [Carles Bruguera]
* Dynamic year and months [Carles Bruguera]
* Selected start month [Pilar Marinas]
* get_months dinamicament [Pilar Marinas]
* Finish select2 widgets [Carles Bruguera]
* Get communities [Pilar Marinas]
* Get communities [Pilar Marinas]
* Method to get date ranges [Carles Bruguera]
* Search PloneStats by community_hash [Pilar Marinas]
* Generalize code [Carles Bruguera]
* Stats view [Carles Bruguera]
* Queries PloneStats document link media [Pilar Marinas]
* Ulearn stats base [Carles Bruguera]
* Traducció literal No hi ha elements cerca [Pilar Marinas]
* Afegir selector obrir finestra nova quicklinks [Pilar Marinas]

1.57 (2015-01-22)
-----------------

* Fix mo in eggs

1.56 (2015-01-22)
-----------------

* Method to remove user permission [Carles Bruguera]

1.55 (2015-01-22)
-----------------

* Remove flag permission on leaving owner role [Carles Bruguera]

1.54 (2015-01-21)
-----------------



1.53 (2015-01-21)
-----------------



1.52 (2015-01-20)
-----------------

* Use activity_view in widget variables [Carles Bruguera]
* Set flag permission to owners [Carles Bruguera]
* Selector activitats [Pilar Marinas]

1.51 (2015-01-15)
-----------------

* Cerca usuaris per telefon i ubicacio [Pilar Marinas]

1.50 (2014-12-10)
-----------------

* i18n [Victor Fernandez de Alba]

1.49 (2014-12-09)
-----------------

* Fix non-consistent community permissions assignment [Victor Fernandez de Alba]

1.48 (2014-12-09)
-----------------

* Fix update permissions for communities [Victor Fernandez de Alba]

1.47 (2014-12-05)
-----------------

* Translates Nexus24 [Victor Fernandez de Alba]
* Update testingt [Victor Fernandez de Alba]
* Updates [Victor Fernandez de Alba]

1.46 (2014-10-22)
-----------------

* i18n [Victor Fernandez de Alba]

1.45 (2014-10-20)
-----------------

* Add helper for bulk reinstall of ulearn.core [Victor Fernandez de Alba]

1.44 (2014-10-20)
-----------------

* New testing [Victor Fernandez de Alba]
* Invalid import [Carles Bruguera]
* Merge branch 'master' of github.com:UPCnet/ulearn.core [Victor Fernandez de Alba]
*  [Victor Fernandez de Alba]
* Conflicts: [Victor Fernandez de Alba]
* ulearn/core/profiles/default/metadata.xml [Victor Fernandez de Alba]
* Not reregister elements that already are registered by genweb.core [Victor Fernandez de Alba]
* Add Quick Links controlpanel [Pilar Marinas]
* Separate main properties from the rest [Carles Bruguera]
* Complete user and communities api [Carles Bruguera]
* Add api view to support REST endpoints [Carles Bruguera]
* PloneFormGen [Pilar Marinas]

1.43 (2014-09-25)
-----------------

* Update i18n [Victor Fernandez de Alba]
* Fallback for some rare cases when we arrive at this point and the MAX context is not created. This happens when the community has been created using the default Dexterity machinery. [Victor Fernandez de Alba]
* Merge branch 'master' of github.com:UPCnet/ulearn.core [Victor Fernandez de Alba]
* Fix search for existing communities on creation [Victor Fernandez de Alba]

1.42 (2014-09-09)
-----------------

* Fixed error on corner cases [Victor Fernandez de Alba]

1.41 (2014-09-04)
-----------------

* Fix subscribe to communities [Victor Fernandez de Alba]

1.40 (2014-09-04)
-----------------

* Fix corner cases for communities getters/setters [Victor Fernandez de Alba]

1.39 (2014-08-07)
-----------------

* Fix tests [Victor Fernandez de Alba]
* Fix some issues on migrations, remove prints [Victor Fernandez de Alba]
* Merging with maxsubscriptions feature branch [Victor Fernandez de Alba]

1.38 (2014-07-24)
-----------------

* Fix searchuser [Victor Fernandez de Alba]

1.37 (2014-07-23)
-----------------

* Added new field to the communities for notify comments. Fix control panel add new users to visibles. [Victor Fernandez de Alba]

1.36 (2014-07-15)
-----------------

* New controlpanel option for setting the library URL [Victor Fernandez de Alba]
* Fix i18n strings and enable filtered_search [Victor Fernandez de Alba]
* Image retrieving from MAX directly [Victor Fernandez de Alba]

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

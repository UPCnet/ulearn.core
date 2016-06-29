#|/bin/bash
cd ..
cd ..
cd ..
/var/plone/genweb.rectorat/bin/i18ndude rebuild-pot --pot ulearn/core/locales/ulearn.pot --create ulearn ../ulearn.theme  ../ulearn.js  .
cd ulearn/core/locales/ca/LC_MESSAGES
/var/plone/genweb.rectorat/bin/i18ndude sync --pot ../../ulearn.pot ulearn.po
cd ..
cd ..
cd en
cd LC_MESSAGES
/var/plone/genweb.rectorat/bin/i18ndude sync --pot ../../ulearn.pot ulearn.po
cd ..
cd ..
cd es
cd LC_MESSAGES
/var/plone/genweb.rectorat/bin/i18ndude sync --pot ../../ulearn.pot ulearn.po

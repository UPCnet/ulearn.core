#|/bin/bash
cd ..
cd ..
cd ..
../../bin/i18ndude rebuild-pot --pot ulearn/core/locales/ulearn.pot --create ulearn ../ulearn.theme  .
cd ulearn/core/locales/ca/LC_MESSAGES
../../../../../../../bin/i18ndude sync --pot ../../ulearn.pot ulearn.po
cd ..
cd ..
cd en
cd LC_MESSAGES
../../../../../../../bin/i18ndude sync --pot ../../ulearn.pot ulearn.po
cd ..
cd ..
cd es
cd LC_MESSAGES
../../../../../../../bin/i18ndude sync --pot ../../ulearn.pot ulearn.po

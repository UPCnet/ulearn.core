*** Settings ***

Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/contenttypes/tests/robot/keywords.txt

Test Setup  Run keywords  Open test browser
Test Teardown  Close all browsers

*** Variables ***

${BROWSER} =  firefox

*** Test Cases ***

Scenario: Test uLearn log in
    Log in  ${TEST_USER_NAME}  ${TEST_USER_PASSWORD}
    Page should contain  Está ahora identificado

*** Keywords ***

# ----------------------------------------------------------------------------
# Login/Logout (Adapted for uLearn from default p.a.robotframework)
# ----------------------------------------------------------------------------

Log in
    [Documentation]  Log in to the site as ${userid} using ${password}. There
    ...              is no guarantee of where in the site you are once this is
    ...              done. (You are responsible for knowing where you are and
    ...              where you want to be)
    [Arguments]  ${userid}  ${password}
    Go to  ${PLONE_URL}/login_form
    Page should contain element  __ac_name
    Page should contain element  __ac_password
    Page should contain element  css=#login_form button[name=submit]
    Input text for sure  __ac_name  ${userid}
    Input text for sure  __ac_password  ${password}
    Click Button  css=#login_form button[name=submit]

Log in as test user

    Log in  ${TEST_USER_NAME}  ${TEST_USER_PASSWORD}

Log in as site owner
    [Documentation]  Log in as the SITE_OWNER provided by plone.app.testing,
    ...              with all the rights and privileges of that user.
    Log in  ${SITE_OWNER_NAME}  ${SITE_OWNER_PASSWORD}

Log in as test user with role
    [Arguments]  ${usrid}  ${role}

    # We need a generic way to login with a user that has one or more roles.

    # Do we need to be able to assign multiple roles at once?

    # Do we need to assign roles to arbitray users or is it sufficient if we
    # always assign those roles to the test user?

Log out
    Go to  ${PLONE_URL}/logout
    Page Should Contain Element  css=#login_form

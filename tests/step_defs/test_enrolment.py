from pytest_bdd import scenarios, then

scenarios("../features")


@then("I can enrol successfully")
def enrolment() -> None:
    pass

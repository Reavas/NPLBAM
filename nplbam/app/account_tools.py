"""
This module Contains functionality to verify the strength of passwords,
and check the validity of form data with regards to user accounts.
"""

import math
import re

from flask import Request

# User account types. (0, 1, 2, 3, 4, 5)
USER_LEVEL_MAX: int = 5
# Looked at the minimum in KeePass 2 for it to be considered green
MIN_PASSWORD_ENTROPY_BITS: int = 64


class AccountInfo:
    """
    Describes the information that makes up an account.
    Used for creating new accounts, as well as validating
    edits to existing accounts.
    """
    # Whether this account creation is valid
    valid: bool = True
    username: str = ""
    password_set: bool = True
    password: str = ""
    user_lvl: int = 0
    # The sets signal whether these optional
    # values are present
    rescue_set: bool = False
    rescue_id: int = 0
    pound_set: bool = False
    pound_id: int = 0


def verify_password_strength(password: str) -> (int, bool):
    """
    Calculate the number of bits of entropy of the entered password,
    return that value as well as whether it meets the minimum requirements.

    :param password: The password to measure the strength of
    :return: A tuple (int, bool)[Password Entropy Bits, Whether the password meets the requirements]
    """
    # Strength formula: log(C) / log(2) * L
    # Where C is the size of the character set,
    # and L is the length of the password
    # Source: https://en.wikipedia.org/wiki/Password_strength
    global MIN_PASSWORD_ENTROPY_BITS
    password_length = len(password)
    # If the password is length 0, then it has no entropy.
    if password_length == 0:
        return (0, False)
    symbol_set_count: int = 0
    # Check whether the password contains a number
    num_match: re.Match = re.search("[0-9]+", password)
    if num_match is not None:
        symbol_set_count += 10
    # Lowercase Letter?
    lower_match: re.Match = re.search("[a-z]+", password)
    if lower_match is not None:
        symbol_set_count += 26
    # Uppercase Letter?
    upper_match: re.Match = re.search("[A-Z]+", password)
    if upper_match is not None:
        symbol_set_count += 26
    # Symbol?
    symbol_match: re.Match = re.search(
        "[~`!@#$%^&*()-_{}\[\]:;\"'<,>|.+=?/\\\\]+", password)
    if symbol_match is not None:
        symbol_set_count += 32
    # A space?
    space_match: re.Match = re.search("[ ]+", password)
    if symbol_match is not None:
        symbol_set_count += 1
    # Calculate the number of entropy bits, whether is is greater than the minimum number
    # then return
    entropy_bits: int = math.floor(
        ((math.log(symbol_set_count)) / (math.log(2))) * password_length
    )
    return (entropy_bits, (entropy_bits >= MIN_PASSWORD_ENTROPY_BITS))


def validate_form_input(request: Request,
                        errors: list,
                        editing_account: bool = False) -> AccountInfo:
    """
    Validate the form input for the new_account page, as well as the edit_account page.

    :param request: Passed flask Request object, to pull the form data out of.
    :param errors: an out parameter, to be populated with any errors encountered in the
        form data.
    :param editing_account: Signifies whether this is a new account being created, or
        whether we are validating an update to an existing account.

        The reason for this differentiation is that an updated account is valid if the password
        field is empty since it signifies that the password is not to be updated, 
        while an empty password field for a new account is not allowed.
    :return: A new instance of AccountInfo, containing the validated information pulled from
        the request parameter. As well as whether the AccountInfo represents a valid update or new
        account. (AccountInfo.valid)
    """
    global USER_LEVEL_MAX
    global MIN_PASSWORD_ENTROPY_BITS
    # Pull and validate the fields:
    username: str = request.form["username"]
    password: str = request.form["password"]
    password_verify: str = request.form["passwordVerify"]
    user_lvl: str = request.form["userLVL"]
    rescue_id: str = request.form["rescueID"]
    pound_id: str = request.form["poundID"]

    account: AccountInfo = AccountInfo()
    # Validate username and password:
    if username == "":
        errors.append("A username is required.")
        account.valid = False
    if password == "":
        # We may not be getting a new password, since we could
        # be editing an existing account.
        if not editing_account:
            errors.append("A password is required.")
            account.valid = False
        else:
            account.password_set = False
    if (password != password_verify):
        errors.append("The passwords entered do not match.")
        account.valid = False

    # Only do this if the password has been set
    if account.password_set:
        entropy_bits, valid = verify_password_strength(password)
        if not valid:
            errors.append(
                "Password does not meet minimum strength requirement of {} bits. ".format(
                    MIN_PASSWORD_ENTROPY_BITS) +
                "It contains {} bits of entropy. ".format(entropy_bits) +
                "Please either increase its length, " +
                "or add characters from different character sets. " +
                "(For example: Add some numbers, or a maybe a symbol.)")
            account.valid = False

    # They are good, add them to the structure.
    account.username = username
    account.password = password
    # Validate against our user level:
    try:
        user_lvl: int = int(user_lvl)
        if (user_lvl < 0) or (user_lvl > USER_LEVEL_MAX):
            errors.append("User level is out of bounds")
            account.valid = False
    except:
        errors.append("user level wasn't entered or was not a number.")
        account.valid = False
    account.user_lvl = user_lvl
    # Validate our optional fields:
    if rescue_id != "":
        try:
            rescue_id: int = int(rescue_id)
        except:
            errors.append("Rescue ID field filled out, and is not a number.")
            account.valid = False
        account.rescue_id = rescue_id
        account.rescue_set = True
    if pound_id != "":
        try:
            pound_id: int = int(pound_id)
        except:
            errors.append("Pound ID field is filled out, and is not a number.")
            account.valid = False
        account.pound_id = pound_id
        account.pound_set = True
    return account

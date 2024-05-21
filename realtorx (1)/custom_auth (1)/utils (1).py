import os
from random import SystemRandom

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

import pandas
from phonenumber_field.phonenumber import PhoneNumber

from realtorx.agencies.models import Agency
from typing import Any, Dict, List, Optional
from OpenSSL import crypto
import jwt
from jwt.utils import base64url_decode
import requests
import logging

logger = logging.getLogger("django")


def set_password_reset_expiration_time():
    return timezone.now() + timezone.timedelta(days=1)


def set_email_verification_expiration_time():
    return timezone.now() + timezone.timedelta(days=7)


def clean_username(username):
    return slugify(username, allow_unicode=True)


def get_header_index(header, name):
    for i, h in enumerate(header):
        if h == name:
            return i
    return -1


def create_agencies(rows, agency_idx):
    print("creating agencies...")
    new_agencies = []
    exist_agencies = set(Agency.objects.all().values_list("name", flat=True))

    for row in rows:
        agency_name = str(row[agency_idx])
        if agency_name not in exist_agencies:
            new_agencies.append(Agency(name=agency_name))
            exist_agencies.add(agency_name)

    Agency.objects.bulk_create(new_agencies)
    print("created {0} agencies".format(len(new_agencies)))


def preloadig_users_from_file(filename):
    from realtorx.custom_auth.models import ApplicationUser

    exist_usernames = set(
        ApplicationUser.objects.all().values_list("username", flat=True)
    )

    data = pandas.read_excel(
        os.path.join(
            settings.BASE_DIR, "realtorx/custom_auth/preloading_files", filename
        ),
        sheet_name=None,
    )
    sheet_names = data.keys()
    print("-------started---------")

    for sheet_name in sheet_names:
        header = data[sheet_name].columns

        first_name_idx = get_header_index(header, "First Name")
        last_name_idx = get_header_index(header, "Last Name")
        email_idx = get_header_index(header, "Email")
        agency_idx = get_header_index(header, "Company Name")
        city_idx = get_header_index(header, "City")
        state_idx = get_header_index(header, "State")
        county_idx = get_header_index(header, "County")
        phone_idx = get_header_index(header, "MobileNumber")
        agency_address_idx = get_header_index(header, "Company Address")
        agency_phone_idx = get_header_index(header, "Company Phone")

        avatar_idx = get_header_index(header, "avatar")
        zipcode_idx = get_header_index(header, "Zipcode")
        sourcesystemid_idx = get_header_index(header, "sourcesystemid")
        username_idx = get_header_index(header, "username")

        print("getting all users emails...")
        exist_users_emails = set(
            ApplicationUser.objects.all().values_list("email", flat=True)
        )
        print("getting all users phones...")
        exist_users_phones = set(
            ApplicationUser.objects.all().values_list("phone", flat=True)
        )
        print("getting all agencies phones...")

        new_users = []
        count = 0

        # replace NaN to ''
        data[sheet_name].fillna("", inplace=True)
        create_agencies(data[sheet_name].values, agency_idx)
        exist_agencies = {agency.name: agency for agency in Agency.objects.all()}

        total_rows = len(data[sheet_name].values)
        for row in data[sheet_name].values:

            count += 1
            if count % 5000 == 0:
                print(count / total_rows * 100, "%")

            avatar = f"avatars/{row[avatar_idx]}.png"
            email = row[email_idx]
            phone_number = row[phone_idx]
            agency_name = row[agency_idx]

            if agency_name == "" or phone_number == "" or email == "":
                continue

            agency = exist_agencies.get(agency_name)

            try:
                phone = PhoneNumber(
                    national_number=str(int(phone_number)), country_code="+1"
                )
                if not phone.is_valid():
                    phone = None
            except Exception:  # NOQA
                phone = None

            username = row[username_idx]
            zipcode = row[zipcode_idx]
            sourcesystemid = row[sourcesystemid_idx]

            if username in exist_usernames:
                continue

            exist_usernames.add(username)

            if email not in exist_users_emails and str(phone):
                # username = email.split('@')[0] + '_' + '_'.join(email.split('@')[1].split('.'))

                try:
                    agency_phone = PhoneNumber(
                        national_number=row[agency_phone_idx], country_code="+1"
                    )
                    if not agency_phone.is_valid():
                        agency_phone = None
                except Exception:  # NOQA
                    agency_phone = None
                temp_pass = str(row[last_name_idx]) + str(
                    SystemRandom().randint(10, 99)
                )
                user = ApplicationUser(
                    username=username,
                    first_name=row[first_name_idx],
                    last_name=row[last_name_idx],
                    full_name=str(row[first_name_idx]) + " " + str(row[last_name_idx]),
                    email=row[email_idx],
                    agency=agency,
                    brokerage_address=row[agency_address_idx],
                    brokerage_phone_number=agency_phone,
                    state=row[state_idx],
                    county=[row[county_idx]],
                    city=[row[city_idx]],
                    phone=phone,
                    send_email_with_temp_password=True,
                    temp_password=temp_pass,
                    zipcode=zipcode,
                    sourcesystemid=sourcesystemid,
                )
                user.avatar = avatar
                new_users.append(user)
                exist_users_emails.add(email)
                if count % 10000 == 0:
                    ApplicationUser.objects.bulk_create(new_users)
                    print("creaated ", len(new_users))
                    new_users = []

        print("100%")
        if new_users:
            ApplicationUser.objects.bulk_create(new_users)

        print("created {0} new_users".format(len(new_users)))


ROOT_CER_URL = "https://www.apple.com/certificateauthority/AppleRootCA-G3.cer"
G6_CER_URL = "https://www.apple.com/certificateauthority/AppleWWDRCAG6.cer"


def validate_and_decode_apple_jwt(apple_jwt_string: str) -> Optional[Dict[str, Any]]:
    # Fetch the well-known/expected root & intermediate keys from Apple:
    root_cert_bytes: bytes = requests.get(ROOT_CER_URL).content
    root_cert = crypto.load_certificate(crypto.FILETYPE_ASN1, root_cert_bytes)
    g6_cert_bytes: bytes = requests.get(G6_CER_URL).content
    g6_cert = crypto.load_certificate(crypto.FILETYPE_ASN1, g6_cert_bytes)

    # Get the signing keys out of the JWT header. The header will look like:
    # {"alg": "ES256", "x5c": ["...base64 cert...", "...base64 cert..."]}
    header = jwt.get_unverified_header(apple_jwt_string)
    alg = header["alg"]  # ES256
    provided_certificates: List[crypto.X509] = []
    certificate_names: List[Dict[bytes, bytes]] = []

    if (
        "x5c" not in header
    ):  # skipping cert verification is there are no certs to be verified in the header
        return

    for cert_base64 in header["x5c"]:
        cert_bytes = base64url_decode(cert_base64)
        another_cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bytes)
        # To see the certificate chain by name, which corresponds to certs you can fetch:
        # https://www.apple.com/certificateauthority/
        #
        # Prints <X509Name object '/CN=Apple Root CA - G3/OU=Apple Certification Authority/O=Apple Inc./C=US'>:
        certificate_names.append(dict(another_cert.get_subject().get_components()))
        provided_certificates.append(another_cert)

    # Verify that the root & intermediate keys are what we expect from Apple:
    assert (
        certificate_names[-1][b"CN"] == b"Apple Root CA - G3"
    ), f"Root cert changed: {certificate_names[-1]}"
    assert (
        certificate_names[-2][b"OU"] == b"G6"
    ), f"Intermediate cert changed: {certificate_names[-2]}"
    assert provided_certificates[-2].digest("sha256") == g6_cert.digest("sha256")
    assert provided_certificates[-1].digest("sha256") == root_cert.digest("sha256")

    # Validate that the cert chain is cryptographically legit:
    store = crypto.X509Store()
    store.add_cert(root_cert)
    store.add_cert(g6_cert)
    for cert in provided_certificates[:-2]:
        try:
            crypto.X509StoreContext(store, cert).verify_certificate()
        except crypto.X509StoreContextError:
            logging.error("Invalid certificate chain in JWT: %s", apple_jwt_string)
            return None
        store.add_cert(cert)

    # Now that the cert is validated, we can use it to verify the actual signature
    # of the JWT. PyJWT does not understand this certificate if we pass it in, so
    # we have to get the cryptography library's version of the same key:
    cryptography_version_of_key = (
        provided_certificates[0].get_pubkey().to_cryptography_key()
    )
    try:
        return jwt.decode(
            apple_jwt_string, cryptography_version_of_key, algorithms=[alg]
        )
    except Exception:
        logging.exception("Problem validating Apple JWT")
        return None


def process_email_value(email):
    if email is None:
        email = ""
    return email.strip().lower()


def export_usernames():
    from realtorx.custom_auth.models import ApplicationUser

    separator = "\n"

    file_path = (
        os.path.join(
            settings.BASE_DIR, "realtorx/custom_auth/preloading_files", "usernames.csv"
        ),
    )
    with open(file_path, "w") as f:
        content = separator.join(
            [d["username"] for d in ApplicationUser.objects.all().values("username")]
        )
        f.write(content)

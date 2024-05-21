import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings

from realtorx.agencies.models import AgencyBranch, Agency
from realtorx.custom_auth.models import ApplicationUser
from localflavor.us.us_states import STATES_NORMALIZED


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        with open(
            os.path.join(settings.BASE_DIR, "Zendesk_Brokerage.csv"), newline=""
        ) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader, None)  # skip the headers
            for row in reader:
                try:
                    user_phone = f"+{row[5]}" if row[5][0] != "+" else row[5]
                    user = ApplicationUser.objects.filter(phone=user_phone)
                    if user.count() > 0:
                        user = user.first()
                        print("Processinng for user => ", user, row[5])
                        print("Updated phone number => ", user_phone)

                        agency = Agency.objects.filter(name=row[0])
                        if agency.count() > 0:
                            agency = agency.first()
                            print("using existing agency for the user => ", agency)
                        else:
                            agency = Agency.objects.create(name=row[0])
                            print("agency created for the user => ", agency)

                        branch_phone = f"+{row[4]}" if row[4][0] != "+" else row[4]
                        print("Updated branch phone number => ", branch_phone)
                        agency_branch = AgencyBranch.objects.filter(
                            state=STATES_NORMALIZED[row[1].strip().lower()],
                            county=row[2],
                            city=row[3],
                            agency=agency,
                            branch_phone=branch_phone,
                        )
                        if agency_branch.count() > 0:
                            agency_branch = agency_branch.first()
                            print(
                                "using existing agency banch for the user => ",
                                agency_branch,
                            )
                        else:
                            agency_branch = AgencyBranch.objects.create(
                                state=STATES_NORMALIZED[row[1].strip().lower()],
                                county=row[2],
                                city=row[3],
                                agency=agency,
                                branch_phone=branch_phone,
                            )
                            print(
                                "agency branch created for the user => ", agency_branch
                            )

                        user.agency = agency
                        user.agency_branch = agency_branch
                        user.agency_branch_state = agency_branch.state
                        user.state = agency_branch.state
                        user.agency_branch_county = agency_branch.county
                        user.county = [agency_branch.county]
                        user.agency_branch_city = agency_branch.city
                        user.city = [agency_branch.city]
                        user.save()
                        print("user updated with the agency and the agency branch \n")
                    else:
                        print("Skipping unknow user => ", user_phone, "\n")
                except Exception as e:
                    print("Error occurred during processing of the row => ", e, "\n")

            print("CSV Processed")

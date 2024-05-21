from realtorx.houses.models import SavedFilter
from realtorx.taskapp import app
from realtorx.custom_auth.models import ApplicationUser
from datetime import datetime, timedelta


@app.task
def delete_trial_user():
    users = ApplicationUser.objects.filter(
        user_type="trial", date_joined__lte=datetime.now() - timedelta(minutes=1)
    )
    SavedFilter.objects.filter(user__in=list(users)).delete()
    users.delete()

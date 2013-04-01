from monkeybook.tasks import RunFqlTask
from monkeybook.models import User
from monkeybook.fql.profile import ProfileFieldsTask, FamilyTask, SquareProfilePicTask
u = User.objects()[0]
rft = RunFqlTask()

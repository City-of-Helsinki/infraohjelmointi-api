from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from infraohjelmointi_api.models import User
import traceback


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            help=(
                "Argument to give name for the API token. "
                + "Usage: --name AppNameToken"
                + " [--deletetoken]"
            ),
            default="",
        )

        parser.add_argument(
            "--deletetoken",
            action="store_true",
            help=(
                "Argument to delete token from specific API User. Does not delete the User. "
                + "Usage: --deletetoken"
            ),
        )

    def handle(self, *args, **options):
        if not options["name"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py generatetoken --name <name for token>"
                )
            )
            return

        if options["deletetoken"] == True:
            self.deleteToken(name=options["name"])
            return

        try:
            self.generateToken(name=options["name"])
        except Exception as e:
            traceback.print_stack(e)
            self.stdout.write(self.style.ERROR(e))

    def generateToken(self, name):
        self.stdout.write(
            self.style.NOTICE(
                "\n"
                + '\033[94m'
                + "\n"
                + "                      Creating new token\n"
                + "\n"
                +  '\033[0m'
            )
        )

        # Create new user
        user,created = User.objects.get_or_create(username=name)

        if created == False:
            print("Found the user:", name)
            print("Checking if token is already created.")

            exists = Token.objects.filter(user=user).exists()
            if (exists):
                print("\nToken exists. Not creating new.\n")
                return
            
            print("\nAdd token for user:", name)

        else:
            print("\nNew user created:", name)

        token = Token.objects.create(user=user)
        print("Token:", token.key)

        print()

    def deleteToken(self, name):
        self.stdout.write(
            self.style.NOTICE(
                "\n"
                + '\033[94m'
                + "\n"
                + "                      Deleting the token\n"
                + "\n"
                +  '\033[0m'
            )
        )

        # Get user
        user = User.objects.get(username=name)

        # Find new user
        if user:
            print("Found the user:", name)

            token = Token.objects.filter(user=user)
            exists = token.exists()
            if (exists):
                print("\nToken exists, deleting.")
                print("Deleted token:", token[0])

                token.delete()
                print("\nToken deleted.\n")
                return

            print("\nUser does not have a token.")

        else:
            print("\nCould not find user:", name)

        print()

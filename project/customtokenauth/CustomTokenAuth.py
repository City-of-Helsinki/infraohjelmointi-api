from rest_framework import authentication

class CustomTokenAuth(authentication.TokenAuthentication):
    authentication.TokenAuthentication.keyword = 'Bearer'

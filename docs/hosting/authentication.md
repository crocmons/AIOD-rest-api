# Keycloak Service 

When running the metadata catalogue in production, you want to ensure that users can authenticate
so that proper authorization over the endpoints can take place.
Keycloak is typically configured to allow users to sign on with credentials from other services,
such as a Google account or an institutional one.

## Configuring Keycloak
To configure Keycloak, set the following environment variables (preferably through the `override.env` file):

 * `HOSTNAME`: URL for issued tokens ([documentation](https://www.keycloak.org/server/hostname)). For example: `auth.aiod.eu`.
 * `AIOD_KEYCLOAK_PORT`: The port at which the Keycloak server should be available in the host machine, e.g., `8081`.
 * `REDIRECT_URIS`: URI a successful login action should redirect back to. E.g., `https://${HOSTNAME}/docs/oauth2-redirect`.
 * `POST_LOGOUT_REDIRECT_URIS`: URI a successful logout action should redirect back to. E.g., `https://${HOSTNAME}/aiod-auth/realms/aiod/protocol/openid-connect/logout`.

As well as the `openid_connect_url` in `./src/config.override.toml` (for authentication on the Swagger page):
```toml
[keycloak]
openid_connect_url = "https://auth.aiod.eu/aiod-auth/realms/aiod/.well-known/openid-configuration"
```

## Hosting and External Identity Providers 

Using external identity providers locally is hard.
The problem is that the dockerized API thinks that the keycloak is located at host `keycloak` (the name of the keycloak docker container), 
while our keycloak console thinks that it's hosted at `localhost`. This is a problem for the authentication. 
The url of the keycloak is embedded in the token (the `iss` field), 
and must be the same as the url that the API uses, otherwise the API cannot authenticate the user. 
But when accessing e.g., the Google Identity Provider, Google requires the redirect-url to be localhost.

[//]: # (Should include information on how to run it locally then...)

## Roles

The table below gives an overview of the different roles which are used in AI-on-Demand:

| Role                | Comment                                       |
|---------------------|-----------------------------------------------|
| edit_aiod_resources | Allows the user to upload and edit resources. |
| default-roles-aiod  | ???                                           |
| offline_access      | ???                                           |
| uma_authorization   | ???                                           |

Note that some roles may be used for services other than the metadata catalogue.

[//]: # ( Are we missing roles? Check admin console. Are all roles still relevant? delete if not)

## Verifying Keycloak is Working

=== "Swagger"

      To verify the Keycloak service is configured correctly (in production), 
      - Go to http://localhost:8000/docs in your favourite browser
      - Go to `/authorization_test`, click on `try it out` and `execute`. You should get an `Error: Unauthorized`
      - Log in
          - using `Authorize` button in the top right
          - Use `OpenIdConnect (OAuth2, authorization_code with PKCE)`
          - click `Authorize`
          - Use any identity provider. 
      - Go to `/authorization_test`, click on `try it out` and `execute`. 

=== "Postman"

    !!! warning

        Instructions for Postman not updated.

    If you edit a collection, you can use OAuth 2.0 authorization. See image:

    ![Postman Authentication](../media/postman_authentication.png)

    - As `auth url`, use https://test.openml.org/aiod-auth/realms/dev/protocol/openid-connect/auth
    - As `Access token url`, use https://test.openml.org/aiod-auth/realms/dev/protocol/openid-connect/token
    - As `client id`, use `aiod-api`
    - As `client secret`, use `7qpbFTGpONBPIn9nBovgd2843BK8Khjg`

    Then, you should be able to send a `GET` to `localhost:8000/authorization_test`.


A successful response to the `/authorization_test` endpoints should result in a response like:

```json
{
  "name": "user",
  "roles": [
    "edit_aiod_resources",
    "default-roles-aiod",
    "offline_access",
    "uma_authorization"
  ]
}
```


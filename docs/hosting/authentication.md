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

## Using External Identity Providers 

There are two ways to integrate external identity providers (e.g. Google, [EGI Check-in](https://docs.egi.eu/users/aai/check-in/)). 

Create both a private and a public client in the external provider (this step is required for both options below).

### Option 1: Update the configuration files
   - Replace `KEYCLOAK_CLIENT_SECRET` in `.env.override` with the value provided by the external IdP.
   - Update `server_url`, `client_idr`, `client_id_swagger` `openid_connect_url` and `scopes` in `./src/config.override.toml`.
   - In this setup, the Keycloak container is not required and can be shut down.
### Option 2: use keycloak as an identity broker
   - Details can be found in the Keycloak documentation: [Integrating identity providers](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker). 
   - This method allows to configure multiple IdPs.
  
[//]: # (Should include information on how to run it locally then...)

## Roles

Roles identify a type or category of user and determine their access and permissions within applications.
Currently, only the ` edit_aiod_resources` role is defined, granting users the ability to upload and edit resources.
Note that roles may be used for services other than the metadata catalogue.

[//]: # ( Are we missing roles? Check admin console. Are all roles still relevant? delete if not)

## Verifying Keycloak is Working

To verify the Keycloak service is configured correctly using the Swagger interface, follows these steps:

 1. Open your browser and go to `http://$HOSTNAME`
 2. Go to `/authorization_test`, click on `try it out` and `execute`. 
    - You should get an `Error: Unauthorized`
 3. Log in:
    - Click the `Authorize` button in the top-right corner.
    - Select `OpenIdConnect (OAuth2, authorization_code with PKCE)`.
    - Click `Authorize` and log in using any available identity provider. 
 4. Return to `/authorization_test`, click `try it out` and then `execute` again.

If authentication is succesful, the request should now be authtorised. 


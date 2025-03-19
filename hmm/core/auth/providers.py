from abc import ABC, abstractmethod
import json
import logging
from typing import TYPE_CHECKING
import requests

from oauthlib.oauth2 import WebApplicationClient

from hmm.auth.schemas import LoginResponse, SudirLoginResponse
from hmm.config import get_settings
from hmm.utils.exceptions import (
    ProviderConnectionError,
    UnauthorizedUser,
    UnknownAuthenticationProvider,
    SudirTokenExpiredError,
)
from hmm.schemas.auth import (
    ExternalUserResponse,
    InnerSudirUserResponse,
    IntrospectResponse,
    OuterSudirUserResponse,
)

if TYPE_CHECKING:
    from hmm.auth.schemas import SudirAuthToken

logger = logging.getLogger(__name__)


async def get_auth_provider(auth_provider: str):
    """Works out the correct authentication provider that needs
    to be contacted, based on the provider name that was
    passed as an argument.

    Raises:
            backend.exceptions.UnknownAuthenticationProvider
    """
    for provider_cls in AuthProvider.__subclasses__():
        try:
            if await provider_cls.meets_condition(auth_provider):
                return provider_cls(client_id=provider_cls.client_id)
        except KeyError:
            continue

    raise UnknownAuthenticationProvider(auth_provider)


class AuthProvider(ABC):
    """Authentication providers interface"""

    def __init__(self, client_id: str):
        # OAuth 2 client setup
        self.auth_client = WebApplicationClient(client_id)

    @staticmethod
    @abstractmethod
    async def meets_condition(auth_provider: str) -> bool:
        """Checks whether this type of authentication provider
        matches any of the ones defined in the configuration.

        Makes sure the correct provider will be instantiated.
        """
        pass

    @abstractmethod
    async def get_tokens(self, auth_token: str) -> LoginResponse:
        pass

    @abstractmethod
    async def refresh_tokens(self, refresh_token: str) -> LoginResponse:
        pass

    @abstractmethod
    async def get_user(self) -> ExternalUserResponse:
        """Receives an authentication token from an external provider (i.e
        Google, Microsoft)
        and exchanges it for an access token. Then, it retrieves the user's
        details from
        the external providers user-info endpoint.

        Args:
                auth_token: The authentication token received from the
                external provider

        Returns:
                external_user: A user object with the details of the user's
                account as it is stored in the external provider's system.
        """
        pass

    @abstractmethod
    async def get_request_uri(
        self, path_param: str | None = None, redirect_uri: str | None = None
    ) -> str:
        """Returns the external provider's URL for sign in.

        In our case this will be an URL that will
        bring up the SUDIR sign in pop-up window and prompt
        the user to log-in.

        Returns:
                request_uri: Sign in pop-up URL
        """
        pass

    @abstractmethod
    async def get_logout_uri(self) -> str:
        """Returns the external provider's URL for log out.

        In our case this will be an URL that will
        bring up the SUDIR logout page and prompt
        the user to log-in.

        Returns:
                logout_uri: Sign in pop-up URL
        """
        pass

    @abstractmethod
    async def _get_discovery_document(self) -> dict:
        """Returns the OpenId configuration information from the Auth provider.

        This is handy in order to get the:
                1. token endpoint
                2. authorization endpoint
                3. user info endpoint

        Returns:
                discovery_document: The configuration dictionary
        """
        pass

    @abstractmethod
    async def check_session_status(self, token) -> IntrospectResponse:
        """Checks token with introspection endpoint.

        Returns:
                session_status: session status
        """
        pass


class SudirInnerAuthProvider(AuthProvider):
    """Inner SUDIR authentication class for authenticating users and
    requesting user's information via and OpenIdConnect flow.
    """

    settings = get_settings()
    client_id = settings.sudir_inner.client_id
    client_secret = settings.sudir_inner.client_id
    redirect_url = settings.sudir_inner.redirect_url
    logout_redirect_url = settings.sudir_inner.logout_redirect_url

    @staticmethod
    async def meets_condition(auth_provider: str):
        return auth_provider == "sudir-inner"

    async def get_tokens(
        self, auth_token: "SudirAuthToken"
    ) -> SudirLoginResponse:
        token_endpoint = await self.get_openid_endpoint("token_endpoint")
        # Request access_token from SUDIR
        token_url, headers, body = self.auth_client.prepare_token_request(
            token_endpoint,
            redirect_url=self.redirect_url,
            code=auth_token.code,
        )

        try:
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

            self.auth_client.parse_request_body_response(
                json.dumps(token_response.json())
            )

        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get SUDIR access token: {repr(exc)}"
            )

        return SudirLoginResponse.model_validate(token_response.json())

    async def get_user(self) -> InnerSudirUserResponse:
        userinfo_endpoint = await self.get_openid_endpoint("userinfo_endpoint")
        # Request user's information from sudir
        uri, headers, body = self.auth_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.json().get("error"):
            external_user = InnerSudirUserResponse.model_validate(
                userinfo_response.json()
            )
        else:
            raise UnauthorizedUser(
                userinfo_response.json().get("error_description")
            )
        return external_user

    async def check_session_status(self, token: str) -> IntrospectResponse:
        introspect_endpoint = await self.get_openid_endpoint(
            "introspection_endpoint"
        )
        # Request access_token from SUDIR
        introspect_url, headers, body = self.auth_client.prepare_token_request(
            introspect_endpoint, token=token
        )

        try:
            introspect_response = requests.post(
                introspect_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get SUDIR session data: {repr(exc)}"
            )
        introspect_response_json = introspect_response.json()
        if (
            introspect_response_json.get("active") is None
            or introspect_response_json.get("active") is False
        ):
            raise UnauthorizedUser("SUDIR session is inactive")

        return IntrospectResponse.model_validate(introspect_response.json())

    async def refresh_tokens(self, refresh_token: str) -> SudirLoginResponse:
        token_endpoint = await self.get_openid_endpoint("token_endpoint")
        # Request new token pair from SUDIR
        (token_url, headers, body) = (
            self.auth_client.prepare_refresh_token_request(
                token_endpoint, refresh_token=refresh_token
            )
        )

        try:
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

            self.auth_client.parse_request_body_response(
                json.dumps(token_response.json())
            )

        except Exception as exc:  # noqa
            raise SudirTokenExpiredError()

        return SudirLoginResponse.model_validate(token_response.json())

    async def get_request_uri(
        self, path_param: str | None = None, redirect_uri: str = redirect_url
    ) -> str:
        authorization_endpoint = await self.get_openid_endpoint(
            "authorization_endpoint"
        )
        redirect_uri = ""
        if path_param is None:
            redirect_uri = self.redirect_url
        else:

            redirect_uri = self.redirect_url + f"/{path_param}"
        request_uri = self.auth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "profile"],
        )

        return request_uri

    async def get_logout_uri(self) -> str:
        logout_endpoint = await self.get_openid_endpoint(
            "end_session_endpoint"
        )
        request_uri = self.auth_client.prepare_request_uri(
            logout_endpoint, post_logout_redirect_uri=self.logout_redirect_url
        )
        return request_uri

    async def get_openid_endpoint(self, endpoint: str):
        discovery_document = await self._get_discovery_document()
        try:
            result = discovery_document[endpoint]
        except KeyError as exc:
            raise ProviderConnectionError(
                f"Could not parse SUDIR discovery document: {repr(exc)}"
            )
        return result

    async def _get_discovery_document(self) -> dict:
        try:
            discovery_document = requests.get(
                get_settings().sudir_inner.discovery_url
            ).json()
        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get inner SUDIR discovery document: {repr(exc)}"
            )

        return discovery_document


class SudirOuterAuthProvider(AuthProvider):
    """Inner SUDIR authentication class for authenticating users and
    requesting user's information via and OpenIdConnect flow.
    """

    settings = get_settings()
    client_id = settings.sudir_outer.client_id
    client_secret = settings.sudir_outer.client_secret
    redirect_url = settings.sudir_outer.redirect_url
    logout_redirect_url = settings.sudir_outer.logout_redirect_url

    @staticmethod
    async def meets_condition(auth_provider: str):
        return auth_provider == "sudir-outer"

    async def get_tokens(
        self,
        auth_token: "SudirAuthToken",
        request_id: str | None = None,
        redirect_url: str = redirect_url,
    ) -> SudirLoginResponse:
        token_endpoint = await self.get_openid_endpoint("token_endpoint")
        # Request access_token from SUDIR
        token_url, headers, body = self.auth_client.prepare_token_request(
            token_endpoint,
            redirect_url=(
                redirect_url + f"/{request_id}" if request_id else redirect_url
            ),
            code=auth_token.code,
        )

        try:
            logger.debug(
                f"[Sudir] {token_url=}; {headers=}; {body=};"
                f" {(self.client_id, self.client_secret)=}"
            )

            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

            self.auth_client.parse_request_body_response(
                json.dumps(token_response.json())
            )

        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get SUDIR access token: {repr(exc)}"
            )

        return SudirLoginResponse.model_validate(token_response.json())

    async def get_user(self) -> OuterSudirUserResponse:
        userinfo_endpoint = await self.get_openid_endpoint("userinfo_endpoint")
        # Request user's information from sudir
        uri, headers, body = self.auth_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.json().get("error"):
            external_user = OuterSudirUserResponse.model_validate(
                userinfo_response.json()
            )
        else:
            raise UnauthorizedUser(
                userinfo_response.json().get("error_description")
            )
        return external_user

    async def check_session_status(self, token: str) -> IntrospectResponse:
        """Validate user token via introspection service"""
        introspect_endpoint = await self.get_openid_endpoint(
            "introspection_endpoint"
        )
        # Request access_token from SUDIR
        introspect_url, headers, body = self.auth_client.prepare_token_request(
            introspect_endpoint, token=token
        )

        try:
            introspect_response = requests.post(
                introspect_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get SUDIR session data: {repr(exc)}"
            )
        logger.info(f"[{self.__class__.__name__}] {introspect_response=}")
        introspect_response_json = introspect_response.json()
        if (
            introspect_response_json.get("active") is None
            or introspect_response_json.get("active") is False
        ):
            raise UnauthorizedUser("SUDIR session is inactive")
        logger.debug(
            f"[{self.__class__.__name__}] {introspect_response_json=}"
        )
        return IntrospectResponse.model_validate(introspect_response_json)

    async def refresh_tokens(self, refresh_token: str) -> SudirLoginResponse:
        token_endpoint = await self.get_openid_endpoint("token_endpoint")
        # Request new token pair from SUDIR
        (token_url, headers, body) = (
            self.auth_client.prepare_refresh_token_request(
                token_endpoint, refresh_token=refresh_token
            )
        )

        try:
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )

            self.auth_client.parse_request_body_response(
                json.dumps(token_response.json())
            )

        except Exception as exc:  # noqa
            raise SudirTokenExpiredError()

        return SudirLoginResponse.model_validate(token_response.json())

    async def get_request_uri(
        self,
        path_param: str | None = None,
        redirect_uri: str = redirect_url,
        prompt: str | None = "none",
    ) -> str:
        authorization_endpoint = await self.get_openid_endpoint(
            "authorization_endpoint"
        )
        if path_param is None:
            redirect = redirect_uri
        else:
            redirect = redirect_uri + f"/{path_param}"
        request_uri = self.auth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect,
            scope=["openid", "profile", "phone"],
            prompt=prompt,
        )

        return request_uri

    async def get_logout_uri(self) -> str:
        logout_endpoint = await self.get_openid_endpoint(
            "end_session_endpoint"
        )
        request_uri = self.auth_client.prepare_request_uri(
            logout_endpoint, post_logout_redirect_uri=self.logout_redirect_url
        )
        return request_uri

    async def get_openid_endpoint(self, endpoint: str):
        discovery_document = await self._get_discovery_document()
        try:
            result = discovery_document[endpoint]
        except KeyError as exc:
            raise ProviderConnectionError(
                f"Could not parse SUDIR discovery document: {repr(exc)}"
            )
        return result

    async def _get_discovery_document(self) -> dict:
        try:
            discovery_document = requests.get(
                get_settings().sudir_outer.discovery_url
            ).json()
        except Exception as exc:
            raise ProviderConnectionError(
                f"Could not get inner SUDIR discovery document: {repr(exc)}"
            )

        return discovery_document


async def get_outer_sudir_provider() -> SudirOuterAuthProvider:
    return await get_auth_provider("sudir-outer")

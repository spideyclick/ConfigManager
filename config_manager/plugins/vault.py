from __future__ import annotations

from typing import TYPE_CHECKING, Any
from httpx import get, post, Response

if TYPE_CHECKING:
    from .. import Config

SECRET_PATH_DELIMITER = "/"
DEFAULT_VAULT_CONFIGURATION = """
[vault]
address = https://vault.[yourdomain].com/v1/
role_id = [role_id_here]
secret_id = [secret_here]
"""


class VaultConfiguration:
    def __init__(
        self,
        address: str,
        role_id: str,
        secret_id: str,
        token: str | None = None,
    ):
        self.address = address
        self.role_id = role_id
        self.secret_id = secret_id
        self.token = token


active_vault: VaultConfiguration | None = None


def interpolate(self: Config, value: str) -> str:
    global active_vault
    if active_vault is None:
        if "vault" not in self.entries:
            m = (
                "Configuration must include a section for Vault configuration\n"
                f"Example INI configuration:\n{DEFAULT_VAULT_CONFIGURATION}"
            )
            raise KeyError(m)
    active_vault = VaultConfiguration(
        address=self.get_str(["vault", "address"]),
        role_id=self.get_str(["vault", "role_id"]),
        secret_id=self.get_str(["vault", "secret_id"]),
        token=None,
    )
    return get_secret(active_vault, value)


def check_token(f):
    """
    Wrap function; if it fails, run it again with argument renewToken=True
    """

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            return f(*args, **kwargs, renewToken=True)

    return wrapper


@check_token
def get_secret(
    self: VaultConfiguration, secret: str, renew_token: bool = False
) -> Any:
    """
    Get a secret from a Hashicorp Vault secrets manager.
    """
    if self.token is None or renew_token:
        print("Config Manager: getting new Vault token")
        self.token = get_token(self)
        print("Config Manager: Vault token obtained")
    secret = secret.strip(SECRET_PATH_DELIMITER)
    path = SECRET_PATH_DELIMITER.join(secret.split(SECRET_PATH_DELIMITER)[0:-1])
    key = secret.split(SECRET_PATH_DELIMITER)[-1]
    response = get(self.address + path, headers={"X-Vault-Token": self.token})
    output = get_response_value(response, ["data", "data", key])
    return output


def get_token(self: VaultConfiguration) -> str:
    """
    Get or renew a token from the Hashicorp Vault API.
    """
    url = self.address + "auth/approle/login"
    data = {"role_id": self.role_id, "secret_id": self.secret_id}
    response = post(url, data=data)
    output = get_response_value(response, ["auth", "client_token"])
    return output


def get_response_value(response: Response, path: list[str] = []) -> Any:
    """
    Take the result of a requests call and format it into a structured dict.
    """
    if response.status_code != 200:
        error_text = response.text
        try:
            error_text = response.json()
        except Exception:
            pass
        raise Exception(f"Error {response.status_code}:\n{error_text}")
    response_content = response.json()
    output = response_content
    if path:
        for level in path:
            try:
                output = output[level]
            except KeyError as e:
                raise KeyError(
                    (
                        f"Path {path} not found in response content:\n"
                        f"{response_content}"
                    )
                ) from e
    return output

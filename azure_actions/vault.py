from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class KeyVaultError(Exception):
    pass


class KeyVault:
    def __init__(self, vault_url: str) -> None:
        self.client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())

    def get_secret(self, secret_name: str) -> str:
        try:
            return self.client.get_secret(secret_name).value
        except (ServiceRequestError, ResourceNotFoundError, HttpResponseError) as ex:
            raise KeyVaultError(f"Could not retrieve secret {secret_name} due to {repr(ex)}") from ex
        except AttributeError:
            raise KeyVaultError("Vault not initialised")

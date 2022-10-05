from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class KeyVaultError(Exception):
    pass


class KeyVault:
    def __init__(self, vault_url: str) -> None:
        self.client = SecretClient(
            vault_url=vault_url,
            credential=DefaultAzureCredential(additionally_allowed_tenants=["a6e2367a-92ea-4e5a-b565-723830bcc095"]),
        )

    def get_secret(self, secret_name: str) -> str:
        try:
            return self.client.get_secret(secret_name).value  # type: ignore
        except (ServiceRequestError, ResourceNotFoundError, HttpResponseError) as ex:
            raise KeyVaultError(f"Could not retrieve secret {secret_name} due to {repr(ex)}") from ex
        except AttributeError:
            raise KeyVaultError("Vault not initialised")

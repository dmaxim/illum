"""Azure infrastructure for mxinfo knowledge platform."""
import pulumi
import pulumi_azure_native as azure_native

# Configuration
config = pulumi.Config()
location = config.get("location") or "eastus"
environment = config.get("environment") or "dev"
namespace = "mxinfo-knowledge"

# Resource Names
resource_group_name = f"rg-{namespace}"
resource_group_physical_name = f"rg-{namespace}-dev"
storage_account_name = f"{namespace}-storage"
storage_account_physical_name = "mxinfoknowledgedev"
storage_container_name = "mxknowledge-upload-container"
storage_container_physical_name = "mxknowledgeupload"
key_vault_name = f"{namespace}-keyvault"
key_vault_physical_name = "kv-mxinfo-know-dev"

# Resource Group
resource_group = azure_native.resources.ResourceGroup(
    resource_group_name,
    resource_group_name=resource_group_physical_name,
    location=location,
)

# Storage Account
storage_account = azure_native.storage.StorageAccount(
    storage_account_name,
    resource_group_name=resource_group.name,
    account_name=storage_account_physical_name,
    location=resource_group.location,
    sku=azure_native.storage.SkuArgs(
        name=azure_native.storage.SkuName.STANDARD_LRS,
    ),
    kind=azure_native.storage.Kind.STORAGE_V2,
    enable_https_traffic_only=True,
    minimum_tls_version=azure_native.storage.MinimumTlsVersion.TLS1_2,
)

# Storage Container
storage_container = azure_native.storage.BlobContainer(
    storage_container_name,
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name=storage_container_physical_name,
    public_access=azure_native.storage.PublicAccess.NONE,
)

# Key Vault
# Get current Azure client configuration for setting access policies
current = azure_native.authorization.get_client_config()

key_vault = azure_native.keyvault.Vault(
    key_vault_name,
    resource_group_name=resource_group.name,
    vault_name=key_vault_physical_name,
    location=resource_group.location,
    properties=azure_native.keyvault.VaultPropertiesArgs(
        tenant_id=current.tenant_id,
        sku=azure_native.keyvault.SkuArgs(
            family="A",
            name=azure_native.keyvault.SkuName.STANDARD,
        ),
        access_policies=[
            azure_native.keyvault.AccessPolicyEntryArgs(
                tenant_id=current.tenant_id,
                object_id=current.object_id,
                permissions=azure_native.keyvault.PermissionsArgs(
                    keys=["all"],
                    secrets=["all"],
                    certificates=["all"],
                ),
            )
        ],
        enable_rbac_authorization=False,
        enabled_for_deployment=True,
        enabled_for_disk_encryption=True,
        enabled_for_template_deployment=True,
    ),
)

# Export resource details
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("storage_account_id", storage_account.id)
pulumi.export("storage_container_name", storage_container.name)
pulumi.export("key_vault_name", key_vault.name)
pulumi.export("key_vault_uri", key_vault.properties.vault_uri)

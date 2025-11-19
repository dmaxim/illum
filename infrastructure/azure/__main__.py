"""Azure infrastructure for mxinfo knowledge platform."""
import pulumi
import pulumi_azure_native as azure_native

# Configuration
config = pulumi.Config()
location = config.get("location") or "eastus"
environment = config.get("environment") or "dev"
namespace = "verida-knowledge"
secret_managers = config.get_object("secret_managers") or []

# Resource Names
resource_group_name = f"rg-{namespace}-{environment}"
resource_group_physical_name = f"rg-{namespace}-{environment}"
storage_account_name = f"{namespace}-storage"
storage_account_physical_name = f"vinfoknowledge{environment}"
storage_container_name = "vknowledge-upload-container"
storage_container_physical_name = f"vknowledgeupload{environment}"
storage_container_chunks_name = "vknowledge-chunks-container"
storage_container_chunks_physical_name = f"vknowledgechunks{environment}"
storage_container_embeddings_name = "vembedding-chunks-container"
storage_container_embeddings_physical_name = f"vembeddingchunks{environment}"
key_vault_name = f"{namespace}-keyvault"
key_vault_physical_name = f"kv-verida-know-{environment}"
ai_search_name = f"ai-{namespace}-{environment}-eus"
ai_search_physical_name = f"ai-{namespace}-{environment}-eus"
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

# Storage Container for Chunks
storage_container_chunks = azure_native.storage.BlobContainer(
    storage_container_chunks_name,
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name=storage_container_chunks_physical_name,
    public_access=azure_native.storage.PublicAccess.NONE,
)

# Storage Container for Embedding Chunks
storage_container_embeddings = azure_native.storage.BlobContainer(
    storage_container_embeddings_name,
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name=storage_container_embeddings_physical_name,
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
        enable_rbac_authorization=True,
        enabled_for_deployment=True,
        enabled_for_disk_encryption=True,
        enabled_for_template_deployment=True,
    ),
)

# Azure AI Search Service
ai_search_service = azure_native.search.Service(
    ai_search_name,
    resource_group_name=resource_group.name,
    search_service_name=ai_search_physical_name,
    location=resource_group.location,
    sku=azure_native.search.SkuArgs(
        name="basic",
    ),
    replica_count=1,
    partition_count=1,
    hosting_mode=azure_native.search.HostingMode.DEFAULT,
)

# Assign current user as Storage Blob Data Contributor
current_user_storage_role = azure_native.authorization.RoleAssignment(
    "current-user-storage-blob-contributor",
    principal_id=current.object_id,
    principal_type=azure_native.authorization.PrincipalType.USER,
    role_definition_id=f"/subscriptions/{current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",
    scope=storage_account.id,
)

# Assign current user as Key Vault Secrets Officer
current_user_kv_role = azure_native.authorization.RoleAssignment(
    "current-user-kv-secrets-officer",
    principal_id=current.object_id,
    principal_type=azure_native.authorization.PrincipalType.USER,
    role_definition_id=f"/subscriptions/{current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b86a8fe4-44ce-4948-aee5-eccb2c155cd7",
    scope=key_vault.id,
)

# Assign current user as Search Index Data Contributor
current_user_search_role = azure_native.authorization.RoleAssignment(
    "current-user-search-index-data-contributor",
    principal_id=current.object_id,
    principal_type=azure_native.authorization.PrincipalType.USER,
    role_definition_id=f"/subscriptions/{current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/8ebe5a00-799e-43f5-93ac-243d3dce84a7",
    scope=ai_search_service.id,
)

# Assign current user as Contributor on AI Search for full management permissions
current_user_search_contributor_role = azure_native.authorization.RoleAssignment(
    "current-user-search-contributor",
    principal_id=current.object_id,
    principal_type=azure_native.authorization.PrincipalType.USER,
    role_definition_id=f"/subscriptions/{current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
    scope=ai_search_service.id,
)

# Assign secret managers as Key Vault Secrets Officer
secret_manager_roles = []
for idx, email in enumerate(secret_managers):
    # Get the object ID for the user email
    user = pulumi.Output.all(email).apply(
        lambda args: azure_native.authorization.get_ad_user(
            user_principal_name=args[0]
        )
    )
    
    role = azure_native.authorization.RoleAssignment(
        f"secret-manager-{idx}-kv-secrets-officer",
        principal_id=user.object_id,
        principal_type=azure_native.authorization.PrincipalType.USER,
        role_definition_id=f"/subscriptions/{current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b86a8fe4-44ce-4948-aee5-eccb2c155cd7",
        scope=key_vault.id,
    )
    secret_manager_roles.append(role)

# Get storage account connection string
storage_account_keys = pulumi.Output.all(
    resource_group.name, storage_account.name
).apply(
    lambda args: azure_native.storage.list_storage_account_keys(
        resource_group_name=args[0],
        account_name=args[1]
    )
)

connection_string = pulumi.Output.all(
    storage_account.name, storage_account_keys
).apply(
    lambda args: f"DefaultEndpointsProtocol=https;AccountName={args[0]};AccountKey={args[1].keys[0].value};EndpointSuffix=core.windows.net"
)

# Store connection string in Key Vault
# This depends on the current user role assignment to ensure we have permissions first
storage_connection_string_secret = azure_native.keyvault.Secret(
    "file-storage-connection-string",
    resource_group_name=resource_group.name,
    vault_name=key_vault.name,
    secret_name="FileStorage--ConnectionString",
    properties=azure_native.keyvault.SecretPropertiesArgs(
        value=connection_string,
    ),
    opts=pulumi.ResourceOptions(depends_on=[current_user_kv_role]),
)

# Get AI Search admin key
ai_search_admin_keys = pulumi.Output.all(
    resource_group.name, ai_search_service.name
).apply(
    lambda args: azure_native.search.list_admin_key(
        resource_group_name=args[0],
        search_service_name=args[1]
    )
)

ai_search_admin_key = ai_search_admin_keys.apply(lambda keys: keys.primary_key)

# Store AI Search admin key in Key Vault
ai_search_admin_key_secret = azure_native.keyvault.Secret(
    "ai-search-admin-key",
    resource_group_name=resource_group.name,
    vault_name=key_vault.name,
    secret_name="AzureSearch--AdminKey",
    properties=azure_native.keyvault.SecretPropertiesArgs(
        value=ai_search_admin_key,
    ),
    opts=pulumi.ResourceOptions(depends_on=[current_user_kv_role]),
)

# Export resource details
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("storage_account_id", storage_account.id)
pulumi.export("storage_container_name", storage_container.name)
pulumi.export("storage_container_chunks_name", storage_container_chunks.name)
pulumi.export("storage_container_embeddings_name", storage_container_embeddings.name)
pulumi.export("key_vault_name", key_vault.name)
pulumi.export("key_vault_uri", key_vault.properties.vault_uri)
pulumi.export("ai_search_service_name", ai_search_service.name)
pulumi.export("ai_search_service_id", ai_search_service.id)

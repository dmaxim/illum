# Azure Infrastructure - mxinfo Knowledge Platform

This directory contains Pulumi infrastructure as code for provisioning Azure resources.

## Resources Created

- **Resource Group**: `rg-mxinfo-knowledge-dev`
- **Storage Account**: `mxinfoknowledgedev`
  - **Container**: `mxknowledgeupload`
- **Key Vault**: `kv-mxinfo-know-dev`

## Prerequisites

1. [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/) installed
2. [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
3. Python 3.8 or higher
4. Azure subscription with appropriate permissions

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Login to Azure:
   ```bash
   az login
   ```

3. Login to Pulumi with Azure Blob Storage backend:
   ```bash
   pulumi login 'azblob://pulumi?storage_account=setransdevopsdevtest'
   ```
   
   This configures Pulumi to store state in Azure Blob Storage:
   - Storage Account: `setransdevopsdevtest`
   - Container: `pulumi`
   - Resource Group: `rg-setrans-devops-dev`
   
   **Note**: You must have the "Storage Blob Data Contributor" role assigned on the storage account.

## Deployment

1. Initialize a new stack (first time only):
   ```bash
   pulumi stack init dev
   ```

2. Configure Azure location (optional, defaults to eastus):
   ```bash
   pulumi config set location eastus
   ```

3. Preview the changes:
   ```bash
   pulumi preview
   ```

4. Deploy the infrastructure:
   ```bash
   pulumi up
   ```

## Configuration

You can customize the deployment using Pulumi configuration:

- `location`: Azure region (default: `eastus`)
- `environment`: Environment name (default: `dev`)
- `secret_managers`: List of user email addresses to grant "Key Vault Secrets Officer" role

Example:
```bash
pulumi config set location westus2
pulumi config set environment prod
pulumi config set secret_managers '["user1@example.com","user2@example.com"]' --path
```

### Key Vault Access

The Key Vault is configured with RBAC authorization. The following roles are automatically assigned:
- Current user (deploying the infrastructure) receives "Key Vault Secrets Officer" role
- Users listed in `secret_managers` configuration receive "Key Vault Secrets Officer" role

The "Key Vault Secrets Officer" role allows users to manage secrets in the Key Vault.

## Outputs

After deployment, the following outputs are available:

- `resource_group_name`: Name of the resource group
- `storage_account_name`: Name of the storage account
- `storage_account_id`: Resource ID of the storage account
- `storage_container_name`: Name of the blob container
- `key_vault_name`: Name of the key vault
- `key_vault_uri`: URI of the key vault

View outputs:
```bash
pulumi stack output
```

## Cleanup

To destroy all resources:
```bash
pulumi destroy
```

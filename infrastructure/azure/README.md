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

3. Login to Pulumi:
   ```bash
   pulumi login
   ```

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

Example:
```bash
pulumi config set location westus2
pulumi config set environment prod
```

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

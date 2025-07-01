# PostgreSQL Source Example

This example demonstrates how to configure a PostgreSQL data source for cr8tor.

## Configuration

```toml
[source]
name = "PostgreSQL Database Connection"
type = "postgresql"
host_url = "postgres-server.example.com"
database = "my_database"
port = 5432

[credentials]
provider = "AzureKeyVault"
username_key = "postgres-username-secret"
password_key = "postgres-password-secret"
```

## Key Points

- **Type**: Use `postgresql` for PostgreSQL databases
- **Credentials**: PostgreSQL uses username/password authentication
- **Required Fields**: `host_url`, `database`, `port`
- **Secret Keys**: `username_key` and `password_key` point to secret names in your key vault

## Database Configuration

The PostgreSQL database should be accessible from the cr8tor services and the provided credentials should have appropriate read permissions for the target schema and tables.

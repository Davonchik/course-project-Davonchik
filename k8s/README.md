# Kubernetes Manifests for Reading List API

This directory contains Kubernetes manifests for deploying the Reading List API application.

## Files

### Application
- `deployment.yaml` - Application deployment configuration with security hardening
- `service.yaml` - Service to expose the API
- `secret.yaml` - Secret template for application secrets (DO NOT commit real secrets!)

### Database
- `postgres-deployment.yaml` - PostgreSQL database deployment
- `postgres-service.yaml` - PostgreSQL service
- `postgres-pvc.yaml` - Persistent Volume Claim for database storage
- `postgres-secret.yaml` - Secret template for database password (DO NOT commit real secrets!)

## Security Features

### Application (reading-list-api)
- **Non-root user**: Runs as UID 1000
- **Read-only root filesystem**: Enabled
- **No privilege escalation**: Enforced
- **Dropped capabilities**: All capabilities dropped
- **Resource limits**: Memory and CPU limits set
- **Security context**: seccomp profile set to RuntimeDefault
- **Health checks**: Liveness and readiness probes configured

### Database (postgres)
- **Non-root user**: Runs as UID 999 (postgres)
- **Minimal capabilities**: Only necessary capabilities added
- **Security context**: seccomp profile set to RuntimeDefault
- **Resource limits**: Memory and CPU limits set
- **Persistent storage**: Uses PVC for data persistence
- **Health checks**: Liveness and readiness probes configured

## Deployment

```bash
# Create namespace (optional)
kubectl create namespace reading-list

# Apply manifests
kubectl apply -f k8s/secret.yaml -n reading-list
kubectl apply -f k8s/postgres-secret.yaml -n reading-list
kubectl apply -f k8s/postgres-pvc.yaml -n reading-list
kubectl apply -f k8s/postgres-deployment.yaml -n reading-list
kubectl apply -f k8s/postgres-service.yaml -n reading-list
kubectl apply -f k8s/deployment.yaml -n reading-list
kubectl apply -f k8s/service.yaml -n reading-list
```

## Important Notes

**DO NOT** commit real secrets to git! The secret files are templates only.

In production:
- Use external secrets management (e.g., Sealed Secrets, External Secrets Operator)
- Use proper secret rotation mechanisms
- Enable network policies
- Configure RBAC appropriately
- Use ingress with TLS for external access

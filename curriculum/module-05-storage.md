# Module 05 — Storage & Stateful Workloads

## Why this matters

Stateless apps scale like ninja clones, but data needs a safe dojo locker. This module teaches you PersistentVolumes, PersistentVolumeClaims, StorageClasses, and StatefulSets—core skills before running Postgres, Kafka, or Qdrant in the capstone.

## Learning Objectives

- Explain PV/PVC relationship and dynamic provisioning.
- Deploy a StatefulSet or Deployment with a persistent volume (Postgres demo).
- Understand storage classes available in your local cluster (kind/k3d defaults).
- Verify data durability across pod restarts.
- Outline tradeoffs of “state on Kubernetes” vs managed services.

## Prerequisite Check

- Local cluster with storage provisioner (kind uses hostPath-provisioner addon; k3d integrates with local-path provisioner).
- Basic SQL familiarity.

## Core Concepts

- **PersistentVolume (PV)**: storage resource in the cluster.
- **PersistentVolumeClaim (PVC)**: request for storage by a pod.
- **StorageClass**: template for dynamic provisioning.
- **StatefulSet vs Deployment**: stable network IDs and volume binding.
- **Config & secrets**: storing DB credentials.

## Hands-On Drills

1. Inspect available storage

   ```bash
   kubectl get storageclass
   kubectl describe storageclass standard
   ```

2. Deploy Postgres with Helm or YAML

   - Option A (Helm):
     ```bash
     helm repo add bitnami https://charts.bitnami.com/bitnami
     helm install postgres bitnami/postgresql -n lab --create-namespace \
       --set auth.postgresPassword=devpass \
       --set primary.persistence.size=1Gi
     ```
   - Option B (YAML): create PVC + Deployment/StatefulSet manually (good practice).

3. Connect and test durability

   ```bash
   kubectl port-forward svc/postgres-postgresql 5432:5432 -n lab
   psql -h localhost -U postgres -d postgres
   CREATE TABLE dojo_notes (id serial PRIMARY KEY, note text);
   INSERT INTO dojo_notes (note) VALUES ('Storage FTW');
   ```

4. Restart pod, verify data

   ```bash
   kubectl delete pod postgres-postgresql-0 -n lab
   kubectl get pods -n lab
   psql ...
   SELECT * FROM dojo_notes;
   ```

5. Explore PVC binding
   ```bash
   kubectl get pvc -n lab
   kubectl describe pvc data-postgres-postgresql-0 -n lab
   ```

## Checkpoint

- You can explain why PVCs survive pod restarts.
- You know the difference between static vs dynamic provisioning.
- You can justify when to offload to managed databases.

## Stretch Goals

- Implement manual PV/PVC definitions using hostPath for kind.
- Try StatefulSet with volumeClaimTemplates and compare to Deployment + PVC.
- Backup/restore using `kubectl cp` or `pg_dump`.
- Explore ReadWriteMany vs ReadWriteOnce access modes.

## Resources

- Kubernetes storage overview — https://kubernetes.io/docs/concepts/storage/
- StatefulSets — https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- Bitnami Postgresql chart values — https://artifacthub.io/packages/helm/bitnami/postgresql

## Deliverable

- Persisted data surviving pod restarts (proof via SQL screenshot/log).
- Journal notes about storage class behavior on your local cluster.

State mastered. Master Lonn nods knowingly—you’re ready to observe and debug your creations.

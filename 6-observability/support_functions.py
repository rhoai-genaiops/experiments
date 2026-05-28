import os


def get_namespace():
    """Read the current OpenShift namespace from env var or k8s service account."""
    namespace = os.getenv("MLFLOW_WORKSPACE")
    if namespace:
        return namespace
    namespace_path = "/run/secrets/kubernetes.io/serviceaccount/namespace"
    if os.path.exists(namespace_path):
        with open(namespace_path) as f:
            return f.read().strip()
    return "default"

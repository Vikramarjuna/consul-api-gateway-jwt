# Consul API Gateway JWT Runbook

## 1. Initialize and Apply Terraform

```sh
terraform init
terraform apply --auto-approve
```

Wait approximately 15 minutes for the build to complete.

## 2. Connect to EKS

```sh
aws eks --region $(terraform output -raw region) update-kubeconfig --name $(terraform output -raw kubernetes_cluster_id)
```

## 3. Create Consul Namespace and Install Consul on Kubernetes

```sh
kubectl create namespace consul

# Setup Consul License
# Create a license file named `consul.hclic` in the root of this repository.
secret=$(cat consul.hclic)
kubectl create secret generic consul-ent-license --from-literal="key=${secret}" -n consul

# Install Consul on Kubernetes
consul-k8s install -config-file=consul/values.yaml
```

## 4. Ensure All Services Are Running

```sh
kubectl get pods --namespace consul
kubectl get pods --namespace default
```

## 5. Deploy HashiCups Application

```sh
kubectl apply --filename k8s-services/
kubectl apply --filename api-gw/consul-api-gateway.yaml
kubectl get services --namespace=consul api-gateway
```

## 6. Extract API Gateway URL

```sh
export APIGW_URL=$(kubectl get services --namespace=consul api-gateway -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo $APIGW_URL
```

## 7. Test API Without JWT

```sh
curl -v "$APIGW_URL/echo"
```

You should see a `200 OK` response.

## 10. JWT Generation

You can generate a JWT token using one of the following methods:

<details>
<summary><strong>Option 1: Local JWT Token Generation</strong></summary>

1. Generate keys and JWKS:
    ```sh
    cd jwt
    python generate_keys_and_jwks.py
    ```
    This will generate `private.key` and `public.key` files in the `jwt` directory, along with an encoded JWKS string, KID, and the algorithm used to generate the public key.
2. Copy the generated encoded JWKS string into the `consul-jwt-provider.yaml` file.
3. Set the KID and algorithm in the `generate_jwt.py` file.
4. Apply the JWT provider, gateway policy, and route authentication filter:
    ```sh
    kubectl apply -f jwt/04-consul-jwt-provider-local.yaml
    kubectl apply -f jwt/05-gateway-policy.yaml
    kubectl apply -f jwt/06-route-auth-filter.yaml
    ```
5. Uncomment the `filters` section in the `api-gw/ingress-echo-load-balancer.yaml` file to enable JWT validation for the echo service.
6. Generate and export a JWT token as an environment variable:
    ```sh
    export JWT_TOKEN=$(python generate_jwt.py)
    ```

</details>

<details>
<summary><strong>Option 2: Use a Fake JWT Provider Service</strong></summary>

1. Depending on the fake jwt provider service used, update the port and image in the files appropriately.
2. Apply the JWT provider, gateway policy, and route authentication filter:
    ```sh
    kubectl apply -f jwt/01-namespace.yaml
    kubectl apply -f jwt/01a-serviceaccount.yaml
    kubectl apply -f jwt/02-deployment.yaml
    kubectl apply -f jwt/03-service.yaml
    kubectl apply -f jwt/04-consul-jwt-provider.yaml
    kubectl apply -f jwt/05-gateway-policy.yaml
    kubectl apply -f jwt/06-route-auth-filter.yaml
    kubectl apply -f jwt/07-debug-pod.yaml
    ```
4. Uncomment the `filters` section in the `api-gw/ingress-echo-load-balancer.yaml` file to enable JWT validation for the echo service.
5. Obtain a JWT token from the fake provider:
    ```sh
    kubectl exec -it network-debug-pod -n consul -- curl -X POST -H "Content-Type: multipart/form-data" -F "sub=testuser" -F "iss=http://fake-jwt-server.jwt-dev.svc.cluster.local:8008" -F "aud=your-api-audience" -F "role=admin" -F "nbf=0" -F "exp=3600" http://fake-jwt-server.jwt-dev.svc.cluster.local:8008/token
    ```
    You can verify the token using `https://jwt.io/` to make sure it has the right role and other values.
6. Set the token as env variable `JWT_TOKEN`

</details>

Select either Option 1 or Option 2 above based on your environment and requirements.

## 9. Test API With and Without JWT

- Invoke the API without a JWT token (should return 401 Unauthorized):
    ```sh
    curl -v "$APIGW_URL/echo"
    ```
- Invoke the API with the JWT token:
    ```sh
    curl -v -H "Authorization: Bearer $JWT_TOKEN" "$APIGW_URL/echo"
    ```

## 10. Cleanup the Environment

```sh
terraform destroy
```

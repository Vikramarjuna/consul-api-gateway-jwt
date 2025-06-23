terraform init
terraform apply --auto-approve
# wait 15 minutes for build

# Connect to EKS
aws eks --region $(terraform output -raw region) update-kubeconfig --name $(terraform output -raw kubernetes_cluster_id)

# Create consul namespace
kubectl create namespace consul

# Setup Consul License
create a license file with name `consul.hclic` in the root of this repositoryg
secret=$(cat consul.hclic)
kubectl create secret generic consul-ent-license --from-literal="key=${secret}"

# Install Consul on Kubernetes
consul-k8s install -config-file=consul/values.yaml


# Ensure all services are up and running successfully
kubectl get pods --namespace consul && kubectl get pods --namespace default


kubectl apply --filename jwt/
kubectl get pods --namespace jwt-dev
kubectl apply --filename k8s-services/
kubectl apply --filename api-gw/consul-api-gateway.yaml
kubectl get services --namespace=consul api-gateway

# Set environment variables
## Check out Daniele's GS on VMs tutorial to find the API version of this
export CONSUL_HTTP_TOKEN=$(kubectl get --namespace consul secrets/consul-bootstrap-acl-token --template={{.data.token}} | base64 -d) && \
export CONSUL_HTTP_ADDR=https://$(kubectl get services/consul-ui --namespace consul -o jsonpath='{.status.loadBalancer.ingress[0].hostname}') && \
export CONSUL_HTTP_SSL_VERIFY=true && \
kubectl get --namespace consul secrets/consul-ca-cert -o json | jq -r '.data."tls.crt"' | base64 -d > ca.crt && \
export CONSUL_CACERT=ca.crt && \
export CONSUL_TLS_SERVER_NAME=server.dc1.consul

# Notice that Consul services exist
consul catalog services

# Update Helm chart
consul-k8s upgrade -config-file=helm/consul-v2-terminating-gw.yaml

# Go to API gateway URL and explore HashiCups (broken state)
export CONSUL_APIGW_ADDR=http://$(kubectl get svc/api-gateway -o json | jq -r '.status.loadBalancer.ingress[0].hostname') && \
echo $CONSUL_APIGW_ADDR



# Cleanup the environment
terraform destroy
# Terraform — AWS VPC + EKS

Provisions the AWS infrastructure for PantryPal:

| File | What it creates |
|------|-----------------|
| `vpc.tf` | VPC, 2 public subnets + 2 private subnets across 2 AZs, Internet Gateway, NAT Gateway, route tables |
| `iam.tf` | EKS control-plane role and worker-node role with the AWS-managed EKS policies |
| `eks.tf` | EKS cluster (Kubernetes 1.34) and a managed node group (2 × t3.medium, scales 1–3) |
| `outputs.tf` | VPC/subnet IDs, cluster name/endpoint/status, `aws eks update-kubeconfig` command |

## Running against mock AWS (default for this project)

No real AWS account is used. A local [moto](https://github.com/getmoto/moto) server
emulates the EC2, IAM, STS and EKS APIs, so `plan`/`apply`/`destroy` exercise the
same code paths without cost.

```bash
docker compose -f mock-aws/docker-compose.yml up -d   # mock AWS on http://localhost:5050
cp terraform.tfvars.example terraform.tfvars           # mock_aws_endpoint is preset
terraform init
terraform plan -out tfplan
terraform apply tfplan

# inspect with the AWS CLI
export AWS_ENDPOINT_URL=http://localhost:5050 AWS_ACCESS_KEY_ID=mock AWS_SECRET_ACCESS_KEY=mock AWS_DEFAULT_REGION=us-east-1
aws eks describe-cluster --name pantrypal-dev

terraform destroy
```

## Running against real AWS

Set `mock_aws_endpoint = ""` in `terraform.tfvars` and authenticate with
`aws configure` / `aws sso login`. **Run `terraform destroy` afterwards** — EKS and
the NAT gateway are billed hourly. Credentials are never stored in this repo.

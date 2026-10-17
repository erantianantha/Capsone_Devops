terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Local state keeps the mock-AWS workflow self-contained. For a shared real
  # AWS account, switch to the S3 backend (bucket + DynamoDB/S3 locking).
  # backend "s3" {
  #   bucket       = "pantrypal-tfstate"
  #   key          = "eks/terraform.tfstate"
  #   region       = "us-east-1"
  #   use_lockfile = true
  # }
}

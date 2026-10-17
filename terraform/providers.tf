locals {
  # When mock_aws_endpoint is set, every AWS API call goes to the local moto
  # server instead of real AWS, using throwaway dummy credentials.
  mock = var.mock_aws_endpoint != ""
}

provider "aws" {
  region = var.aws_region

  access_key = local.mock ? "mock-access-key" : null
  secret_key = local.mock ? "mock-secret-key" : null

  skip_credentials_validation = local.mock
  skip_metadata_api_check     = local.mock
  skip_requesting_account_id  = local.mock

  endpoints {
    ec2 = local.mock ? var.mock_aws_endpoint : null
    eks = local.mock ? var.mock_aws_endpoint : null
    iam = local.mock ? var.mock_aws_endpoint : null
    sts = local.mock ? var.mock_aws_endpoint : null
  }

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

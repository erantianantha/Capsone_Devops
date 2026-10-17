variable "project" {
  description = "Project name used as a prefix for resource names"
  type        = string
  default     = "pantrypal"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "mock_aws_endpoint" {
  description = "URL of a local AWS emulator (moto), e.g. http://localhost:5050. Leave empty to target real AWS."
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for the subnets (at least two)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "EKS needs subnets in at least two availability zones."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDRs for the public subnets, one per AZ"
  type        = list(string)
  default     = ["10.20.0.0/20", "10.20.16.0/20"]
}

variable "private_subnet_cidrs" {
  description = "CIDRs for the private (worker node) subnets, one per AZ"
  type        = list(string)
  default     = ["10.20.128.0/20", "10.20.144.0/20"]
}

variable "enable_nat_gateway" {
  description = "Create a NAT gateway so private worker nodes can reach the internet"
  type        = bool
  default     = true
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS control plane"
  type        = string
  default     = "1.34"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}
